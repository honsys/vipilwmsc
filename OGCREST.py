#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/OGCREST.py $'
svnId = rcsId = '$Name$ $Id: OGCREST.py 24 2008-04-01 06:19:16Z hon $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
OGCREST provides the principle entry point/function into the OGCWMSC
system, via CGI or Mod_Python. A CGI app. uses parseCGI to evaluate
the WMS REST request args., then invokes the renderPNG() func. A 
mod_python handler invokes the WMSModPyHandler func., which 
parses the WMS REST req. args, then invokes the renderPNG() func.
"""
#
# note that both GeoImage and Raster now import vipsCC
# evidently vipsCC pops sys.argv! so first make a deep 
# copy of it and restore it!
import os, sys, time, copy, urllib
_argv = copy.deepcopy(sys.argv)

from PIL import Image
#from mod_python import apache
#GeoImage = apache.import_module('~/lib/GeoImage.py')
#GeoProj = apache.import_module('~/lib/GeoProj.py')
#PILMemCache = apache.import_module('~/lib/PILMemCache.py')
#FileKeyUtils = apache.import_module('~/lib/FileKeyUtils.py')
#import G3WMS.GeoImage as GeoImage
#import G3WMS.GeoProj as GeoProj
#import FileKeyUtils, PILMemCache, GeoProj, GeoImage
#import G3WMS.FileKeyUtils as FileKeyUtils
#import G3WMS.PILMemCache as PILMemCache
import GeoImage
import GeoProj
import FileKeyUtils
import PILMemCache
import Raster

# globals:
_URLencode = {'!':'%21', '*':'%2A', "'":'%27', '(':'%28', ')':'%29', ';':'%3B',
              ':':'%3A', '@':'%40', '&':'%26', '=':'%3D', '+':'%2B', '$':'%24',
              ',':'%2C', '/':'%2F', '?':'%3F', '%':'%25', '#':'%23', '[':'%5B',
              ']':'%5D'}
_URLdecode = {'%21':'!', '%2A':'*', '%27':"'", '%28':'(', '%29':')', '%3B':';',
              '%3A':':', '%40':'@', '%26':'&', '%3D':'=', '%2B':'+', '%24':'$',
              '%2C':',', '%2F':'/', '%3F':'?', '%25':'%', '%23':'#', '%5B':'[',
              '%5D':']'}

# shorter list is faster:
_URLWMSdecode = {'%3A':':', '%26':'&', '%3D':'=', '%2C':',', '%2F':'/'}

#
def decodeURL(arg):
  """
  Returns a decoded URL string value.
  """
  global _URLdecode
  decode = copy.deepcopy(arg)
  for key, val in _URLWMSdecode.items():
    decode = FileKeyUtils.replaceStr(decode, key, val)
#   print 'decodeURL> ', arg, ' ==> ', decode

  return decode

def printReq(req):
  """
  Prints the contents ofr the mod_python handler request object. 
  """
  req.content_type = 'text/plain'
  t = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
  sr = t + '\n'
  req.write(sr)
  sr = "%s\n" % req
  req.write(sr)
  sr = "%s\n" % req.unparsed_uri
  req.write(sr)
  sr = "%s\n" % req.args
  req.write(sr)
# sr = "%s\n" % req.subprocess_env
# req.write(sr)
  for k in req.subprocess_env.keys():
    sr = "%s" % k
    sr += ' == '
    sr += "%s\n" % req.subprocess_env[k]
    req.write(sr)
#end printReq

def urlCascadeCGI(url) :
  """
  Helper to CGI apps. that cascade/forward WMS requests to external services. 
  """
  ul = 0
  try:
    ul = len(url)
  except:
    pass

  if ul <= 0 :
    url = os.environ.get('HTTP_REFERER','?')

  wmsurl = url + '?'
  cgireq = os.environ.get('QUERY_STRING','?')
# print >> FileKeyUtils.WMSlog, 'OGCREST.urlCascadeCGI> req. query: ', cgireq

  if len(cgireq) <= 1 :
    return wmsurl

  wmsurl += cgireq
# print >> FileKeyUtils.WMSlog, 'OGCREST.urlCascadeCGI> wmsurl: ', wmsurl
  return wmsurl
#end urlCascadeCGI

def urlCascadeReq(req, url): # mod_python
  """
  Helper to mod_python handlers that cascade/forward WMS requests to external services. 
  """
  wmsurl = url + req.subprocess_env['QUERY_STRING']
  print >> FileKeyUtils.WMSlog, 'OGCREST.urlCascadeReq> wmsurl: ', wmsurl
  return wmsurl

def htdocRoot(req):
  """
  Returns apache httpd document root of mod_python handler.
  """
# for mod_python app
  docpath = req.subprocess_env.get('PATH_TRANSLATED', None)
  if docpath == None: return None
  try:
    htpos = docpath.rindex('htdoc')
    if htpos >= 0:
      try:
        slashpos = docpath.index('/',htpos)
        root = docpath[0:slashpos+1] # include slash
        return root
      except: return docpath
  except: pass

  return docpath

def parseModPyArgs(args):
  """
  Returns hash dict. of parsed WMS REST ampersan (&) separated and key = comma (,) delimited values.
  URL decoding is also performed.
  """
  arghash = {}
# parse & separated list of REST args
  rest = FileKeyUtils.parseAmpers(args) # example list[] of 3 elem. like:  'foo=bar&bar=drink,food&etc=more,money,now'
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseModPyArgs> rest args list: ', rest
  for item in rest:
    decitem = decodeURL(item)
    arg = FileKeyUtils.parseEqual(decitem) # should return a 2-tuple: 'a=b' --> ['a', 'b']
    if len(arg) <= 1 : continue # skip to the next item
    key = arg[0]
    vals = FileKeyUtils.parseCommas(arg[1])
    if len(vals) <= 0 :
      continue # do not put it into hash -- this should not happen...
    elif len(vals) == 1 :
      arghash[key] = vals[0] # just put the single value into hash
    else:
      arghash[key] = vals

  return arghash  
    
#end parseModPyArgs

def parseWMS(req, OGCreq):
  """
  Applies parseModPyArgs() to all key args provided in REST req. to set full OGCReq hash dict.
  """
# OpenLayers will submit a WMS GetMap request that looks like:
# http://localhost:9090/openlayers/rest.py?LAYERS=world&TRANSPARENT=true&FORMAT=image/png&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&EXCEPTIONS=application/vnd.ogc.se_inimage&SRS=EPSG:4326&BBOX=-118.125,50.625,-112.5,56.25&WIDTH=256&HEIGHT=256
#
  if len(req.args) <= 0:
    return 0

# note that some http text macros may be present like: '%3A' == ':' and '%2F' == '/'
  format = service = srs = None
  trans = 'true'
  size = []; bbox = []; layers = []

  modpyreq = {}
  modpyreq = parseModPyArgs(req.args) # hash dict object hold the req/form data
  if len(modpyreq) <= 0:
    return 0

  layr = None
  if modpyreq.has_key('layers') :
    layr = modpyreq.get('layers')
  if modpyreq.has_key('Layers') :
    layr = modpyreq.get('Layers')
  if modpyreq.has_key('LAYERS') :
    layr = modpyreq.get('LAYERS')

  if layr == None:
    return 0

# check whether single or multiple layers specified:
  if isinstance(layr, str):
    layers.append(layr)
  else:
    layers = layr

  numlayers = len(layers)
  if numlayers <= 0 :
    printSysInfo(req, OGCreq)
    print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSModPy> no layers specified, abort..."
    return 0

# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> layers: ', layers
  OGCreq['layers'] = layers

#
  if modpyreq.has_key('srs') :
    srs = modpyreq.get('srs',"EPSG:4326")
  if modpyreq.has_key('Srs') :
    srs = modpyreq.get('Srs',"EPSG:4326")
  if modpyreq.has_key('SRS') :
    srs = modpyreq.get('SRS',"EPSG:4326")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> srs: ', srs
  try:
    p = srs.index('%3A')
    if p >= 0 : # replace with ':'
      s = srs[0:p]
      r = srs[p+3:]
      srs = s + ':' + r
  except: pass
  OGCreq['srs'] = srs
#
  if modpyreq.has_key('service') :
    service = modpyreq.get('service',"WMS")
  if modpyreq.has_key('Service') :
    service = modpyreq.get('Service',"WMS")
  if modpyreq.has_key('SERVICE') :
    service = modpyreq.get('SERVICE',"WMS")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> service: ', service
  OGCreq['service'] = service
#
  if modpyreq.has_key('format') :
    format = modpyreq.get('format',"image/png")
  if modpyreq.has_key('Format') :
    format = modpyreq.get('Format',"image/png")
  if modpyreq.has_key('FORMAT') :
    format = modpyreq.get('FORMAT',"image/png")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> format: ', format
  try:
    p = srs.index('%2F')
    if p >= 0 : # replace with '/'
      s = srs[0:p]
      r = srs[p+3:]
      srs = s + '/' + r
  except: pass
  OGCreq['format'] = format
#
  if modpyreq.has_key('transparent') :
    trans = modpyreq.get('transparent',"true")
  if modpyreq.has_key('Transparent') :
    trans = modpyreq.get('Transparent',"true")
  if modpyreq.has_key('TRANSPARENT') :
    trans = modpyreq.get('TRANSPARENT',"true")
  trans = trans.lower()
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> transparent: ', trans
  if trans in ('true', 'True', 'TRUE') :
    OGCreq['opacity'] = 255
  elif trans in ('false', 'False', 'FALSE') :
    OGCreq['opacity'] = 0
  elif str(trans).isdigit() :
    OGCreq['opacity'] = int(trans)
  else :
    OGCreq['opacity'] = 255
#
  if modpyreq.has_key('width') :
    size.append(int(modpyreq.get('width')))
  if modpyreq.has_key('Width') :
    size.append(int(modpyreq.get('Width')))
  if modpyreq.has_key('WIDTH') :
    size.append(int(modpyreq.get('WIDTH')))
  if modpyreq.has_key('height') :
    size.append(int(modpyreq.get('height')))
  if modpyreq.has_key('Height') :
    size.append(int(modpyreq.get('Height')))
  if modpyreq.has_key('HEIGHT') :
    size.append(int(modpyreq.get('HEIGHT')))
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> width, height: ', size
  OGCreq['size'] = size;
#
  sbbox = []; # bbox as text list
  if modpyreq.has_key('bbox') :
    sbbox = modpyreq.get('bbox')
  if modpyreq.has_key('Bbox') :
    sbbox = modpyreq.get('Bbox')
  if modpyreq.has_key('BBOX') :
    sbbox = modpyreq.get('BBOX')
    
# print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSModPy> comma separated bbox field specified: ", sbbox
  for item in sbbox :
    try: 
      bbox.append(float(item))
    except: pass
#
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> bbox: ', bbox
  OGCreq['bbox'] = bbox
#
  print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSModPy> OGCreq{} == ', OGCreq
#
  return numlayers
#end parseWMS()

def printSysInfo(req, OGCreq) :
  """
  Printout environment of mod_python process.
  """
  import platform
  print >> FileKeyUtils.WMSlog, "OGCREST.Content-type: text/plain; charset=iso-8859-1"
  print >> FileKeyUtils.WMSlog, platform.platform()
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> sys.path: ", sys.path
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> version: ", sys.version
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> builtin modules: ", sys.builtin_module_names
  t = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> time: ", t
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> req: ", req
  if len(req) <= 0:
    return 0

  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> unparsed_uri: ", req.unparsed_uri
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> args: ", req.args
  for k in req.subprocess_env.keys():
    print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> ", k, " == ", req.subprocess_env[k]

  numlayers = parseWMS(req, OGCreq)
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> ", service, format, trans, layers, size, bbox, '\n'
  return numlayers
#end printSysInfo

def printSysInfoCGI(OGCreq) :
  """
  Printout environment of CGI app.
  """
  import platform
  print >> FileKeyUtils.WMSlog, "OGCREST.Content-type: text/plain; charset=iso-8859-1", '\n'
  print >> FileKeyUtils.WMSlog, platform.platform(), '\n'
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> sys.path: ", sys.path, '\n'
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> version: ", sys.version, '\n'
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> builtin modules: ", sys.builtin_module_names, '\n'
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> evaluate request URI: ", '\n'
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> evaluate request method type...", '\n'
  method = os.environ.get('REQUEST_METHOD', 'GET')
  if method in ['GET', 'HEAD']:
    print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> GET or HEAD: ", method.lower(), '\n'
  if method == 'POST':
    print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> POST: ",  method.lower(), '\n'
#
  client = os.environ.get('HTTP_USER_AGENT','?') 
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> client: ", client, '\n'
  clientaccepts = os.environ.get('HTTP_ACCEPT','?') 
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> client accepts HTTP: ", clientaccepts, '\n'
  ref = os.environ.get('HTTP_REFERER','REF')
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> REFERER: ", ref, '\n'
  uri = os.environ.get('REQUEST_URI', 'URI')
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> URI: ", uri, '\n'
  req = os.environ.get('QUERY_STRING','?')
  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> req. query: ", req, '\n'
  if len(req) <= 0 or req == '?' :
    return 0

  cgireq = cgi.FieldStorage() # FieldStorage object to hold the req/form data
  if cgireq : 
    service = ''; format = ''; trans = ''; layers = []; size = []; bbox = []
    numlayers = parseWMSCGI(cgireq, OGCreq)
    print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> ", service, format, trans, layers, size, bbox, '\n'
    return numlayers

  print >> FileKeyUtils.WMSlog, "OGCREST.printSysInfo> cgi.FieldStorage is empty?...", '\n'
  return 0
#end printSysInfoCGI(OGCreq)

def parseWMSCGI(cgireq, OGCreq) :
  """
  Applies standard python CGI module functions to parse all key args provided in REST req. 
  and set the full OGCReq hash dict.
  """
# OpenLayers will submit a WMS GetMap request that looks like:
# http://localhost:9090/openlayers/rest.cgi?LAYERS=world&TRANSPARENT=true&FORMAT=image/png&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&EXCEPTIONS=application/vnd.ogc.se_inimage&SRS=EPSG:4326&BBOX=-118.125,50.625,-112.5,56.25&WIDTH=256&HEIGHT=256
#
  try:
    cgireq = cgi.FieldStorage() # FieldStorage object to hold the req/form data
  except:
    printSysInfoCGI(OGCreq)
    print >> FileKeyUtils.WMSlog, "OGCREST.cgi.FieldStorage() exception, abort..."
    return 0

  format = service = srs = None
  trans = 'true'
  size = []; bbox = []; layers = []

  if cgireq.has_key('layers') :
    cgilayer = cgireq.getfirst('layers', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated layer field specified: ", cgilayer
    layers = FileKeyUtils.parseCommas(cgilayer)
  if cgireq.has_key('Layers') :
    cgilayer = cgireq.getfirst('Layers', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated layer field specified: ", cgilayer
    layers = FileKeyUtils.parseCommas(cgilayer)
  if cgireq.has_key('LAYERS') :
    cgilayer = cgireq.getfirst('LAYERS', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated layer field specified: ", cgilayer
    layers = FileKeyUtils.parseCommas(cgilayer)
#
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> layers: ', layers
  OGCreq['layers'] = layers
  numlayers = len(layers)
  if numlayers <= 0 :
    printSysInfoCGI(OGCreq)
    print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> no layers specified, abort..."
    sys.exit()
#
  if cgireq.has_key('srs') :
    srs = cgireq.getvalue('srs',"EPSG:3226")
  if cgireq.has_key('Srs') :
    srs = cgireq.getvalue('Srs',"EPSG:3226")
  if cgireq.has_key('SRS') :
    srs = cgireq.getvalue('SRS',"EPSG:3226")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> SRS: ', srs
  OGCreq['srs'] = srs
#
  if cgireq.has_key('service') :
    service = cgireq.getvalue('service',"WMS")
  if cgireq.has_key('Service') :
    service = cgireq.getvalue('Service',"WMS")
  if cgireq.has_key('SERVICE') :
    service = cgireq.getvalue('SERVICE',"WMS")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> service: ', service
  OGCreq['service'] = service
#
  if cgireq.has_key('format') :
    format = cgireq.getvalue('format',"image/png")
  if cgireq.has_key('Format') :
    format = cgireq.getvalue('Format',"image/png")
  if cgireq.has_key('FORMAT') :
    format = cgireq.getvalue('FORMAT',"image/png")
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> format: ', format
  OGCreq['format'] = format
#
  if cgireq.has_key('transparent') :
    trans = cgireq.getvalue('transparent',"true")
  if cgireq.has_key('Transparent') :
    trans = cgireq.getvalue('Transparent',"true")
  if cgireq.has_key('TRANSPARENT') :
    trans = cgireq.getvalue('TRANSPARENT',"true")
  trans = trans.lower()
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> transparent: ', trans
  if trans == 'true' :
    OGCreq['opacity'] = 255
  elif trans == 'false' :
    OGCreq['opacity'] = 255
  elif trans.isdigit() :
    OGCreq['opacity'] = int(trans)
  else :
    OGCreq['opacity'] = 255
#
  if cgireq.has_key('width') :
    size.append(int(cgireq.getvalue('width')))
  if cgireq.has_key('Width') :
    size.append(int(cgireq.getvalue('Width')))
  if cgireq.has_key('WIDTH') :
    size.append(int(cgireq.getvalue('WIDTH')))
  if cgireq.has_key('height') :
    size.append(int(cgireq.getvalue('height')))
  if cgireq.has_key('Height') :
    size.append(int(cgireq.getvalue('Height')))
  if cgireq.has_key('HEIGHT') :
    size.append(int(cgireq.getvalue('HEIGHT')))
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> width, height: ', size
  OGCreq['size'] = size;
#
  sbbox = []; # bbox as text list
  if cgireq.has_key('bbox') :
    cgibbox = cgireq.getfirst('bbox', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated bbox field specified: ", cgibbox
    sbbox = FileKeyUtils.parseCommas(cgibbox)
  if cgireq.has_key('Bbox') :
    cgibbox = cgireq.getfirst('Bbox', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated bbox field specified: ", cgibbox
    sbbox = FileKeyUtils.parseCommas(cgibbox)
  if cgireq.has_key('BBOX') :
    cgibbox = cgireq.getfirst('BBOX', "")
#   print >> FileKeyUtils.WMSlog, "OGCREST.parseWMSCGI> comma separated bbox field specified: ", cgibbox
    sbbox = FileKeyUtils.parseCommas(cgibbox)
    
  for item in sbbox :
    bbox.append(float(item))
#
# print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> bbox: ', bbox
  OGCreq['bbox'] = bbox
#
  print >> FileKeyUtils.WMSlog, 'OGCREST.parseWMSCGI> OGCreq{} == ', OGCreq
#
  return numlayers
#end parseWMS()

def preCacheLatLon(port, bbox):
# this is a place-holder; really hope to use the tilecache.org 'seeder' tool someday
  srs = 'SRS=EPSG:3410'  
  wms = 'http://gdev.sci.gsfc.nasa.gov:'+repr(port)+'/wmsc/wmscgiovanni.py/wmsc2km8km?Transparent=true&Format=image/png&Service=WMS&Request=GetMap&Width=256&Height=256&'
# layers = 'POLBNDA,INWATERA,OCEANSEA'
  layers = 'POLBNDA'
  wmsurl = wms + srs + '&Layers='+layers+'&Bbox='+repr(bbox[0])+','+repr(bbox[1])+','+repr(bbox[2])+','+repr(bbox[3])
  print >> FileKeyUtils.WMSlog, "OGCREST.preCacheLatLon> wmsurl: ", wmsurl
  urllib.urlretrieve(wmsurl, layers+'_'+repr(bbox[0])+'_'+repr(bbox[1])+'_'+repr(bbox[2])+'_'+repr(bbox[3])+'.png')
  layers = 'SummerBMNG'
  wmsurl = wms + srs + '&Layers='+layers+'&Bbox='+repr(bbox[0])+','+repr(bbox[1])+','+repr(bbox[2])+','+repr(bbox[3])
  print >> FileKeyUtils.WMSlog, "OGCREST.preCacheLatLon> wmsurl: ", wmsurl
  urllib.urlretrieve(wmsurl, layers+'_'+repr(bbox[0])+'_'+repr(bbox[1])+repr(bbox[2])+'_'+repr(bbox[3])+'.png')
#end preCacheLatLon

def preCachePolarProj(port, latlist):
  """
  Performs a series of urllib.urlretrieve invocations using WMS requests constructed for
  stereographic polar projections over the indicated list of lat. longs.
  """
  os.system('chmod -R g+rw /devstore/GIS/imgcache > /dev/null 2>&1')
  vmap0 = 'POLBNDA' # 'POLBNDA,INWATERA,OCEANSEA'
  vmap0H2O = 'INWATERA,OCEANSEA' # 'INWATERA,HYDROTXT,OCEANSEA,BNDTXT'
  wmapall = 'vmap0polh2o' # alias
# EPSG:3413 == north polar proj.
# EPSG:3412 == south polar proj.
  wms = 'http://gdev.sci.gsfc.nasa.gov:'+repr(port)+'/wmsc/wmscgiovanni.py/wmsc2km8km?Transparent=true&Format=image/png&Service=WMS&Request=GetMap&Width=700&Height=600&'
  bbox = [-90.0, 0.0]
  lon = -180.0
  print >> FileKeyUtils.WMSlog, "OGCREST.preCachePolarProj> wmsc: ", wms
  print >> FileKeyUtils.WMSlog, "OGCREST.preCachePolarProj> latlist: ", latlist
# while lon <= 180.0:
  while lon <= -175.0:
    lon = 10 + lon
    bbox[0] = lon
    for lat in latlist:
      if lat < 0 :
        srs = 'SRS=EPSG:3412'
        hemi = 'sp'
      else:
        srs = 'SRS=EPSG:3413'
	hemi = 'np'

      bbox[1] = lat
# bmng raster
      wmsurl = wms + srs+'&Layers=BMNG&Bbox='+repr(bbox[0])+','+repr(bbox[1])
      print >> FileKeyUtils.WMSlog, "OGCREST.preCachePolarProj> wmsurl: ", wmsurl
      urllib.urlretrieve(wmsurl, hemi+'bmng_'+repr(lon)+'_'+repr(lat)+'.png')
# vmap0 shapefile
      wmsurl = wms + srs+'&Layers='+vmap0+'&Bbox='+repr(bbox[0])+','+repr(bbox[1])
      print >> FileKeyUtils.WMSlog, "OGCREST.preCachePolarProj> wmsurl: ", wmsurl
      urllib.urlretrieve(wmsurl, hemi+'vmap0_'+repr(lon)+'_'+repr(lat)+'.png')
#   end lat for
# end lon while
  os.system('chmod -R g+rw /devstore/GIS/imgcache > /dev/null 2>&1')
# end preCachePolarProj

def renderPNG(req, OGCreq) :
  """
  This is the main entry point in to all the map projection functionality from a
  mod_python handler. Given the REST req. and fully initialized OGCReq has dict.
  args., proceeds to invoked either polar or latlon image map tile functions and
  writes the resultant PIL image as a PNG to the browser via the web server.
  """
  global _imgdict
# print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> OGCreq: ', OGCreq
  layers = OGCreq['layers']
  bbox = OGCreq['bbox']
  size = OGCreq['size']
  opacity = OGCreq['opacity']
  if opacity < 0 :
    opacity = 0 
  if opacity > 255 :
    opacity = 255 

  epsg = OGCreq['srs']
  img = None
  if epsg in GeoProj.NorthPolarEPSGlist:
    projname = GeoProj.NorthPolarProjlist[0] # 'npstere'
    key = FileKeyUtils.tileNameKey(projname, layers, size, bbox, 'C')
    if PILMemCache._imgdict.has_key(key):
      img = PILMemCache._imgdict[key] #; PILMemCache.manageImgdictRefCnt(key, img, 1)
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key present in global hash dict: ', key
    else:
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key NOT present in global hash dict: ', key
#     cntrLon = bbox[0] ; boundLat = bbox[1] # the bbox only needs these two values, ignore others
#     img = GeoImage.handleNorthPolarCentered(layers, opacity, size, cntrLon, boundLat) # origin at center of image
      img = GeoImage.handleNorthPolarCentered(layers, opacity, size, bbox) # origin at center of image
      if not(img == None):
        nimc = PILMemCache.manageImgdict(key, img) # PILMemCache.manageImgdictRefCnt(key, img, 0)
        print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', nimc:', nimc, ', new key in global hash dict: ', key
      else:
	print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> handleNorthPolarCentered retuned None!'
  elif epsg in GeoProj.SouthPolarEPSGlist:
    projname = GeoProj.SouthPolarProjlist[0] # 'spstere'
    key = FileKeyUtils.tileNameKey(projname, layers, size, bbox, 'C')
    if PILMemCache._imgdict.has_key(key):
      img = PILMemCache._imgdict[key] #; PILMemCache.manageImgdictRefCnt(key, img, 1)
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key present in global hash dict: ', key
    else:
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key NOT present in global hash dict: ', key
#     cntrLon = bbox[0] ; boundLat = bbox[1] # the bbox only needs these two values, ignore others
#     img = GeoImage.handleSouthPolarCentered(layers, opacity, size, cntrLon, boundLat) # origin at center of image
      img = GeoImage.handleSouthPolarCentered(layers, opacity, size, bbox) # origin at center of image
      if not(img == None):
        nimc = PILMemCache.manageImgdict(key, img) # PILMemCache.manageImgdictRefCnt(key, img, 0)
        print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', nimc:', nimc, ', new key in global hash dict: ', key
      else:
	print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> handleSouthPolarCentered retuned None!'
  else:
    projname = 'latlon'
    key = FileKeyUtils.tileNameKey(projname, layers, size, bbox, None) # origin not needed by mapnik api
    if PILMemCache._imgdict.has_key(key):
      img = PILMemCache._imgdict[key] #; PILMemCache.manageImgdict(key, img, 1)
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key present in global hash dict: ', key
    else:
      print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', key NOT present in global hash dict: ', key
      img = GeoImage.handleLatLon(layers, opacity, size, bbox) 
      if not(img == None):
        nimc = PILMemCache.manageImgdict(key, img) # PILMemCache.manageImgdictRefCnt(key, img, 0)
        print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> ', projname, ', nimc:', nimc, ', new key in global hash dict: ', key
      else:
	print >> FileKeyUtils.WMSlog, 'OGCREST.renderPNG> handleLatLon retuned None!'

  if img == None:
    req.content_type = 'text/plain'
    req.write('WMSGIOVANNI unable to generate requested projection...')
    printReq(req)
    return

  # send html header and image
  req.content_type = 'image/png'
  img.save(req, 'png') # PIL save/write to req obj. behaves like file obj.
  del img # not clear that PIL memory management actually frees this!
#end renderPNG

def WMSModPyHandler(req):
  """
  General purpose mod_python handler entry point into OGCWMS system. Opens log file
  and makes use of module functions to parse the request., then invokes the renderPNG
  func.
  """
# while the ogc standard only indicates transparent == true or false, let's allow an alpha
# range 0-255:
# OGCreq = { 'request' : 'GetMap', 'service' : 'WMS', 'format' : 'image/png', 'styles' : '',
#            'srs' : 'EPSG:3226', 'exceptions' : 'ExceptionGIF',
#            'opacity' : 255, 'size' : [1024,512],
#            'bbox' : [-180.0, -90.0, 180.0, 90.0],
#            'layers' : ['world','USstate'] }
  OGCreq = { 'request' : 'GetMap', 'service' : 'WMS', 'format' : 'image/png', 'styles' : '',
             'srs' : 'EPSG:3226', 'exceptions' : 'ExceptionGIF',
             'opacity' : 255, 'size' : [1024,512],
             'bbox' : [-90.0, 0.0, 0.0, 0.0],
             'layers' : ['POLBNDA','UScounty'] }

  root = htdocRoot(req)
  log = '/devstore/apache2/logs95/wmsmodpy.log' + '95'
  FileKeyUtils.openWMSlog(logfile=log)
  numlayers = parseWMS(req, OGCreq)
  if numlayers <= 0 :
    print >> FileKeyUtils.WMSlog, 'OGCREST.WMSModPyHandler> no layers returned from OGCREST.parseWMS'
    print >> FileKeyUtils.WMSlog, 'OGCREST.WMSModPyHandler> req: ', OGCreq
    FileKeyUtils.closeWMSlog()
    req.content_type = 'text/plain'
    req.write('No layers returned from OGCREST.parseWMS?')
    req.write('WMSGIOVANNI unable to generate requested projection...')
    printReq(req)
    return

  bbox = OGCreq['bbox']
  if len(bbox) <= 1 :
    print >> FileKeyUtils.WMSlog, 'OGCREST.WMSModPyHandler> bad bbox returned from OGCREST.parseWMS'
    print >> FileKeyUtils.WMSlog, 'OGCREST.WMSModPyHandler> req: ', OGCreq
    FileKeyUtils.closeWMSlog()
    req.content_type = 'text/plain'
    req.write('No BBOX returned from OGCREST.parseWMS?')
    req.write('WMSGIOVANNI unable to generate requested projection...')
    printReq(req)
    return

  renderPNG(req, OGCreq)

  FileKeyUtils.closeWMSlog()
  return
#end wms mod_python publisher handler WMSModPyHandler

def WMS500mModPyHandler(req):
  """
  Special purpose mod_python handler for BMNG 500m resolution map tile projection images/
  """
# Raster.initBMNG500mPImgs()
# nimg500 = Raster.initBMNG500mVImgs()
# nimg2km = Raster.initBMNG2kmVImgs()
# nimg8km = Raster.initBMNG8kmVImgs()
# print >> FileKeyUtils.WMSlog, 'OGCREST.WMS500mModPyHandler>', nimg500 + nimg2km + nimg8km
  return WMSModPyHandler(req)

def WMS2km8kmModPyHandler(req):
  """
  Special purpose mod_python handler for BMNG 2k and 8km resolution map tile projection images/
  """
# Raster.initBMNG2kmPImgs()
# nimg2km = Raster.initBMNG2kmVImgs()
# nimg8km = Raster.initBMNG8kmVImgs()
# print >> FileKeyUtils.WMSlog, 'OGCREST.WMS2kmModPyHandler>', nimg2km + nimg8km
  return WMSModPyHandler(req)

def WMS8kmModPyHandler(req):
  """
  Special purpose mod_python handler for BMNG 8k resolution map tile projection images/
  """
# Raster.initBMNG8kmPImgs()
# nimg8km = Raster.initBMNG8kmVImgs()
# print >> FileKeyUtils.WMSlog, 'OGCREST.WMS8kmModPyHandler>', nimg8km
  return WMSModPyHandler(req)

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print _modinfo
  help("OGCREST")

if __name__ ==  '__main__' :
  """
  Unit test main for OGCREST module, '-p' or '-l' precache options
  invoke the precache functions.
  """
  port = 9595
  print >> FileKeyUtils.WMSlog, sys.argv, _argv, port
# while the ogc standard only indicates transparent == true or false, let's allow an alpha
# range 0-255: 
  OGCreq = { 'request' : 'GetMap', 'service' : 'WMS', 'format' : 'image/png', 'styles' : '',
             'srs' : 'EPSG:3226', 'exceptions' : 'ExceptionGIF', 
             'opacity' : 128, 'size' : [500,300],
             'bbox' : [-180.0,-90.0,180.0,90.0],
             'layers' : ['a','b','christopher','david','e','f','gregory','hon'] }

# wmsreqshp = urlCascade("http://gdev.sci.gsfc.nasa.gov:9090/nov2007/esrishpwms.cgi")
# print >> FileKeyUtils.WMSlog, "OGCREST.OGCreq> tile req.: ", wmsreqshp
# wmsreq = urlCascade(' ')
# print >> FileKeyUtils.WMSlog, "OGCREST.OGCreq> tile req.: ", wmsreq
  if len(_argv) > 1 :
    if _argv[1] in ('-p', '-pol', '-polar'):
      print >> FileKeyUtils.WMSlog, 'precache north and south polar projections...'
#     northlat = [0.01, 5., 10., 15., 20., 25., 30., 35., 40., 45., 50., 55., 60., 65., 70., 75., 80., 85.]
      northlat = [0.01]
      preCachePolarProj(port, northlat)
#     southlat = [-0.01, -5., -10., -15., -20., -25., -30., -35., -40., -45., -50., -55., -60., -65., -70., -75., -80., -85.]
      southlat = [-0.01]
      preCachePolarProj(port, southlat)
    if _argv[1] in ('-l','-ll','-lalo'):
      bbox = [-135.0, 0.0, -90, 90] # north america
      if len(_argv) > 5:
        bbox = [ float(_argv[2]), float(_argv[3]), float(_argv[4]), float(_argv[5]) ] 
      print >> FileKeyUtils.WMSlog, 'precache latlon projection, bbox:', bbox
      preCacheLatLon(port, bbox)
  else :
    printSysInfo({}, OGCreq)

