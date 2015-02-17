#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/FileKeyUtils.py $'
svnId = rcsId = '$Name:  $ $Id: .FileKeyUtils.py,v 1.1 2008/05/22 15:40:06 dhon Exp $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
Module FileKeyUtils provides logging, image cache file name, I/O and
management, along with memcache hash dict. key name construction
funcs.
"""
#
import os, sys, time, copy
#from mod_python import apache
from PIL import Image
#import G3WMS.GeoProj as GeoProj
import GeoProj
import Raster

# global datasource location
DataStore = '/devstore/GIS/'
#ImgCache = DataStore + 'imgcache/' # 'ops' diskcache
#ImgCache = DataStore + 'scratch/imgcache/' # 'debug' diskcache
ImgCache = DataStore + 'EditMePNGCacheDir/' # make target editme uses $(CACHEDIR) to set/sed EditMePNGCacheDir
VMAP0Store = DataStore + 'VMAP0/'
USAStore = DataStore + 'USA/'
BMNG8kmStore = DataStore + 'BMNG/world_8km/'
BMNG2kmStore = DataStore + 'BMNG/world_2km/'
BMNG500mStore = DataStore + 'BMNG/world_500m/'

#
WMSlog = None
def closeWMSlog():
  """
  Supports log trace of WMS logic
  """
  global WMSlog
  global _logrefcnt
  if WMSlog == None:
    return
  t = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
  print >> WMSlog, 'FileKeyUtils.openWMSlog> ====================== close log @', t, '======================='
  WMSlog.close() 
  WMSlog = None
#end closeWMSlog

def openWMSlog(logfile='/devstore/apache2/logs/wms.log'):
  """
  Supports log trace of WMS logic
  """
  global WMSlog
  if not(WMSlog == None):
    return # already opened

  t = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
  try:
    WMSlog = open(logfile, 'a')
    print >> WMSlog, 'FileKeyUtils.openWMSlog> ====================== open log @', t, '========================'
  except:
    WMSlog = None
  return
#end openWMSlog

def replaceStr(sval, chold, chnew):
  """
  Returns a deep copy string value that contains replaced sub-text.
  """
  s = copy.deepcopy(sval)
  done = False
  nch = len(chold)
  while not(done):
    try:
      p = s.index(chold)
      if p >= 0 : # replace with chnew
        left = s[0:p]
        right = s[p+nch:]
        s = left + chnew + right
    except:
      done = True

  return s
# replaceStr

def parseDelim(s, d):
  """
  Returns list of words parsed from string s, using specified delimiter d.
  """
# print >> WMSlog, 'FileKeyUtils.parseDelim> d: ', d, ', in s: ', s, '\n'
  lis = []
  p = -1;
  while True :
    p0 = 1 + p;
    try :
      p = s.index(d, p0)
      lis.append(s[p0:p])
#     print >> WMSlog, 'FileKeyUtils.parseCommas> lis: ', lis, '\n'
    except:
      lis.append(s[p0:])
#     print >> WMSlog, 'FileKeyUtils.parseCommas> return parse list: ', lis, '\n'
      return lis
#end parseDelim

def parseAmpers(s):
  return parseDelim(s, '&')

def parseCommas(s):
  return parseDelim(s, ',')

def parseEqual(s):
  return parseDelim(s, '=')

def tileNameKey(projname, layerlist, size, bbox, origin):
  """
  Returns a string suitable for use as a hash dict. key and/or
  an image (PNG) filename prefix from the args. provided:
  0. projection name (see names supported in GeoProj module)
  1. list/arrsy of layer names or aliases
  2. size == [width, height]
  3. bbox == [polar center lon., polar bounding lat.]
          or [min. lon., min lat., max lon., max lat.]
  4. origin == 'C', or other polar GeoProj.Anchor[]
            or None
  """
# note that for pole centered projections the bbox should
# contain only two values: center longitude and outermost lat
# otherwise expect the usual lonlatmin/max 4 element rect.
  name = projname
  for layer in layerlist:
    name += layer + '_'

  key = name+repr(size[0])+'x'+repr(size[1])
  if not(origin == None):
    key += origin

  if projname in GeoProj.PolarProjlist:
    for b in bbox[0:2]:
      key += '_' + repr(b)
  else:
    for b in bbox:
      key += '_' + repr(b)

  print >> WMSlog, 'FileKeyUtils.tileNameKey> key: ', key
  return key

def tileNameInfoKey(projname, layerlist, size, bbox, origin):
  """
  Support notion of two related/correltaed hash dict. key strings:
  and 'Info:key' and it corresponding 'Data:key'
  """
  return 'Info:'+tileNameKey(projname, layerlist, size, bbox, origin)

def tileNameFile(projname, layerlist, size, bbox, origin):
  """
  (deprecated) Returns string suitable for image tile file name prefix.
  """
  filename = tileNameKey(projname, layerlist, size, bbox, origin)
# filename += '.png'
  return filename

def tileNamePath(projname, layername, opacity, size):
  """
  Returns string containing a full directory path specirfication
  using the args. supplied and the DataStore and ImgCache globals.
  Also insures that the full set of subdirectories indicated in
  the path exist.
  """
  global DataStore
  global ImgCache

  filepath = DataStore
  try:
    os.mkdir(filepath) # make sure the directory exists!
  except: pass
#   return None
  filepath = ImgCache
  try:
    os.mkdir(filepath) # make sure the directory exists!
  except: pass
#   return None
  filepath += projname
  try:
    os.mkdir(filepath) # make sure the directory exists!
  except: pass
#   return None
  filepath += '/'+layername+'/'
  try:
    os.mkdir(filepath) # make sure the directory exists!
  except: pass
#   return None
  filepath += repr(opacity)+'alpha'+repr(size[0])+'x'+repr(size[1])+'/'
  try:
    os.mkdir(filepath) # make sure the directory exists!
  except: pass
#   return None

  return filepath

def tileNameFullPath(projname, layerlist, opacity, size, bbox, origin):
  """
  Returns string containing a full file name prefix with directory path
  specification using the args. supplied and the DataStore and ImgCache globals.
  Also insures that the full set of subdirectories indicated in
  the path exist.
  """  
  if isinstance(layerlist, str):
    layername = layerlist
  else:
    layername = layerlist[0]

# include first layer of layerlist in directory path name 
  filepath = tileNamePath(projname, layername, opacity, size)
# print >> WMSlog, 'FileKeyUtils.tileNameFullPath> filepath: ', filepath
  filename = tileNameFile(projname, layerlist, size, bbox, origin)
# print >> WMSlog, 'FileKeyUtils.tileNameFullPath> filename: ', filename
  file = filepath+filename
  print >> WMSlog, 'FileKeyUtils.tileNameFullPath> file path+name: ', file
  return file

def tilePNGPath(projname, layerlist, opacity, size, bbox, origin):
  """
  Returns string containing a full image file name (fileprefix.png)
  with directory path specification using the args. supplied and the
  DataStore and ImgCache globals.
  Also insures that the full set of subdirectories indicated in
  the path exist.
  """  
  tilepng = tileNameFullPath(projname, layerlist, opacity, size, bbox, origin)
  tilepng += '.png'
  return tilepng
# end tilePNGPath

def rasterNameFullPath(layerlist, bmngres=None):
  """
  For low to med. res. rasters, returns string containing a full image file
  name with directory path specification using the args. supplied and the
  DataStore global. Currently only supports BMNG raster PNGs or TIFFs.
  For high res. resters, returns hash dict. of all relevant full file names.
  """ 
  if isinstance(layerlist, str):
    layername = layerlist
  else:
    layername = layerlist[0]

  rasterfile = None
  if bmngres == None:
    # check for initialized BMNG images:  
#   if len(Raster._BMNG500mVImgs) > 0 or len(Raster._BMNG500mPImgs) > 0:
#     rasterfile = BMNG500mStore + GeoProj.layerFileBMNG500m(layername)
    if len(Raster._BMNG2kmVImgs) > 0 or len(Raster._BMNG2kmPImgs) > 0:
      km2 = GeoProj.layerFileBMNG2km(layername)
      if not( km2 == None ): rasterfile = BMNG2kmStore + km2
    if len(Raster._BMNG8kmVImgs) > 0 or len(Raster._BMNG8kmPImgs) > 0:
      km8 = GeoProj.layerFileBMNG8km(layername)
      if not( km8 == None): rasterfile = BMNG8kmStore + km8

  if bmngres == 'BMNG8km':
    km8 = GeoProj.layerFileBMNG8km(layername)
    if not( km8 == None): rasterfile = BMNG8kmStore + km8
  if bmngres == 'BMNG2km':
    km2 = GeoProj.layerFileBMNG2km(layername)
    if not( km2 == None): rasterfile = BMNG2kmStore + km2
  if bmngres == 'BMNG500m':
    rasterfile = {}
    for key, val in GeoProj.layerFileBMNG500m(layername):
      if not( val == None): rasterfile[key] = BMNG500mStore + val

  return rasterfile # single string for res < 500m, dict of 8 elem for 500m 
#end rasterNameFullPath

def toRGBAlpha(alpha, imgfile):
  """
  Adds an alpha plane (using arg. values) to the RGB PNG image file to create
  an RGBA file, overwriting the original file.
  """
  img = Image.open(imgfile)
  img.putalpha(alpha)
  img.save(imgfile)
# end toRGBAlpha

def toRGBAlphaFile(alpha, size, folder, prefix) :
  """
  Adds an alpha plane (using arg. values) to the RGB PNG image and creates
  a new RGBA file to create. Creates another resized image file for
  'quick-look' purposes. This behavior should be changed to perform
  only one or the other optionally, perhaps tiriggered by the size arg... 
  """
  alpha = 127; w = size[0]; wq = w/32; h = size[1]; hq = h/32
# alpha = 127; w=21600 ; wq = w/32; h=10800; hq = h/32
# folder = 'world_2km/'
# prefix = 'world.topo.bathy.200407.3x'
  pngfile = prefix+repr(w)+'x'+repr(h)+'.png'
  img=Image.open(folder+pngfile) # 'lazy' open does not cause any i/o
  pix=img.load() # force read of entire image file
  img.putalpha(alpha)
  img.save(folder + repr(alpha) + pngfile)
  qlook = img.resize([wq,hq])
  qlfile = prefix+repr(wq)+'x'+repr(hq)+'.png'
  qlook.save(folder + repr(alpha) + qlfile)
#end toRGBAlpha

def mapPNGToStdOut(file):
  """
  Reads specified file (must be fully specified path/imagefile.png);
  checks content to insure it is indeed a PNG, and if not, renames it,
  otherwise writes result to stdout. This important 'check/side-affect'
  insures the integrity of the image cache, and helps prevent all sorts
  of badly handled errors, especially with the 'WMSCascade' feature.
  """
# check if imagefile has been cached
# note that a cached file may contain errors
# so take this opportunity to remove any bogus files from cache
# read the 'cached' map image file and perform binary write to stdout
  try:
    png = open(file, "rb").read()
  except:
    return False

  filetype = png[0:4]
  try:
    if filetype.index('PNG') >= 0 :
      typePNG = True
      sys.stdout.write(png)
      return True
# or use PIL
#    im = Image.open(file)
#    im.save(sys.stdout,'png')
  except:
    pass

# and remove any non PNG file present
  try:
#   os.remove(file)
    if file.rindex('/') >= 0 :
      path = file[0:file.rindex('/')+1]
      name = file[1+file.rindex('/'):]  
      renamefile = path + '.' + name # rename it to a hidden file
      os.rename(file, renamefile)
  except:
    pass

  return False
#end mapPNGToStdOut(file)

def mapPILToStdOut(img):
  """
  Writes PIL img arg. content out to stdout as PNG.
  """
# print >> WMSlog, 'FileKeyUtils.mapPILToStdOut> img mode, size: ', img.mode, ', ', img.size
  img.save(sys.stdout, 'png')
#end mapPILToStdOut

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print _modinfo
  help("FileKeyUtils")

if __name__ ==  '__main__' :
  """
  Logs DataStore, ImgCache global text settings.
  """
  arg0 = sys.argv.pop(0)
# consider providing imgcache directory as arg...
  print >> WMSlog, 'FileKeyUtils.printInfoDoc> datastore, imgcache: ', DataStore, ImgCache
