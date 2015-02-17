#!/bin/env python
import os, sys
from PIL import Image
from vipsCC import *

_winter500m = '/devstore/GIS/BMNG/world_500m/world.topo.bathy.200401.3x21600x21600.'
_summer500m = '/devstore/GIS/BMNG/world_500m/world.topo.bathy.200407.3x21600x21600.'
_winter2km = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.200401.3x21600x10800'
_summer2km = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.200407.3x21600x10800'

_BMNG500m = ['A1','A2','B1','B2', 'C1','C2','D1','D2']
_BMNG12month = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

def printSysMemInfo():
  pagesz = os.sysconf('SC_PAGESIZE')/1024.0
  numpages = os.sysconf('SC_PHYS_PAGES')/1024.0
  freepages = os.sysconf('SC_AVPHYS_PAGES')/1024.0
# print 'page size (kb):', pagesz , ', total pages (mb):', numpages,', available pages:', freepages
  totalmbsz = numpages * pagesz
  totalmbfree = pagesz * freepages
  totalmbused = totalmbsz - totalmbfree
  print 'total mb:',totalmbsz ,', total mb used:', totalmbused, ', total free mb:', totalmbfree

def printVImgInfo(vim):
  print  vim.filename()
  print 'xsize,res, ysize,res:', vim.Xsize(), vim.Xres(), vim.Ysize(), vim.Yres()
  print 'bands:', vim.Bands(), vim.BandFmt(), ', length: ', vim.Length()
  print 'encoding, type:', vim.Coding(), vim.Type(), ', compression:', vim.Compression()
  print 'xyoffset:', vim.Xoffset(), vim.Yoffset()

def printPImgInfo(pim):
  print pim.mode, pim.size, pim.format

def vipsPng2Tiff500m(pathfileprefix, pnglist):
  print 'vipsPng2Tiff500m>', pnglist
  for im in pnglist:
    png = pathfileprefix + im + '.png'
    tif = pathfileprefix + im + '.tif'
    print png, ' to ', tif
    vim = VImage.VImage(png)
    printVImgInfo(vim)
    vim.write(tif)
    del vim
    vim = VImage.VImage(tif)
    printVImgInfo(vim)
    del vim

def vipsPng2Tiff2km(molist):
  print 'vipsPng2Tiff2km>', molist
  for mo in molist:
    png = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.2004'+mo+'.3x21600x10800.png'
    tif = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.2004'+mo+'.3x21600x10800.tif'
    vim = VImage.VImage(png)
#   print png, ' to ', tif
    printVImgInfo(vim)
    vim.write(tif)
    del vim
    vim = VImage.VImage(tif)
    printVImgInfo(vim)
    del vim

def vipsPng2Tiff8km(molist):
  print 'vipsPng2Tiff2km>', molist
  for mo in molist:
    png = '/devstore/GIS/BMNG/world_8km/world.topo.bathy.2004'+mo+'.3x5400x2700.png'
    tif = '/devstore/GIS/BMNG/world_8km/world.topo.bathy.2004'+mo+'.3x5400x2700.tif'
    vim = VImage.VImage(png)
#   print png, ' to ', tif
    printVImgInfo(vim)
    vim.write(tif)
    del vim
    vim = VImage.VImage(tif)
    printVImgInfo(vim)
    del vim

def pilPng2Tiff500m(pathfileprefix, pnglist):
  print 'pilPng2Tiff500m>', pnglist
  for im in pnglist:
    png = pathfileprefix + im + '.png'
    tif = pathfileprefix + im + '.tif'
    print png, ' to ', tif
    pim = Image.open(png)
    printPImgInfo(vim)
    pim.save(tif, 'tiff')
    del pim
    pim = Image.open(tif)
    printPImgInfo(vim)
    del pim

def pilPng2Tiff2km(monthlist):
  print 'pilPng2Tiff2km>', monthlist
  for mo in monthlist:
    png = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.2004'+mo+'.3x21600x10800.png'
    tif = '/devstore/GIS/BMNG/world_2km/world.topo.bathy.2004'+mo+'.3x21600x10800.tif'
    pim = Image.open(png)
    print png, ' to ', tif
    printPImgInfo(pim)
    pim.save(tif,'tiff')
    del pim
    pim = Image.open(tif)
    printPImgInfo(vim)
    del pim

