#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/PILMemCache.py $'
svnId = rcsId = '$Name$ $Id: PILMemCache.py 24 2008-04-01 06:19:16Z hon $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
The PILMemCache module provides functions for 'pickling' PIL Image
objects and for their insertion and extraction to/from one
or more 'memcached' daemons. 
"""

import os, sys, time, zlib
import copy, cPickle, mmap
import numpy
import memcache
from PIL import Image
#import G3WMS.FileKeyUtils as FileKeyUtils
import FileKeyUtils

# memcached globals
_mcached = dict(IP='127.0.0.1', port=[11110,11111,11112,11113,11114,11115,11116,11117,11118,11119])
_mconnections = {11110:None, 11111:None, 11112:None, 11113:None, 11114:None,
                 11115:None, 11116:None, 11117:None, 11118:None, 11119:None}

# segregate vmap0 tile results and raster/(png,jpg?) tile results in respective cacheds:
#_mctileports = {'VMAP0LatLon':11110, 'VMAP0NorthPole':11111, 'VMAP0SouthPole':11112,
#                'RasterLatLon':11113, 'RasterNorthPole':11114, 'RasterSouthPole':11115}

# the above can be used when we have enough ram to run lots more memcacheds
# for now let's just run 3
_mctileports = {'LatLon':11110, 'NorthPole':11111, 'SouthPole':11112}

# for use with the 'allkey' content lists:
_mcontentkeys = {11110:'MContent0', 11111:'MContent1', 11112:'MContent2',
                 11113:'MContent3', 11114:'MContent4', 11115:'MContent5',
                 11116:'MContent6', 11117:'MContent7', 11118:'MContent8', 11119:'MContent9'}

# the 'allkey' content lists:
_mcontent = {11110:[], 11111:[], 11112:[], 11113:[], 11114:[],
             11115:[], 11116:[], 11117:[], 11118:[], 11119:[]}

# Use Heap space cache?
_UseHeapCache = False 
# httpd process/mod_python globals:
_imglimit = 36*18 # assuming global 10 deg. incr. in lat-lon
_keylist = [] # alt. to dict refcnt

# this approach may result in memory exhaustion
# there is an interesting discussion of python mem. alloc. issues
# (partially) fixed/improved in 2.5 at http://evanjones.ca/memoryallocator
_imgdict = {}
_imgrefcnt = {}

def manageImgdict(key, img):
  """
  The mod_python application can use internal (apache process RAM) memory
  to store a hash dict. of PIL Images for immediate delivery to a browser
  WMS client. This function provides the means to insert newly created images,
  and once the internal memory limit is reached, removes older images.
  """
  global _imglimit
  global _keylist
  global _imgdict
  global _UseHeapCache

  if not(_UseHeapCache):
    return 0 # (no-op) let's not use the heap-space cache for now...

# use imglist and imgdict rather than refcnt
  if _imgdict.has_key(key):
    print >> FileKeyUtils.WMSlog, 'PILMemCache.manageImgdict> _imgdict has key:', key
    return len(_imgdict)

  _keylist.append(key)
  _imgdict[key] = img
  print >> FileKeyUtils.WMSlog, 'PILMemCache.manageImgdict> inserting new img, imgcnt:', len(_imgdict), ', key:', key

  if len(_imgdict) > _imglimit :
# remove oldest resident image
    key0 = _keylist.pop(0)
    img0 = _imgdict.pop(key0) # should be == pop(0)
    del img0 ; del key0
    print >> FileKeyUtils.WMSlog, 'PILMemCache.manageImgdict> reached limits, pop & removed:', key0

  return len(_imgdict)
# end manageImgdict

def manageImgdictRefCnt(key, img, cnt):
  """
  Alternative image management func. that attempts a simpleminded way to insure
  hashdicts don't exhaust httpd process memory. Not currently used.
  """
# simpleminded way to insure hashdict don't exhaust httpd process memory
  global _imglimit
  global _imgdict
  global _imgrefcnt
  if cnt <= 0:
    _imgrefcnt[key] = 1 ;  _imgdict[key] = img
  elif _imgrefcnt.has_key(key):
    rcnt = _imgrefcnt[key] ; _imgrefcnt[key] = 1 + rcnt
  else:
    _imgrefcnt[key] = 1 ; _imgdict[key] = img

# check how large the imgdict has grown and remove
# a somewhat aribtrary item, if dict is too large
  imgcnt = len(_imgdict)
  if imgcnt <= _imglimit:
    return imgcnt

# search for img (other than the one just handled) with a low refcnt
# (little used) end remove it
  c = 1.0
# while True:
  while c < 100000.0: # try to avoid an infinite loop that never returns
    c = 2*c # try to keep the search quick by doubling-up the min. refcnt.
    for k in _imgrefcnt.keys():
      rcnt = _imgrefcnt.pop(k)
      if k != key:
        if rcnt < c:
          dimg = _imgdict.pop(k) ; del dimg ; del rcnt
          return len(_imgdict)
  return len(_imgdict)
# end manageImgdictRefCnt

def memcacheAddContent(mcserver, content):
  """
  Inserts/replaces info. key old content with new.
  """
  global _mcontentkeys
  global _mcontent
  mcIP = mcserver['IP']; mcport = mcserver['port']
  mckey = _mcontentkeys[mcport] # key for all contents of memcached with port #
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  fullcontents = _mcontent[mcport] = mc.get(mckey) # fetch list of all keys in mcache
  if fullcontents == None:
    _mcontent[mcport] = fullcontents = [content]
    mc.set(mckey, fullcontents)
    return fullcontents

  fullcontents += content
  _mcontent[mcport] = fullcontent
  mc.replace(mckey, fullcontents)
  return fullcontents
  
def memcacheGetContent(mcserver):
  """
  Fetches the full content (list of all info. keys) of the specified memcached
  server and returns list.
  """
  global _mcontentkeys
  global _mcontent
  mcIP = mcserver['IP']; mcport = mcserver['port']
  mckey = _mcontentkeys[mcport] # key for all contents of memcached with port #
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  fullcontents = _mcontent[mcport] = mc.get(mckey) # fetch list of all keys in mcache
  return fullcontents
  
def memcacheStats(mcserver):
  """
  Fetches the current connection (and other) status of the specified memcached
  server and (optionally prints it to the log) and returns hash dict.
  """
  mcIP = mcserver['IP']; mcport = mcserver['port']
  global _mconnections
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  stats = mc.get_stats()
# print >> FileKeyUtils.WMSlog, stats
  return stats

def memcachePutPNG(png, pngkey, mcserver):
  """
  Method for inserting a PNG image into a memcached via 'Cpickle'.
  """
  mcIP = mcserver['IP']; mcport = mcserver['port']
  global _mconnections
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  mdmp = png
  mdmp = cPickle.dumps(png, protocol=2)
# mdmp = numpy.asarray(png)
# zlib compress level 3 is fast and produces something sufficiently small for memcache (range is 1-9)
# mdmp = zlib.compress(png, 3) # 3 is faster than the default 6, but bigger
  try:
    s = mc.set(pngkey, mdmp)
    print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPNG> put png key: ', pngkey, ', set status return s: ', s
  except:
    print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPNG> failed put png! pngkey: ', datakey, ', set status return s: ', s
    return None

  return pngkey

def memcacheGetPNG(pngkey, mcserver):
  """
  Method for extracting a PNG image from a memcached via 'Cpickle'.
  """
  mcIP = mcserver['IP']; mcport = mcserver['port']
  global _mconnections
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  try:
    mppng = mc.get(pngkey)
    if mppng == None:
      print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPNG> memcache get returned None for key: ', pngkey
      return None
  except:
    print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPNG> memcache get failed for key: ', pngkey
    return None

  mpng = cPickle.loads(mppng)
  return mpng

def memcachePutPIL(pim, imgkeys, mcserver):
  """
  Method for inserting a PIL Image into a memcached via 'zlib compression'.
  Currently compression level == 3 is used, this is fast and sufficiently
  compressed to handle 512x512 RGBA images, but larger one may be problematic.
  There is a limit to the size of an object the memcached protocal supports.
  """
  global _mconnections
  global _mcontent
  imginfo = dict(mode=pim.mode, size=pim.size)
  mcIP = mcserver['IP']; mcport = mcserver['port']

  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  infokey = imgkeys['info']; datakey = imgkeys['data']
# zlib compress level 3 is fast and produces something sufficiently small for memcache (range is 1-9)
  mdmp = zlib.compress(pim.tostring(), 3) # 3 is faster than the default 6, but bigger
# mdmp = cPickle.dumps(spim, protocol=2)
# mdmp = numpy.asarray(pim)
# mdmp = pim.tostring()
  si =  mc.set(infokey, imginfo)
  print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPIL> mcache put image info: ', infokey, imginfo # mc.get(infokey)
  sd = mc.set(datakey, mdmp)
  print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPIL> put image datakey: ', datakey, ', mcport: ', mcport
  mckey = _mcontentkeys[mcport] # key for all contents of memcached with port #
  if not( infokey in _mcontent[mcport] ):
    _mcontent[mcport].append(infokey) 
    s = mc.set(mckey, _mcontent[mcport])
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPIL> set newContent: ', _mcontent[mcport]
  else:
    print >> FileKeyUtils.WMSlog, 'PILMemCache.memcachePutPIL> failed put newContent list: ', mckey

# mim = Image.fromstring(mc.get(datakey))
# mim.show()
  return imginfo

def memcacheGetPIL(imgkeys, mcserver):
  """
  Method for extracting a compressed PIL image from a memcached via 'zlib'.
  """
  mcIP = mcserver['IP']; mcport = mcserver['port']
  global _mconnections
  if _mconnections[mcport] == None:
    mcId = mcIP + ':' + repr(mcport)
    mc = _mconnections[mcport] = memcache.Client([mcId], debug=0)
  else:
    mc = _mconnections[mcport]

  infokey = imgkeys['info'];
  imginfo = mc.get(infokey)
  if imginfo == None:
    print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPIL> failed mcache get image info: ', infokey
    return None
  datakey = imgkeys['data'];
  print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPIL> mcache get image datakey: ', datakey
  mdmp = None
  try:
    mdmp = mc.get(datakey)
    if mdmp == None:
      print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPIL> memcache get returned None'
    else:
#     mim = Image.fromarray(imginfo['mode'], imginfo['size'], mdmp)
#     mim = Image.fromstring(imginfo['mode'], imginfo['size'], mdmp)
      dcm = zlib.decompress(mdmp)
      mim = Image.fromstring(imginfo['mode'], imginfo['size'], dcm)
      print >> FileKeyUtils.WMSlog, 'PILMemCache.memcacheGetPIL> memcache get returned ', mim.mode, mim.size
#     mim.show()
      return mim
  except: pass
  return None

def picklePutPIL(pim, pfile):
  """
  Returns PIL Image info: imginfo['mode'], imginfo['size'] via cPickle file I/O read,
  given the Image object pim and the filename full path pfile args.
  """
# dmp = pim.tostring()
  dmp = zlib.compress(pim.tostring(), 3)
# dmp = cPickle.dumps(spim, protocol=2)
# mm=mmap.mmap(bf.fileno(), 0)
  pf=open(pfile, mode='w+'); cPickle.dump(dmp, pf, protocol=2); pf.close()
# dmp = numpy.asarray(pim); dmp.dump(pfile)
  imginfo = dict(mode=pim.mode, size=pim.size)
  print >> FileKeyUtils.WMSlog, 'PILMemCache.picklePutPIL> (with zlib compression level == 3) ', imginfo
  return imginfo
#end picklePutPIL

def pickleGetPIL(imginfo, pfile):
  """
  Returns PIL Image opbject via cPickle file I/O read, given the image attribute
  info: imginfo['mode'], imginfo['size'], and the filename full path args.
  """
  f=open(pfile, mode='r'); sim=cPickle.load(f); f.close()
  dsim = zlib.decompress(sim)
  im=Image.fromstring(imginfo['mode'], imginfo['size'], dsim)
# im=Image.fromarray(numpy.load(pfile))
  print >> FileKeyUtils.WMSlog, 'PILMemCache.pickleGetPIL> (via zlib decompression) ', im.mode, im.size
# im.show()
  return im
#end pickleGetPIL

def testPILPut(mcserver):
  """
  Performs a set of puts (and gets) of PIL Images to test the memcached interface(s).
  """
  filetyp = 'png'
# pix = im.load()
# im.show()
# print >> FileKeyUtils.WMSlog, 'PILMemCache.PILMemCache> pix load image:', im.mode, im.size
# sys.exit(0)
# tile = im.resize([256,256])
# tile.save(filenm+'256x256.png')
# tile = Image.open(filenm+'256x256.png')
# pfile = filenm+'256x256.pickle'
# info = picklePutPIL(tile, pfile)
# pim = pickleGetPIL(info, pfile)
# pim.show()
  path = '/devstore/GIS/BMNG/world_8km/' ; filenm = 'world.topo.bathy.200401.3x5400x2700'
  tile = im = Image.open(path+filenm+'.'+filetyp)
  tile = im.resize([1024,512])
  bmng = filetyp+'BMNG'+repr(tile.size[0])+'x'+repr(tile.size[1])
  imgkeys = dict(info='Info:'+bmng, data='Data:'+bmng)
  imginfo = memcachePutPIL(tile, imgkeys, mcserver)

  path = './PNGs/'
  filenm = 'g3-d'
  tile = im = Image.open(path+filenm+'.'+filetyp)
  g3d = filetyp+'G3-D'+repr(tile.size[0])+'x'+repr(tile.size[1])
  imgkeys = dict(info='Info:'+g3d, data='Data:'+g3d)
  imginfo = memcachePutPIL(tile, imgkeys, mcserver)
# mim = memcacheGetPIL(imgkeys, mcserver)
# if not( mim == None ):
#   mim.show()
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> keys: ', imgkeys,', server: ', mcserver
# else:
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> failed, keys: ', imgkeys,', server: ', mcserver

  path = './PNGs/'
  filenm = 'VOWorldUScounty1024x512'
  tile = im = Image.open(path+filenm+'.'+filetyp)
  v0 = filetyp+'VOWorldUScounty'+repr(tile.size[0])+'x'+repr(tile.size[1])
  imgkeys = dict(info='Info:'+v0, data='Data:'+v0)
  imginfo = memcachePutPIL(tile, imgkeys, mcserver)
# mim = memcacheGetPIL(imgkeys, mcserver)
# if not( mim == None ):
#   mim.show()
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> keys: ', imgkeys,', server: ', mcserver
# else:
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> failed, keys: ', imgkeys,', server: ', mcserver

  filenm = '255northpolarBMNG_512x512C90.0_0.0bbox=-180.0_0.0_-90.0_0.0'
  tile = im = Image.open(path+filenm+'.'+filetyp)
  pnorbmng = filetyp+'PNorBMNG'+repr(tile.size[0])+'x'+repr(tile.size[1])
  imgkeys = dict(info='Info:'+pnorbmng, data='Data:'+pnorbmng)
  imginfo = memcachePutPIL(tile, imgkeys, mcserver)
# mim = memcacheGetPIL(imgkeys, mcserver)
# if not( mim == None ):
#   mim.show()
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> keys: ', imgkeys,', server: ', mcserver
# else:
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> failed, keys: ', imgkeys,', server: ', mcserver

  filenm = '255southpolarBMNG_512x512C-90.0_0.0bbox=-180.0_0.0_-90.0_0.0'
  tile = im = Image.open(path+filenm+'.'+filetyp)
  psoubmng = filetyp+'PSouBMNG'+repr(tile.size[0])+'x'+repr(tile.size[1])
  imgkeys = dict(info='Info:'+psoubmng, data='Data:'+psoubmng)
  imginfo = memcachePutPIL(tile, imgkeys, mcserver)
# mim = memcacheGetPIL(imgkeys, mcserver)
# if not( mim == None ):
#   mim.show()
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> keys: ', imgkeys,', server: ', mcserver
# else:
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILPut> failed, keys: ', imgkeys,', server: ', mcserver

  memcacheStats(mcserver)
  print >> FileKeyUtils.WMSlog, memcacheGetContent(mcserver)
#end testPILPut

def dataKeyFromInfoKey(infokey):
  """
  Insures that the data key and the info. key for a specific PIL Image
  hash dict. element are self consistent. Once an info key is generated,
  this function should be used to generate the associated data key.
  """
  keyelem = FileKeyUtils.parseDelim(infokey, ':')
  datakey = 'Data:' + keyelem[1]
  return datakey

def testPILGet(mcserver):
  """
  Performs a single get of a PIL Image to test the memcached interface.
  """
  mim = None
  infokeys = memcacheGetContent(mcserver)
  for k in infokeys:
#   print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILGet key: ', k,', server: ', mcserver 
    d = dataKeyFromInfoKey(k)
    imgkeys = dict(info=k, data=d)
    print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILGet> keys: ', imgkeys,', server: ', mcserver 
    mim = memcacheGetPIL(imgkeys, mcserver)
    if not( mim == None ):
      print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILGet> ', mim.mode, mim.size, ' keys: ', imgkeys,', server: ', mcserver 
#     mim.show()
    else:
      print >> FileKeyUtils.WMSlog, 'PILMemCache.testPILGet> failed, keys: ', imgkeys,', server: ', mcserver

def testPNG(mcserver, filenmame):
  """
  Performs a single iput and get of a PNG file to test the memcached interface.
  """
# filenm = 'g3-d'
  filenm = 'BMNGwarped2ups'
  if not(filename == None):
    if len(filename) > 0:
      filenm = filename
  filetyp = 'png'
  file = filenm + '.' + filetyp 
  key = filetyp + filenm
  try:
    png = open(file, "rb").read()
    memcachePutPNG(png, key, mcserver)
    mp = memcacheGetPNG(key, mcserver)
  except:
    print >> FileKeyUtils.WMSlog, 'PILMemCache.testPNG> open failed: ', file
#end testPNG

def testContents():
  """
  Performs a memcache get of the 'full content' special purpose
  hash dict. object that should contain all the info. keys of all
  the PIL Image objects currently resident in the memory cache.
  Prints out the results, but does not return anything.
  """
  global _mcached
  memcd = 'memcached -d -k -m 2048 -l 127.0.0.1 -p ' # + repr('11111')
  for p in range(0,3):
    portno =_mcached['port'][p]
#   startmemcd = memcd + repr(portno) ; os.system(startmemcd) 
    mcserver = dict(IP=_mcached['IP'], port=portno)
    contents = memcacheGetContent(mcserver)
    print >> FileKeyUtils.WMSlog, 'PILMemCache.testContents> portNo: ', portno, ', allkeys (contents):\n'
    print >> FileKeyUtils.WMSlog, contents
#end testContents

def viewPNGs(pnglist):
  """
  Relies on an externally installed 'xv' binary application that must be
  found in the user environment to display the list of PNG files specified
  in the arg.
  """
# only works if xv app. is in path
  if len(pnglist) <= 0: # check cmd-line args:
    args = copy.deepcopy(sys.argv)
    arg0 = args.pop(0)
    pnglist = []
    while len(args) > 0 :
      arg = args.pop(0)
      try: # ignore non-PNG file args
        if arg.lower().index('.png') >= 0 :
          pnglist.append(arg)
      except: pass

  for png in pnglist :
    im=Image.open(png)
    im.show()
    pix=im.load()
    print >> FileKeyUtils.WMSlog, 'PILMemCache.viewPNGs> ', png, ', mode & size: ', im.mode, im.size, ', pix 0,0: ', pix[0,0]
# end viewPNG

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print _modinfo
  help("PILMemCache")
 
if __name__ ==  '__main__' :
  """
  Unit test main test memcached interfaces.
  """
  if len(sys.argv) > 1 :
    viewPNGs([])
    sys.exit(0)

# memcd = 'memcached -d -k -m 2048 -l 127.0.0.1 -p 11111'
# memcd = 'memcached -d -k -M -m 2048 -l 127.0.0.1 -p 11111'
# memcd = 'memcached-debug -vv -k -M -m 2048 -l 127.0.0.1 -p 11111'
# os.system(memcd)
# mcserver = {'IP':'127.0.0.1', 'port':11111}
  mcserver = dict(IP=_mcached['IP'], port=_mcached['port'][1])
#
# testPILPut(mcserver)
# time.sleep(0.5) # do we need to allow some time to digest things?
  testPILGet(mcserver)
  testContents()
# end main
