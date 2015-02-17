#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/GeoImage.py $'
svnId = rcsId = '$Name$ $Id: GeoImage.py 24 2008-04-01 06:19:16Z hon $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
The GeoImage module provides functions for generating latlong
and polar map projection PIL/PNG Image 'tiles' from ESRI
and BMNG input data. The latlong (Cylindrical Equidistant) projections
are handle by the Mapnik module, and the polar (Sterographic)
projections are handled by Matplotlib.basemap.

The polar tiles funcs. should return a PIL Image via matplotlib.basemap
The flat map 'latlon' tile func. should return a PIL Image via mapnik
The tile-name should be equiv. to the memcached key and/or the 
diskcache file-name prefix (filename extension should default to png)
Each func. should first attempt to find the tile in the memcached,
then the diskcache, and finally render it directly (and cache it for
future use).
"""
#
import os, sys
import matplotlib
# set backend to Agg.
matplotlib.use('Agg')
import pylab
from matplotlib.toolkits.basemap import Basemap, shiftgrid
#from pylab import show,arange,draw,figure,load,ravel,cm,axes,\
#                  colorbar,title,gca,pi,meshgrid
#import matplotlib.colors as colors
from matplotlib.image import pil_to_array
import mapnik 
from PIL import Image
from vipsCC import *
#
#import G3WMS.PILMemCache as PILMemCache
import PILMemCache
#import G3WMS.GeoProj as GeoProj
import GeoProj
#import G3WMS.FileKeyUtils as FileKeyUtils
import FileKeyUtils
#import G3WMS.ProcUtils as ProcUtils
import ProcUtils
import Raster

##################################3################# module globals:  
_bmngres = 'BMNG8km'
_freeforall = False

_mcdlatlon = dict(IP=PILMemCache._mcached['IP'], port=PILMemCache._mcached['port'][0])
_mcdnorth = dict(IP=PILMemCache._mcached['IP'], port=PILMemCache._mcached['port'][1])
_mcdsouth = dict(IP=PILMemCache._mcached['IP'], port=PILMemCache._mcached['port'][2])

def usage():
  """
  (depracted) Help printout for unit test main (GeoImage.py -h)
  """
  print >> FileKeyUtils.WMSlog, 'GeoImage.(unit test) usage: GeoImage.py -h => print >> FileKeyUtils.WMSlog, this help'
  print >> FileKeyUtils.WMSlog, 'GeoImage.(unit test) usage: GeoImage.py -anchor [lat_0 lon_0 bbox[0] bbox[1] bbox[2] bbox[3]]'
  print >> FileKeyUtils.WMSlog, 'GeoImage.(unit test) usage: -anchor allowed vals: -c -sw -s -se -e -ne -n -nw -w'
  print >> FileKeyUtils.WMSlog, 'GeoImage.-anchor is required! and according to the basemap help:'
  print >> FileKeyUtils.WMSlog, 'GeoImage.anchor - determines how map is placed in axes rectangle (passed to'
  print >> FileKeyUtils.WMSlog, 'GeoImage.axes.set_aspect). Default is "C", which means map is centered.'
  print >> FileKeyUtils.WMSlog, 'GeoImage.lat_0 - central latitude (y-axis origin) - used by all projections,'
  print >> FileKeyUtils.WMSlog, 'GeoImage.lon_0 - central meridian (x-axis origin) - used by all projections,'
  print >> FileKeyUtils.WMSlog, 'GeoImage.pole-centered projections (npstere,spstere,nplaea,splaea,npaeqd,spaeqd)'
  print >> FileKeyUtils.WMSlog, 'GeoImage.result in square regions centered on the north or south pole.'
  print >> FileKeyUtils.WMSlog, 'GeoImage.longitude lon_0 is at 6-o\'clock, and latitude lat_0 is tangent to the'
  print >> FileKeyUtils.WMSlog, 'GeoImage.edge of the map at lon_0.'
#end usage
 
def latlonCached(layerlist, alpha, size, bbox):
  """
  Returns latlon projection tile image found in cache(s). The args. are used to construct
  a hash dict. key which is first used to search the process in-memory image list, then
  the memcached images. If neither memory cache contans the desired image, then the key
  string is evaluated for a PNG path-file name that is sought in the disk cache. If no
  cached image is found, the 'None' object is returned.
  """
# chek for img in memcached, then diskcache:
  global _mcdlatlon

  mcserver = _mcdlatlon # memcached for latlon tiles
# file = FileKeyUtils.tileNameFullPath('latlon', layerlist, alpha, size, bbox, None)
  file = FileKeyUtils.tilePNGPath('latlon', layerlist, alpha, size, bbox, None)
  ikey = FileKeyUtils.tileNameInfoKey('latlon', layerlist, size, bbox, None) # origin not needed by mapnik api
  dkey = PILMemCache.dataKeyFromInfoKey(ikey)
  imgkeys = dict(info=ikey, data=dkey)

  print >> FileKeyUtils.WMSlog, 'GeoImage.latlonCached> keys: ', imgkeys,', server: ', mcserver
  img = PILMemCache.memcacheGetPIL(imgkeys, mcserver)
  if not(img == None):
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonCached> img returned from memcached: ', img.mode, img.size
    return img

  print >> FileKeyUtils.WMSlog, 'GeoImage.latlonCached> img NOT returned from memcached, try disk cache: ', file
  try:
    img = Image.open(file)
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonCached> img found in disk cache, file: ', file
    return img
  except:
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonCached> img NOT found in disk cache, file: ', file
#   pass
  return None

#def polarCenteredCached(projname, layerlist, alpha, size, centerLon, boundLat):
def polarCenteredCached(projname, layerlist, alpha, size, bbox):
  """
  Returns polar projection tile image found in cache(s). The args. are used to construct
  a hash dict. key which is first used to search the process in-memory image list, then
  the memcached images. If neither memory cache contans the desired image, then the key
  string is evaluated for a PNG path-file name that is sought in the disk cache. If no
  cached image is found, the 'None' object is returned.
  """
# chek for img in memcached, then diskcache:
  global _mcdnorth
  global _mcdsouth
  layername = ""
  for layer in layerlist:
    layername += layer 

# layername should indicate north or south pole; otherwise check boundLat for +/-
# nprojname = 'nplaea' # or 'npaeqd' 
# nprojname = 'npeqd' # or 'nplaea'
# sprojname = 'splaea' # or 'spaeqd' 
# sprojname = 'speqd' # or 'splaea'
# projname = nprojname ; mcd = _mcdnorth # memcached for northpolar tiles
  mcserver = _mcdnorth # default to north?
  try:
    indxpos = projname.lower().index('sp') 
    if indxpos >= 0:
      mcserver = _mcdsouth # memcached for southpolar tiles
  except: pass

  origin = 'C'
  centerLon = bbox[0] ; boundLat = bbox[1] # the bbox only needs these two values, ignore others
# file = FileKeyUtils.tileNameFullPath(projname, layerlist, alpha, size, [centerLon, boundLat], origin)
  file = FileKeyUtils.tilePNGPath(projname, layerlist, alpha, size, [centerLon, boundLat], origin)
  ikey = FileKeyUtils.tileNameInfoKey(projname, layerlist, size, [centerLon, boundLat], origin)
  dkey = PILMemCache.dataKeyFromInfoKey(ikey)
  imgkeys = dict(info=ikey, data=dkey)

  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredCached> keys: ', imgkeys,', server: ', mcserver
  img = PILMemCache.memcacheGetPIL(imgkeys, mcserver)
  if not(img == None):
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredCached> img returned from memcached: ', img.mode, img.size
    return img

  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredCached> img NOT returned from memcached, try disk cache: ', file
  try:
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredCached> file: ', file
    img = Image.open(file)
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredCached> img found in disk cache, file: ', file
    return img
  except: pass

  return None

def polarCenteredRasterPIL(projname, layerlist, alpha, size, centerLon, boundLat):
  """
  Returns a polar projection tile (PIL) Image centered at the pole ('n' north or 's' south
  should be indicated in the first characer of the projection name arg). The args. are
  used to construct a hash dict. key and a PNG full-path-file name that are used to
  store the tile image in the memory and disk caches for future use. Currently this only
  supports the BMNG 8 or 2km datasets. Matplotlib.basemap and pylab module objects and
  functions are used in conjunction with PIL. 
  """
# avoid matplotlib.basemap toolkit whitespace issues by always specifying
# a square image projection, then resize it to the wms requestes size:
  square = [512,512]
  if size[0] > size[1]:
    square = [size[0], size[0]]
  else:
    square = [size[1], size[1]]

  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> size: ', size, ', square: ', square
  origin = 'C'
  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath(projname, layerlist, alpha, size, [centerLon, boundLat], origin)
# use raster datasource file (like BMNG PNG or JPG or HDF):
# read the raster data source and warp it (only bmng pngs for now)...
  rasterfile = FileKeyUtils.rasterNameFullPath(layerlist, _bmngres)
  if rasterfile == None:
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> unable to determine raster input file from layerlist...'
    return None

# sanity check -- raster files are not named '*.shp'!0
  if isinstance(layerlist,str):
    layername = layerlist
  else:
    layername = layerlist[0]

  try:
    if layername.upper().index('BMNG'):
      if rasterfile.index('.shp'):
        print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> HUH?', layername, rasterfile
        return None 
  except: pass

# check for buffered images 2km, or 8km res.
  pilImage = Raster.buffered2kmBMNGPImg(rasterfile)
  if pilImage == None:
    pilImage = Raster.buffered8kmBMNGPImg(rasterfile)
  if pilImage == None:
    try:
      pilImage = Image.open(rasterfile)
    except:
      print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> unable to open raster input file: ', rasterfile
      return None

  rgba = pil_to_array(pilImage)
  rgba = rgba.astype(pylab.float32)/255. # convert to normalized floats.
# define lat/lon grid that BMNG image spans (projection='cyl').
  nlons = rgba.shape[1]; nlats = rgba.shape[0]
  delta = 360./float(nlons)
  lons = pylab.arange(-180.+0.5*delta,180.,delta)
  lats = pylab.arange(-90.+0.5*delta,90.,delta)
# create new figure
  GeoProj.setRcParms(square[0], square[1])
  fig = pylab.figure()
# need to eval. which polar proj. takes the least amount of time?
# setup lambert azimuthal map projection (Northern Hemisphere).
# m = Basemap(llcrnrlon=-150.,llcrnrlat=-18.,urcrnrlon=30.,urcrnrlat=--18.,\
#             resolution='c',area_thresh=10000.,projection='laea',\
#             lat_0=90.,lon_0=-105.)
# this is equivalent, but simpler.
# setup azimuthal equidistant map projection (Northern Hemisphere).
# m = Basemap(llcrnrlon=-150.,llcrnrlat=40.,urcrnrlon=30.,urcrnrlat=40.,\
#             resolution='c',area_thresh=10000.,projection='aeqd',\
#             lat_0=90.,lon_0=-105.)
# this is equivalent, but simpler.
  m = Basemap(projection=projname, lon_0=centerLon, boundinglat=boundLat, resolution=None, area_thresh=10000.)
# transform to nx x ny regularly spaced native projection grid
# nx and ny chosen to have roughly the same horizontal res as original image.
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> m.xmin= ',m.xmin,', m.ymin= ',m.ymin,', m.xmax= ',m.xmax,', m.ymax= ',m.ymax
  dx = 2.*pylab.pi*m.rmajor/float(nlons)
  nx = int((m.xmax-m.xmin)/dx)+1; ny = int((m.ymax-m.ymin)/dx)+1
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> nlons= ',nlons,', nlats= ',nlats,', nx= ',nx,', ny= ',ny
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> expect ny == nx for w=h tile ...'
  if not nx == ny :
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> tile image will be clipped with whitespace.'
  rgba_warped = pylab.zeros((ny,nx,4),pylab.float64)
# interpolate rgba values from proj='cyl' (geographic coords) to 'lcc'
  for k in range(4):
    rgba_warped[:,:,k] = m.transform_scalar(rgba[:,:,k],lons,lats,nx,ny)
# render warped rgba image.
  im = m.imshow(rgba_warped)
# draw parallels and meridians.
# parallels = pylab.arange(0.,80,20.)
# m.drawparallels(parallels,color='0.5')
# meridians = pylab.arange(0.,360.,20.)
# m.drawmeridians(meridians,color='0.5')
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> save png: ', outfile
  fig.savefig(outfile) # overwrite below with properly (re)sized image
  sqimg = Image.open(outfile)
  img = sqimg.resize(size)
# if not(img.mode == 'RGBA') : img.putalpha(alpha)
  img.putalpha(alpha) # ensure ouput tile is 'rgba' png
  img.save(outfile, 'png')
# pix=img.load()
# print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterPIL> ',png, ' : ', img.size, pix[0,0], pix[size[0]-1, size[1]-1]
  return img
#
#end polarCenteredRasterPIL

def polarCenteredRasterVIPS(projname, layerlist, alpha, size, centerLon, boundLat):
  """
  Returns a polar projection tile (PIL) Image centered at the pole ('n' north or 's' south
  should be indicated in the first characer of the projection name arg). The args. are
  used to construct a hash dict. key and a PNG full-path-file name that are used to
  store the tile image in the memory and disk caches for future use. Currently this only
  supports the BMNG 8 or 2km datasets. Matplotlib.basemap and pylab module objects and
  functions are used in conjunction with PIL. 
  Note that this is untested and unlikely to work due to the fact that there is no built-in
  'vips_to_array' function in matplotlib.basemap!
  """
# avoid matplotlib.basemap toolkit whitespace issues by always specifying
# a square image projection, then resize it to the wms requestes size:
  square = [512,512]
  if size[0] > size[1]:
    square = [size[0], size[0]]
  else:
    square = [size[1], size[1]]

  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> size: ', size, ', square: ', square
# if isinstance(layerlist, str)
#   layer = layerlist
# else:
#   layer = layerlist[0]
  origin = 'C'
  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath(projname, layerlist, alpha, size, [centerLon, boundLat], origin)
# use raster datasource file (like BMNG PNG or JPG or HDF):
# read the raster data source and warp it (only bmng pngs for now)...
  rasterfile = FileKeyUtils.rasterNameFullPath(layerlist, _bmngres)
  if rasterfile == None:
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> unable to determine raster input file from layerlist...'
    return None

# check for buffered images 2km, or 8km res.
  vipsImage = Raster.buffered2kmBMNGVImg(rasterfile)
  if vipsImage == None:
    vipsImage = Raster.buffered8kmBMNGVImg(rasterfile)
  if vipsImage == None:
    try:
      vipsImage = VImage.VImage(rasterfile)
    except:
      print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> unable to open raster input file: ', rasterfile
      return None

# rgba = pil_to_array(pilImage)
  rgba = vipsImage.data() # VIPS TIFF input should be an rgba-like object, but this may not suffice
  rgba = rgba.astype(pylab.float32)/255. # convert to normalized floats.
# define lat/lon grid that BMNG image spans (projection='cyl').
  nlons = rgba.shape[1]; nlats = rgba.shape[0]
  delta = 360./float(nlons)
  lons = pylab.arange(-180.+0.5*delta,180.,delta)
  lats = pylab.arange(-90.+0.5*delta,90.,delta)
# create new figure
  GeoProj.setRcParms(square[0], square[1])
  fig = pylab.figure()
# need to eval. which polar proj. takes the least amount of time?
# setup lambert azimuthal map projection (Northern Hemisphere).
# m = Basemap(llcrnrlon=-150.,llcrnrlat=-18.,urcrnrlon=30.,urcrnrlat=--18.,\
#             resolution='c',area_thresh=10000.,projection='laea',\
#             lat_0=90.,lon_0=-105.)
# this is equivalent, but simpler.
# setup azimuthal equidistant map projection (Northern Hemisphere).
# m = Basemap(llcrnrlon=-150.,llcrnrlat=40.,urcrnrlon=30.,urcrnrlat=40.,\
#             resolution='c',area_thresh=10000.,projection='aeqd',\
#             lat_0=90.,lon_0=-105.)
# this is equivalent, but simpler.
  m = Basemap(projection=projname, lon_0=centerLon, boundinglat=boundLat, resolution=None, area_thresh=10000.)
# transform to nx x ny regularly spaced native projection grid
# nx and ny chosen to have roughly the same horizontal res as original image.
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> m.xmin= ',m.xmin,', m.ymin= ',m.ymin,', m.xmax= ',m.xmax,', m.ymax= ',m.ymax
  dx = 2.*pylab.pi*m.rmajor/float(nlons)
  nx = int((m.xmax-m.xmin)/dx)+1; ny = int((m.ymax-m.ymin)/dx)+1
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> nlons= ',nlons,', nlats= ',nlats,', nx= ',nx,', ny= ',ny
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> expect ny == nx for w=h tile ...'
  if not nx == ny :
    print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> tile image will be clipped with whitespace.'
  rgba_warped = pylab.zeros((ny,nx,4),pylab.float64)
# interpolate rgba values from proj='cyl' (geographic coords) to 'lcc'
  for k in range(4):
    rgba_warped[:,:,k] = m.transform_scalar(rgba[:,:,k],lons,lats,nx,ny)
# render warped rgba image.
  im = m.imshow(rgba_warped)
# draw parallels and meridians.
# parallels = pylab.arange(0.,80,20.)
# m.drawparallels(parallels,color='0.5')
# meridians = pylab.arange(0.,360.,20.)
# m.drawmeridians(meridians,color='0.5')
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> save png: ', outfile
  fig.savefig(outfile) # overwrite below with properly (re)sized image
  sqimg = Image.open(outfile)
  img = sqimg.resize(size)
# if not(img.mode == 'RGBA') : img.putalpha(alpha)
  img.putalpha(alpha) # force max. opacity and allow client to scale it
  img.save(outfile, 'png') # ensure ouput tile is 'rgba' png
# pix=img.load()
# print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredRasterVIPS> ',png, ' : ', img.size, pix[0,0], pix[size[0]-1, size[1]-1]
  return img
#
#end polarCenteredRasterVIPS

def polarCenteredESRI(projname, layerlist, alpha, size, centerLon, boundLat):
  """
  Returns a polar projection tile (PIL) Image centered at the pole ('n' north or 's' south
  should be indicated in the first characer of the projection name arg). The args. are
  used to construct a hash dict. key and a PNG full-path-file name that are used to
  store the tile image in the memory and disk caches for future use. This supports any
  proper ESRI shapefile dataset(s) input. Matplotlib.basemap and pylab module objects and
  functions are used in conjunction with PIL. 
  """
# avoid matplotlib.basemap toolkit whitespace issues by always specifying
# a square image projection, then resize it to the wms requestes size:
  square = [512,512]
  if size[0] > size[1]:
    square = [size[0], size[0]]
  else:
    square = [size[1], size[1]]

  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredESRI> size: ', size, ', square: ', square
  origin = 'C'
  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath(projname, layerlist, alpha, size, [centerLon, boundLat], origin)
# use Matplotlib.basemep projection and (VMAP0/1 and more) ESRI shapefile datastore
# use the GeoProj func:
  GeoProj.setRcParms(square[0], square[1])
# create new figure
  fig = pylab.figure()
# and map
  m = Basemap(projection=projname, lon_0=centerLon, boundinglat=boundLat, resolution=None, area_thresh=10000.)
  shp_info = {}
  for layername in layerlist:
# construct filepathandname from layername
    shpfile = FileKeyUtils.DataStore + layername # world political boumndary layer
    try:
      if layername.index('US') >= 0:
         shpfile = FileKeyUtils.USAStore + layername # US state or county layer
    except: pass
    vmap0 = GeoProj.vmap0Layer(layername) # or vmap0 layer
    if len(vmap0) <= 0: # not a VMAP0 layer/shapefile name 
      shp_info[layername] = m.readshapefile(shpfile, layername, drawbounds=True)
      print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredESRI> read shpfile: ', shp_info[layername]
    for v0 in vmap0: # continental reagion subdirectories...
      shpfile = FileKeyUtils.VMAP0Store + v0 # under GIS/VMAP0/etc. subdirectories
      shp_info[layername] = m.readshapefile(shpfile, layername, drawbounds=True)
      print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredESRI> read shpfile: ', shp_info[layername]
#
# no m.imshow(...)?
#
  print >> FileKeyUtils.WMSlog, 'GeoImage.polarCenteredESRI> save png: ', outfile
  fig.savefig(outfile)
  sqimg = Image.open(outfile)
  img = sqimg.resize(size)
  if not( img.mode == 'RGBA' ) >= 0 : img.putalpha(alpha)
  img.putalpha(alpha) # ensure ouput tile is 'rgba' png
  img.save(outfile, 'png')
# pix=img.load()
# print >> FileKeyUtils.WMSlog, 'GeoImage.polarTile> ',png, ' : ', img.size, pix[0,0], pix[size[0]-1, size[1]-1]
  return img
#end polarCenteredESRI

def latlonMapnik(layerlist, alpha, size, bbox):
  """
  Returns an Cylindrical Equidistant 'latlon' projection tile (PIL) Image of specified arg.
  size = [width, height] pixels, with area defined by bbox = [min. lon, min lat, max lon., max lat.].
  The args. are also used to construct a hash dict. key and a PNG full-path-file name that are
  used to store the tile image in the memory and disk caches for future use. As indicated
  in the function name, this relies on the Mapnik module classes and functions along with PIL.
  It supports any proper ESRI shapefile dataset(s) input, but does not currently support raster
  (PNG) input (i.e. no BMNG data). 
  """
  opaqBlack = mapnik.Color(0, 0, 0, 255)
  transBlack = mapnik.Color(0, 0, 0, alpha)
  opaqWhite = mapnik.Color(255, 255, 255, 255)
  transWhite = mapnik.Color(255, 255, 255, alpha)
  opaqRed = mapnik.Color(255, 0, 0, 255)
  transRed = mapnik.Color(255, 0, 0, alpha)
  opaqGreen = mapnik.Color(0, 255, 0, 255)
  transGreen = mapnik.Color(0, 255, 0, alpha)
  opaqBlue = mapnik.Color(0, 0, 255, 255)
  transBlue = mapnik.Color(0, 0, 255, alpha)

  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath('latlon', layerlist, alpha, size, bbox, None)
# use Mapnik default projection and VMAP0 ESRI shapefile datastore
  m = mapnik.Map(size[0], size[1], "+proj=latlong +datum=WGS84")
# background color.
# can use 'named' colours, #rrggbb, #rgb or rgb(r%,g%,b%) format
# m.background = mapnik.Color('steelblue')
  m.background = transWhite
  m.foreground = transBlack

# create a style and add it to the Map.
  s = mapnik.Style()
# a Style can have one or more rules
# a rule consists of a filter, min/max scale demoninators and 1..N Symbolizers.
# if you don't specify filter and scale denominators you get default values :
# Filter =  'ALL' filter (meaning symbolizer(s) will be applied to all features)
# MinScaleDenominator = 0
# MaxScaleDenominator = INF
# keep things simple and use default value, but to create a map we
# must provide at least one Symbolizer. fill countries polygons with
# greyish colour and draw outlines with a bit darker stroke.
  r = mapnik.Rule()
  polyfill = mapnik.PolygonSymbolizer(transBlack)
# r.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color('#f2eff9')))
  r.symbols.append(polyfill)
  linecolor= mapnik.LineSymbolizer(opaqWhite, 0.5)
# r.symbols.append(mapnik.LineSymbolizer(mapnik.Color('rgb(50%,50%,50%)'),0.5))
  r.symbols.append(linecolor)
  s.rules.append(r)

# add our style to the Map, giving it a name.
  m.append_style('MapnikStyle', s)

  for layername in layerlist:
# construct filepathandname from layername
    shpfile = FileKeyUtils.DataStore + layername # world political boumndary layer
    try:
      if layername.index('US') >= 0:
         shpfile = FileKeyUtils.USAStore + layername # US state or county layer
    except: pass
    layer = mapnik.Layer(layername)
    vmap0 = GeoProj.vmap0Layer(layername)
    if len(vmap0) <= 0: # not vmap...
      print >> FileKeyUtils.WMSlog, 'GeoImage.latlongMapnik> layername, shapefile:', layername, shpfile
      layer.datasource = mapnik.Shapefile(file=shpfile)
      layer.styles.append('MapnikStyle')
      m.layers.append(layer)
    for v0 in vmap0: # handle vmap0 continental region subdirectories
      shpfile = FileKeyUtils.VMAP0Store + v0 # under GIS/VMAP0/etc. subdirectories
      print >> FileKeyUtils.WMSlog, 'GeoImage.latlongMapnik> layername, shapefile:', layername, shpfile
      layer.datasource = mapnik.Shapefile(file=shpfile)
      layer.styles.append('MapnikStyle')
      m.layers.append(layer)
# end layerlist
  envbox = mapnik.Envelope(bbox[0], bbox[1], bbox[2], bbox[3])
  m.zoom_to_box(envbox)
# cache it to disk (old style):
# mapnik.render_to_file(m, outfile, 'png')
# img = Image.open(outfile)
# pix=img.load(); size = img.size
# print >> FileKeyUtils.WMSlog, 'GeoImage.latlongMapnik> ', outfile, ' : ', size, pix[0,0], pix[size[0]-1, size[1]-1]
# new style as of mapnik 0.5.0:
  mimg = mapnik.Image(m.width,m.height)
  mapnik.render(m, mimg)
# save image to rgba png file
  mimg.save(outfile, 'png') # true-colour RGBA
  print >> FileKeyUtils.WMSlog, 'GeoImage.latlongMapnik> ', outfile
  img = Image.open(outfile) # evidently mapnik.Image is not a PIL Image -- bummer!
  img.putalpha(alpha) # ensure ouput tile is 'rgba' png
  return img
#end latlongMapnik

def latlonRasterPIL(layerlist, alpha, size, bbox):
  """
  Returns an Cylindrical Equidistant 'latlon' projection tile (PIL) Image of specified arg.
  size = [width, height] pixels, with area defined by bbox = [min. lon, min lat, max lon., max lat.].
  The args. are also used to construct a hash dict. key and a PNG full-path-file name that are
  used to store the tile image in the memory and disk caches for future use. This function relies
  exclusively on PIL (Python Image Library) classes and functions and currently only supports raster
  (PNG or TIFF) input (i.e. only BMNG data). 
  """

  inImage = None
  print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterPIL> input: ', rasterfile
# check for buffered images 2km, or 8km res.
  if Raster.use500m(bbox, size):
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterPIL> test 500m BMNG later...'

# use raster datasource file (like BMNG PNG or TIFF or JPG or HDF):
# read the raster data source and extract tile (only bmng pngs for now)...
  bmngres = Raster.chooseRes(bbox, size)
  rasterfile = FileKeyUtils.rasterNameFullPath(layerlist, bmngres)
  if rasterfile == None:
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterPIL> unable to determine raster input file from layerlist...'
    return None

  inImage = Raster.bufferedBMNGPImg(rasterfile, bmngres)
  if inImage == None:
    try:
      inImage = Image.open(rasterfile)
    except:
      print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterPIL> unable to open raster input file: ', rasterfile
      return None

  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath('latlon', layerlist, alpha, size, bbox, None)
  cropimg = Raster.extractPIL(inImage, bmngres, bbox)
  if cropimg == None: # exception/error in extractio/crop 
    return None 
  outimg = cropimg.resize(size)
  if outimg != cropimg: del cropimg
# if not( outimg.mode == 'RGBA' ) : outimg.putalpha(alpha)
  outimg.putalpha(alpha) # ensure ouput tile is 'rgba' png
  outimg.save(outfile, 'png')
  return outimg
#end latlonRasterPIL

def latlonRasterVIPS(layerlist, alpha, size, bbox):
  """
  Returns an Cylindrical Equidistant 'latlon' projection tile (PIL) Image of specified arg.
  size = [width, height] pixels, with area defined by bbox = [min. lon, min lat, max lon., max lat.].
  The args. are also used to construct a hash dict. key and a PNG full-path-file name that are
  used to store the tile image in the memory and disk caches for future use. This function relies
  on both VIPS and PIL (Python Image Library) classes and functions and currently only supports raster
  (PNG or TIFF) input (i.e. only BMNG data). 
  """
  global _freeforall
  inImage = None ; 
# check for buffered images 2km, or 8km res.
# if Raster.use500m(bbox, size):
#   print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> test 500m BMNG later...'
#   return None

# use raster datasource file (like BMNG PNG or TIFF or JPG or HDF):
# read the raster data source and extract tile (only bmng pngs for now)...
  bmngres = Raster.chooseRes(bbox, size)
  if bmngres == 'BMNG500m':
    bmngres = 'BMNG2km' # restrict system to 8 or 2 km for now (500m code not yet ready for prime time)
  rasterfile = FileKeyUtils.rasterNameFullPath(layerlist, bmngres)
  if rasterfile == None:
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> unable to determine raster input file from layerlist...'
    return None

  print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> check buffered input bmngres:', bmngres,', rasterfile:', rasterfile
  inImage = Raster.bufferedBMNGVImg(rasterfile, bmngres)
  if inImage == None:
    print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> not buffered?, open rasterfile:', rasterfile
    try:
      inImage = VImage.VImage(rasterfile)
      _freeforall = True # since we are not using pre-buffered in-ram Vimages, be sure to free this
    except:
      print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> unable to open raster input file: ', rasterfile
      return None
 
  cropvim = Raster.extractVIPS(inImage, bmngres, bbox)
  if cropvim == None: # exception/error in extractio/crop 
    return None 

  vtile = Raster.resizeVImg(cropvim, size)
  alpha = 255 # force max. opacity and allow client to scale it
  outfile = FileKeyUtils.tilePNGPath('latlon', layerlist, alpha, size, bbox, None)
  vtile.write(outfile)
  print >> FileKeyUtils.WMSlog, 'GeoImage.latlonRasterVIPS> created scaled/resize:' ,size, outfile
  del vtile ;  del cropvim
  if _freeforall:
    del inImage
# retain PIL for final output
  ptile = Image.open(outfile)
  if not( ptile.mode == 'RGBA' ) : ptile.putalpha(alpha)
  ptile.putalpha(alpha) #  ensure tile is 'rgba' png
  ptile.save(outfile, 'png')
  return ptile
#end latlonRasterVIPS

def handleLatLon(layerlist, alpha, size, bbox):
  """
  Returns an Cylindrical Equidistant 'latlon' projection tile (PIL) Image of specified arg.
  size = [width, height] pixels, with area defined by bbox = [min. lon, min lat, max lon., max lat.].
  First check caches, and if needed, makes use of latlonRaster() or latlonMapnik() to
  create the first-time rendition of the Image tile. This is an entry point from a CGI app. or
  mod_python handler.
  """
# check for img in memcache, then diskcache, othewise create and cache it:
  img = latlonCached(layerlist, alpha, size, bbox)
  if not(img == None):
#   print >> FileKeyUtils.WMSlog, 'GeoImage.handleLatLon> found in neither disk nor memcd cache ', img.mode, img.size
    return img

# try raster (BMNG?)
# img = latlonRasterPIL(layerlist, alpha, size, bbox)
  img = latlonRasterVIPS(layerlist, alpha, size, bbox)
  if img == None: # assume shapefile layer list
    img = latlonMapnik(layerlist, alpha, size, bbox) # this sets disk cache

  if img == None: # quit
    return None

# cache it to memcached:
  global _mcdlatlon
# file = FileKeyUtils.tileNameFullPath('latlon', layerlist, alpha, size, bbox, None)
  file = FileKeyUtils.tilePNGPath('latlon', layerlist, alpha, size, bbox, None)
  ikey = FileKeyUtils.tileNameInfoKey('latlon', layerlist, size, bbox, None) # origin not needed by mapnik api
  dkey = PILMemCache.dataKeyFromInfoKey(ikey)
  imgkeys = dict(info=ikey, data=dkey)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleLatLon> caching initial rendition, file: ', file, ', imgkeys: ', imgkeys
  PILMemCache.memcachePutPIL(img, imgkeys, _mcdlatlon)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleLatLon> fully cached:', img.mode, img.size
  return img
#end handleLatLon

#def handleNorthPolarCentered(layerlist, alpha, size, centerLon, boundLat):
def handleNorthPolarCentered(layerlist, alpha, size, bbox):
  """
  Returns an North polar projection tile (PIL) Image of specified arg. size = [width, height] pixels,
  with area defined by bbox = [center lon, bounding lat]. First check caches, and if needed,
  makes use of polarCenteredRaster() or  polarCenteredESRI() to create the first-time
  rendition of the Image tile. This is an entry point from a CGI app. or mod_python handler.
  """
  global _mcdnorth
  global _bmngres
# projname should indicate north or south pole; otherwise check boundLat for +/-
  nprojname = GeoProj.NorthPolarProjlist[0] # 'npstere' or 'nplaea' or 'npaeqd'
# _bmngres = Raster.chooseRes(bbox, size) # polar uses default 8km res.
  centerLon = bbox[0] ; boundLat = bbox[1] # the bbox only needs these two values, ignore others
# img = polarCenteredCached(nprojname, layerlist, alpha, size, centerLon, boundLat)
  img = polarCenteredCached(nprojname, layerlist, alpha, size, bbox)
  if not(img == None):
    print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> ', nprojname, ' found in either disk or memcd cache ', img.mode, img.size
    return img

# try raster (BMNG?)
  img = polarCenteredRasterPIL(nprojname, layerlist, alpha, size, centerLon, boundLat)
  if not(img == None):
    print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> ', nprojname, ' created and cached img  ', img.mode, img.size
    return img

# sanity check
  if isinstance(layerlist,str):
    layername = layerlist
  else:
    layername = layerlist[0]

  print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> layername :',layername
  try:
    if layername.upper().index('BMNG'):
      print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> HUH? BMNG tif/png filename error?', layername
      return None
  except: pass

  img = polarCenteredESRI(nprojname, layerlist, alpha, size, centerLon, boundLat)
  if img == None: # quit
    return None

  origin = 'C'
# file = FileKeyUtils.tileNameFullPath(nprojname, layerlist, alpha, size, [centerLon, boundLat], origin)
  file = FileKeyUtils.tilePNGPath(nprojname, layerlist, alpha, size, [centerLon, boundLat], origin)
  ikey = FileKeyUtils.tileNameInfoKey(nprojname, layerlist, size, [centerLon, boundLat], origin) # origin not needed by mapnik api
  dkey = PILMemCache.dataKeyFromInfoKey(ikey)
  imgkeys = dict(info=ikey, data=dkey)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> caching initial rendition, file: ', file, ', imgkeys: ', imgkeys
  PILMemCache.memcachePutPIL(img, imgkeys, _mcdnorth)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> ', nprojname, ' fully cached: ', img.mode, img.size
  return img
#end handleNorthPolarCentered 

#def handleSouthPolarCentered(layerlist, alpha, size, centerLon, boundLat):
def handleSouthPolarCentered(layerlist, alpha, size, bbox):
  """
  Returns an South polar projection tile (PIL) Image of specified arg. size = [width, height] pixels,
  with area defined by bbox = [center lon, bounding lat]. First check caches, and if
  needed, makes use of polarCenteredRaster() or  polarCenteredESRI() to create the first-time
  rendition of the Image tile. This is an entry point from a CGI app. or mod_python handler.
  """
  global _mcdsouth
  global _bmngres
# _bmngres = Raster.chooseRes(bbox, size)
  centerLon = bbox[0] ; boundLat = bbox[1] # the bbox only needs these two values, ignore others
# projname should indicate north or south pole; otherwise check boundLat for +/-
  sprojname = GeoProj.SouthPolarProjlist[0] # 'spstere' or 'splaea' or 'spaeqd'
# img = polarCenteredCached(sprojname, layerlist, alpha, size, centerLon, boundLat)
  img = polarCenteredCached(sprojname, layerlist, alpha, size, bbox)
  if not(img == None):
    print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> ', sprojname, ' found in cache ', img.mode, img.size
    return img

# try raster (BMNG?)
  img = polarCenteredRasterPIL(sprojname, layerlist, alpha, size, centerLon, boundLat)
  if not( img == None ):
    return img

# sanity check
  if isinstance(layerlist,str):
    layername = layerlist
  else:
    layername = layerlist[0]

  try:
    if layername.upper().index('BMNG'):
      print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> HUH? BMNG tif/png filename error?', layername
      return None
  except: pass

  img = polarCenteredESRI(sprojname, layerlist, alpha, size, centerLon, boundLat)
  if img == None: # quit
    return None

  origin = 'C'
# file = FileKeyUtils.tileNameFullPath(sprojname, layerlist, alpha, size, [centerLon, boundLat], origin)
  file = FileKeyUtils.tilePNGPath(sprojname, layerlist, alpha, size, [centerLon, boundLat], origin)
  ikey = FileKeyUtils.tileNameInfoKey(sprojname, layerlist, size, [centerLon, boundLat], origin) # origin not needed by mapnik api
  dkey = PILMemCache.dataKeyFromInfoKey(ikey)
  imgkeys = dict(info=ikey, data=dkey)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleSouthPolarCentered> caching initial rendition, file: ', file, ', imgkeys: ', imgkeys
  PILMemCache.memcachePutPIL(img, imgkeys, _mcdsouth)
  print >> FileKeyUtils.WMSlog, 'GeoImage.handleNorthPolarCentered> ', sprojname, ' fully cached: ', img.mode, img.size
  return img
#end handleNorthPolarCentered 

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print _modinfo
  help("GeoImage")

if __name__ ==  '__main__' :
  """
  Unit test main can be used to restart memcached(s) and/or test polar and latlon projection funcs.
  """
# preserve argv -- evidently some modules need it
  arg0 = sys.argv[0] # do not use sys.argv.pop(0)!

  FileKeyUtils.openWMSlog(logfile='/devstore/apache2/logs/WMSunittestGeoImage.log')
  projname = 'latlon'
  alpha = 255;
  size = [1024, 512] ; bbox = [-180.0, -90.0, 180.0, 90.0] 
  size = [512, 512] ; bbox = [-120.0, 20.0, -80.0, 60.0] 
# print >> FileKeyUtils.WMSlog, 'GeoImage.py> parms:', orign, cntrlatlon, bbox
# layerlist = ['USstate', 'UScounty', 'COASTL', 'HYDROTXT', 'INWATERA', 'OCEANSEA', 'POLBNDA'] #, 'ROADL']
# layerlist = ['USstate', 'COASTL', 'HYDROTXT', 'INWATERA', 'OCEANSEA', 'POLBNDA'] #, 'ROADL']
# layerlist = ['USstate', 'POLBNDA', 'INWATERA']
  layerlist = ['POLBNDA', 'INWATERA']
# layerlist = ['INWATERA', 'POLBNDA']
  if len(sys.argv) > 1:
   arg = sys.argv[1]
   if arg in ('-restart', '-kill', '-k'):
     ProcUtils.restartMemCached()
   if arg in ('-n', '-np'):
     projname = GeoProj.NorthPolarProjlist[0]
     print >> FileKeyUtils.WMSlog, 'GeoImage> ', arg0, ', projname: ', projname
     alpha = 255; size = [512, 512]
     cntrLon = -90.0; boundLat = 0.0
     img = handleNorthPolarCentered(layerlist, alpha, size, cntrLon, boundLat) # origin at center of image
     sys.exit(0)   
   if arg in ('-s', '-sp'):
     projname = GeoProj.SouthPolarProjlist[0]
     print >> FileKeyUtils.WMSlog, 'GeoImage> ', arg0, ', projname: ', projname
     alpha = 255; size = [512, 512]
     cntrLon = -90.0; boundLat = 0.0
     img = handleSouthPolarCentered(layerlist, alpha, size, cntrLon, boundLat) # origin at center of image
     sys.exit(0)   

# test default projection:
  print >> FileKeyUtils.WMSlog, 'GeoImage> ', arg0, ', default projname: ', projname
  img = handleLatLon(layerlist, alpha, size, bbox) 
  FileKeyUtils.mapPILToStdOut(img)
  FileKeyUtils.closeWMSlog()
#end main