def pilPng2Tiff8km(monthlist):
  print 'pilPng2Tiff8km>', monthlist
  for mo in monthlist:
    png = '/devstore/GIS/BMNG/world_8km/world.topo.bathy.2004'+mo+'.3x5400x2700.png'
    tif = '/devstore/GIS/BMNG/world_8km/world.topo.bathy.2004'+mo+'.3x5400x2700.tif'
    pim = Image.open(png)
    print png, ' to ', tif
    printPImgInfo(pim)
    pim.save(tif,'tiff')
    del pim
    pim = Image.open(tif)
    printPImgInfo(vim)
    del pim

def convPng2Tiff():
  print 'convPng2Tiff>...'
  global _BMNG500m
  global _BMNG12month
  global _winter500m
  global _summer500m
  global _winter2km
  global _summer2km
# pilPng2Tiff2km(_BMNG12month)
  vipsPng2Tiff8km(_BMNG12month)
# vipsPng2Tiff2km(['01', '07'])
# vipsPng2Tiff500m(_summer500m, _BMNG500m)
# vipsPng2Tiff500m(_winter500m, _BMNG500m)
  
def vipsExtract(file, bbox, size):
  print 'vipsExtract>', file
  vim = VImage.VImage(file)
  printSysMemInfo()
  xysize = [1024,1024]
  xyoffset = [vim.Xsize()/4, vim.Ysize()/4]
  print 'vipsExtract>', xyoffset, xysize
  im = vim.extract_area(xyoffset[0], xyoffset[1], xysize[0], xysize[1])
  printSysMemInfo()
  xscale = 1.0*size[0]/im.Xsize()
  yscale = 1.0*size[1]/im.Ysize()
  tile = im.affine(xscale, 0, 0, yscale, 0, 0, 0, 0, size[0], size[1])
  printSysMemInfo()
  outfile = 'tile.png'
  try:
    if file.index('.tif') >= 0:
      outfile = 'vipstif' + outfile
  except: pass
  try:
    if file.index('.png') >= 0:
      outfile = 'vipspng' + outfile
  except: pass
  
  print 'vipsExtract>', outfile
  tile.write(outfile)
  del vim ; del im ; del tile
  printSysMemInfo()

def pilExtract(file, bbox, size):
  print 'pilExtract>', file
  pim = Image.open(file)
  printSysMemInfo()
  xysize = [1024,1024]
  xyoffset = [pim.size[0]/4, pim.size[1]/4]
  crpbox = xyoffset + xysize
  print 'pilExtract>', crpbox
  im = pim.crop(crpbox)
  printSysMemInfo()
  tile = im.resize(size)
  printSysMemInfo()
  outfile = 'tile.png'
  try:
    if file.index('.tif') >= 0:
      outfile = 'piltif' + outfile
  except: pass
  try:
    if file.index('.png') >= 0:
      outfile = 'pilpng' + outfile
  except: pass
  
  print 'pilExtract>', outfile
  tile.save(outfile,'png')
  del pim ; del im ; del tile
  printSysMemInfo()


def testVips(png, tif, bbox, size):
  if len( sys.argv ) > 0:
    vipsExtract(png, bbox, size)
    printSysMemInfo()
    return

  vipsExtract(tif, bbox, size) 
  printSysMemInfo()
 
def testPIL(png, tif, bbox, size):
  if len( sys.argv ) > 0:
    pilExtract(png, bbox, size)
    printSysMemInfo()
    return

  pilExtract(tif, bbox, size) 
  printSysMemInfo()

if __name__ ==  '__main__' :
# printSysMemInfo()
  size = [256, 256]
  bbox = [0.0, 0.0 , 0.0, 0.0]
  png = _summer2km + '.png'
  tif = _summer2km + '.tif'
# vipspng2tif2km(png)
# png = _winter2km + '.png'
# vipspng2tif2km(png)

  arg0 = sys.argv.pop(0)
  try:
    if arg0.index('vips') >= 0:
      print '\nVIPS test BMNG 2km extraction of 1024x1024 and resize to 256x256 tile:', arg0
      testVips(png, tif, bbox, size)
      sys.exit(0)
  except: pass
  
  try:
    if arg0.index('pil') >= 0:
      print '\nPIL test BMNG 2km extraction of 1024x1024 and resize to 256x256 tile:', arg0
      testPIL(png, tif, bbox, size)
      sys.exit(0)
  except: pass

  try:
    if arg0.index('png2tif') >= 0:
      print 'convert PNG(s) to TIFF(s)...'
      convPng2Tiff()
      sys.exit(0)
  except: pass
