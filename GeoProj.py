#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/GeoProj.py $'
svnId = rcsId = '$Name$ $Id: GeoProj.py 24 2008-04-01 06:19:16Z hon $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
Module GeoProj prvides global lists and hash dicts. containing
projection and layer names and aliases supported by the OGCWMS. There
are also some convenience functions for accessing the layer names and
aliases.
"""
#
import os, sys
import matplotlib
# set backend to Agg.
#matplotlib.use('Agg')
#from matplotlib.toolkits.basemap import Basemap, shiftgrid
#from pylab import show,arange,draw,figure,load,ravel,cm,axes,\
#                  colorbar,title,gca,pi,meshgrid
#import matplotlib.colors as colors
import pylab
#import G3WMS.FileKeyUtils as FileKeyUtils
import FileKeyUtils

################################################### module funcs:
def usage():
  """
  (depracted) Help printout for unit test main (GeoProj.py -h)
  """
  print >> FileKeyUtils.WMSlog, '(unit test) usage: GeoProj.py -h => print >> FileKeyUtils.WMSlog, this help'
  print >> FileKeyUtils.WMSlog, '(unit test) usage: GeoProj.py -anchor [lat_0 lon_0 bbox[0] bbox[1] bbox[2] bbox[3]]'
  print >> FileKeyUtils.WMSlog, '(unit test) usage: -anchor allowed vals: -c -sw -s -se -e -ne -n -nw -w'
  print >> FileKeyUtils.WMSlog, '-anchor is required! and according to the basemap help:'
  print >> FileKeyUtils.WMSlog, 'anchor - determines how map is placed in axes rectangle (passed to'
  print >> FileKeyUtils.WMSlog, 'axes.set_aspect). Default is "C", which means map is centered.'
  print >> FileKeyUtils.WMSlog, 'lat_0 - central latitude (y-axis origin) - used by all projections,'
  print >> FileKeyUtils.WMSlog, 'lon_0 - central meridian (x-axis origin) - used by all projections,'
  print >> FileKeyUtils.WMSlog, 'pole-centered projections (npstere,spstere,nplaea,splaea,npaeqd,spaeqd)'
  print >> FileKeyUtils.WMSlog, 'result in square regions centered on the north or south pole.'
  print >> FileKeyUtils.WMSlog, 'longitude lon_0 is at 6-o\'clock, and latitude lat_0 is tangent to the'
  print >> FileKeyUtils.WMSlog, 'edge of the map at lon_0.'
#end usage

def parseCmdln(cntrlatlon, bbox):
  """
  Command line parsing of projection and bbox params.
  """
  quit = False
  orign = 'C'
  if len(sys.argv) > 1 :
    arg = sys.argv[1]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      if arg.index('-h') >= 0 :
        quit = True # how we get past the exit below is a mystery to me
        usage()
        sys.exit(0)
    except: pass

  if quit :
    sys.exit(0)

  if len(sys.argv) > 1 :
    arg = sys.argv[1]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    for a in Anchor :
      a = a.lower() 
      try:
        if arg.index(a) >= 0 : orign = arg[1:].upper()
      except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox

  if len(sys.argv) > 2 :
    arg = sys.argv[2]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
     cntrlatlon[0] = lat0 = float(arg)
    except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox

  if len(sys.argv) > 3 :
    arg = sys.argv[3]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      cntrlatlon[1] = lon0 = float(arg)
    except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox
 
  if len(sys.argv) > 4 :
    arg = sys.argv[4]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      bbox[0] = float(arg)
    except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox

  if len(sys.argv) > 5 :
    arg = sys.argv[5]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      bbox[1] = float(arg)
    except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox

  if len(sys.argv) > 6 :
    arg = sys.argv[6]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      bbox[2] = float(arg)
    except: pass
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox

  if len(sys.argv) > 7 :
    arg = sys.argv[7]
#   print >> FileKeyUtils.WMSlog, 'GeoProj.py> arg: ', arg
    try:
      bbox[3] = float(arg)
    except: pass

  return orign
#end parseCmdln()

def printDict(dict):
  """
  Yet another way to printout hash dict. contents
  """
  for k in proj4dict.keys():
    print >> FileKeyUtils.WMSlog, k, ' ==> ', proj4dict[k]

# invoke this before creating matplotlib.basemap/pylab 'figure' 
def setRcParms(wpix, hpix):
  """
  Set relevant Matplotlib.basemap graphics rendering style.
  """
# pylab.rcParams['image.aspect'] = wpix/hpix
  dpi = float(pylab.rcParams['savefig.dpi'])
  pylab.rcParams['figure.dpi'] = dpi 
  pylab.rcParams['figure.figsize'] = (wpix/dpi, hpix/dpi)
  pylab.rcParams['lines.antialiased'] = True
  pylab.rcParams['lines.color'] = 'w'
  pylab.rcParams['lines.linestyle'] = '-' # solid?
  pylab.rcParams['lines.linewidth'] = 0.50
# these are no longer allowed == 0
# pylab.rcParams['figure.subplot.wspace'] = 0.0
  pylab.rcParams['figure.subplot.wspace'] = 0.0000001
  pylab.rcParams['figure.subplot.hspace'] = 0.0000001
  pylab.rcParams['figure.subplot.bottom'] = 0.0000001
# pylab.rcParams['figure.subplot.top'] = 1.0
  pylab.rcParams['figure.subplot.top'] = 0.9999999
  pylab.rcParams['figure.subplot.left'] = 0.0000001
  pylab.rcParams['figure.subplot.right'] = 0.9999999
# this seems to have become 'deprecated':
# pylab.rcParams['grid.antialiased'] = True
  pylab.rcParams['grid.color'] = 'w'
  pylab.rcParams['grid.linestyle'] = '-' # solid?
  pylab.rcParams['grid.linewidth'] = 0.50
  pylab.rcParams['patch.antialiased'] = True
  pylab.rcParams['patch.facecolor'] = 'w'
  pylab.rcParams['patch.edgecolor'] = 'w' # solid?
  pylab.rcParams['patch.linewidth'] = 0.50
# print >> FileKeyUtils.WMSlog, 'GeoProj.setRcParms> pylab.rcParams:\n', pylab.rcParams
#end setRcParms

############################################################ module attributes:
# these pole-centered epsg codes were cut-pasted from
# the table in http://nsidc.org/data/atlas/ogc_services.html 
LatLonEPSGlist = ['EPSG:3410', 'EPSG:4326']

NorthPolarEPSGlist = ['EPSG:32661', 'EPSG:3411', 'EPSG:3413', 'EPSG:3571', 
                      'EPSG:3572' , 'EPSG:3573', 'EPSG:3574', 'EPSG:3575', 'EPSG:3576']
SouthPolarEPSGlist = ['EPSG:32761', 'EPSG:3031', 'EPSG:3412']

PolarEPSGlist = NorthPolarEPSGlist + SouthPolarEPSGlist

# basemap 'internal/native datastore' resolutions:
Resbasemap = ['c', 'l', 'i', 'h'] # course/crude, low, interm., high
# Allowed Anchor/origin values are:
Anchor = ['C', 'SW', 'S', 'SE', 'E', 'NE', 'N', 'NW', 'W']

# these dicts can be used with the Basemap ctor(projection='whatever',...)
# and rather than a manual cut-paste, the Proj4dict could be initialized
# better via a popen('proj -l') or popen('proj -lp')
# and a tad bit more info. on each projection id via popen('proj -l=id') 
#
# assume ups and pstere are synonymous (for now)
#PolarProjlist = ['ups', 'pstere', 'paeqd', 'plaea']
PolarProjlist = ['pstere', 'paeqd', 'plaea']
NorthPolarProjlist = ['npstere', 'npaeqd', 'nplaea']
PolarProjlist += NorthPolarProjlist
SouthPolarProjlist = ['spstere', 'spaeqd', 'splaea']
PolarProjlist += SouthPolarProjlist

PolarProjdict = {'PolarStereographic':'pstere', 'UniversalPolarStereographic':'ups',
'PolarAzimuthalEquidistant':'paeqd', 'PolarLambertAzimuthal':'plaea'}

ReversePolarProjdict = {'pstere':'PolarStereographic', 'ups':'UniversalPolarStereographic',
'paeqd':'PolarAzimuthalEquidistant', 'plaea':'PolarLambertAzimuthal'}

Proj4dict = {'AlbersEqualArea':'aea',
'AzimuthalEquidistant':'aeqd',
'Airy':'airy',
'Aitoff':'aitoff',
'Mod.StererographicsofAlaska':'alsk',
'ApianGlobularI':'apian',
'AugustEpicycloidal':'august',
'BaconGlobular':'bacon',
'Bipolarconicofwesternhemisphere':'bipc',
'BoggsEumorphic':'boggs',
'Bonne(Wernerlat_1=90)':'bonne',
'Cassini':'cass',
'CentralCylindrical':'cc',
'EqualAreaCylindrical':'cea',
'ChamberlinTrimetric':'chamb',
'Collignon':'collg',
'CrasterParabolic(PutninsP4)':'crast',
'DenoyerSemi-Elliptical':'denoy',
'EckertI':'eck1',
'EckertII':'eck2',
'EckertIII':'eck3',
'EckertIV':'eck4',
'EckertV':'eck5',
'EckertVI':'eck6',
'EquidistantCylindrical(PlateCaree)':'eqc',
'EquidistantConic':'eqdc',
'Euler':'euler',
'Fahey':'fahey',
'Foucaut':'fouc',
'FoucautSinusoidal':'fouc_s',
'Gall(GallStereographic)':'gall',
'Geocentric':'geocent',
'GeostationarySatelliteView':'geos',
'GinsburgVIII(TsNIIGAiK)':'gins8',
'GeneralSinusoidalSeries':'gn_sinu',
'Gnomonic':'gnom',
'GoodeHomolosine':'goode',
'Mod.Stererographicsof48U.S.':'gs48',
'Mod.Stererographicsof50U.S.':'gs50',
'Hammer&Eckert-Greifendorff':'hammer',
'HatanoAsymmetricalEqualArea':'hatano',
'InternationalMapoftheWorld':'imw_p',
'KavraiskyV':'kav5',
'KavraiskyVII':'kav7',
'Krovak':'krovak',
'Laborde':'labrd',
'LambertAzimuthalEqualArea':'laea',
'Lagrange':'lagrng',
'Larrivee':'larr',
'Laskowski':'lask',
'Lat/long(Geodetic)':'latlong',
'Lat/long(Geodetic)':'longlat',
'LambertConformalConic':'lcc',
'LambertConformalConicAlternative':'lcca',
'LambertEqualAreaConic':'leac',
'LeeOblatedStereographic':'lee_os',
'Loximuthal':'loxim',
'SpaceobliqueforLANDSAT':'lsat',
'McBryde-ThomasFlat-PolarSine(No.1)':'mbt_s',
'McBryde-ThomasFlat-PoleSine(No.2)':'mbt_fps',
'McBride-ThomasFlat-PolarParabolic':'mbtfpp',
'McBryde-ThomasFlat-PolarQuartic':'mbtfpq',
'McBryde-ThomasFlat-PolarSinusoidal':'mbtfps',
'Mercator':'merc',
'MillerOblatedStereographic':'mil_os',
'MillerCylindrical':'mill',
'ModifiedPolyconic':'mpoly',
'Mollweide':'moll',
'MurdochI':'murd1',
'MurdochII':'murd2',
'MurdochIII':'murd3',
'Nell':'nell',
'Nell-Hammer':'nell_h',
'NicolosiGlobular':'nicol',
'Near-sidedperspective':'nsper',
'NewZealandMapGrid':'nzmg',
'GeneralObliqueTransformation':'ob_tran',
'ObliqueCylindricalEqualArea':'ocea',
'OblatedEqualArea':'oea',
'ObliqueMercator':'omerc',
'OrteliusOval':'ortel',
'Orthographic':'ortho',
'PerspectiveConic':'pconic',
'Polyconic(American)':'poly',
'PutninsP1':'putp1',
'PutninsP2':'putp2',
'PutninsP3':'putp3',
'PutninsP3':'putp3p',
'PutninsP4':'putp4p',
'PutninsP5':'putp5',
'PutninsP5':'putp5p',
'PutninsP6':'putp6',
'PutninsP6':'putp6p',
'QuarticAuthalic':'qua_aut',
'Robinson':'robin',
'RoussilheStereographic':'rouss',
'RectangularPolyconic':'rpoly',
'Sinusoidal(Sanson-Flamsteed)':'sinu',
'Swiss.Obl.Mercator':'somerc',
'Stereographic':'stere',
'ObliqueStereographicAlternative':'sterea',
'TransverseCentralCylindrical':'tcc',
'TransverseCylindricalEqualArea':'tcea',
'Tissot':'tissot',
'TransverseMercator':'tmerc',
'TwoPointEquidistant':'tpeqd',
'Tiltedperspective':'tpers',
'UniversalPolarStereographic':'ups',
'UrmaevV':'urm5',
'UrmaevFlat-PolarSinusoidal':'urmfps',
'UniversalTransverseMercator(UTM)':'utm',
'vanderGrinten(I)':'vandg',
'vanderGrintenII':'vandg2',
'vanderGrintenIII':'vandg3',
'vanderGrintenIV':'vandg4',
'VitkovskyI':'vitk1',
'WagnerI(KavraiskyVI)':'wag1',
'WagnerII':'wag2',
'WagnerIII':'wag3',
'WagnerIV':'wag4',
'WagnerV':'wag5',
'WagnerVI':'wag6',
'WagnerVII':'wag7',
'WerenskioldI':'weren',
'WinkelI':'wink1',
'WinkelII':'wink2',
'WinkelTripel':'wintri'} # Proj4dict{}

#the vmap0 layer ists created via somethong like:
# find /devstore/GIS/VMAP0 -name "*.shp'," | cut -c3-' | cut -d' ' -f11- | sed 's/\.shp//g' | sed 's/ -> ../":"/g' | sed 's/^/"/g' | sed 's/$/",/g'

VMAP0EURLayers = {
"AEROFACP":"v0eur_shp/AEROFACP",
"AQUECANL":"v0eur_shp/AQUECANL",
"BARRIERL":"v0eur_shp/BARRIERL",
"BNDTXT":"v0eur_shp/BNDTXT",
"BUILTUPA":"v0eur_shp/BUILTUPA",
"BUILTUPP":"v0eur_shp/BUILTUPP",
"COASTL":"v0eur_shp/COASTL",
"CONTOURL":"v0eur_shp/CONTOURL",
"CROPA":"v0eur_shp/CROPA",
"CUTFILL":"v0eur_shp/CUTFILL",
"DANGERP":"v0eur_shp/DANGERP",
"DEPTHL":"v0eur_shp/DEPTHL",
"DQAREA":"v0eur_shp/DQAREA",
"DQLINE":"v0eur_shp/DQLINE",
"ELEVP":"v0eur_shp/ELEVP",
"EXTRACTA":"v0eur_shp/EXTRACTA",
"EXTRACTP":"v0eur_shp/EXTRACTP",
"FISHINDA":"v0eur_shp/FISHINDA",
"GRASSA":"v0eur_shp/GRASSA",
"GROUNDA":"v0eur_shp/GROUNDA",
"HYDROTXT":"v0eur_shp/HYDROTXT",
"INDTXT":"v0eur_shp/INDTXT",
"INWATERA":"v0eur_shp/INWATERA",
"LANDICEA":"v0eur_shp/LANDICEA",
"LIBREF":"v0eur_shp/LIBREF",
"LIBREFT":"v0eur_shp/LIBREFT",
"LNDFRML":"v0eur_shp/LNDFRML",
"MISCL":"v0eur_shp/MISCL",
"MISCP":"v0eur_shp/MISCP",
"MISINDP":"v0eur_shp/MISINDP",
"MISPOPP":"v0eur_shp/MISPOPP",
"MISTRANL":"v0eur_shp/MISTRANL",
"OCEANSEA":"v0eur_shp/OCEANSEA",
"PHYSTXT":"v0eur_shp/PHYSTXT",
"PIPEL":"v0eur_shp/PIPEL",
"POLBNDA":"v0eur_shp/POLBNDA",
"POLBNDL":"v0eur_shp/POLBNDL",
"POLBNDP":"v0eur_shp/POLBNDP",
"POPTXT":"v0eur_shp/POPTXT",
"RAILRDL":"v0eur_shp/RAILRDL",
"ROADL":"v0eur_shp/ROADL",
"RRYARDP":"v0eur_shp/RRYARDP",
"SEAICEA":"v0eur_shp/SEAICEA",
"STORAGEP":"v0eur_shp/STORAGEP",
"SWAMPA":"v0eur_shp/SWAMPA",
"TILEREF":"v0eur_shp/TILEREF",
"TILEREFT":"v0eur_shp/TILEREFT",
"TRAILL":"v0eur_shp/TRAILL",
"TRANSTRC":"v0eur_shp/TRANSTRC",
"TRANSTRL":"v0eur_shp/TRANSTRL",
"TRANSTXT":"v0eur_shp/TRANSTXT",
"TREESA":"v0eur_shp/TREESA",
"TUNDRAA":"v0eur_shp/TUNDRAA",
"UTILL":"v0eur_shp/UTILL",
"UTILP":"v0eur_shp/UTILP",
"UTILTXT":"v0eur_shp/UTILTXT",
"WATRCRSL":"v0eur_shp/WATRCRSL"}

VMAP0NOALayers = {
"AEROFACP":"v0noa_shp/AEROFACP",
"AQUECANL":"v0noa_shp/AQUECANL",
"BNDTXT":"v0noa_shp/BNDTXT",
"BUILTUPA":"v0noa_shp/BUILTUPA",
"COASTL":"v0noa_shp/COASTL",
"CONTOURL":"v0noa_shp/CONTOURL",
"CROPA":"v0noa_shp/CROPA",
"DANGERP":"v0noa_shp/DANGERP",
"DEPTHL":"v0noa_shp/DEPTHL",
"DQAREA":"v0noa_shp/DQAREA",
"DQLINE":"v0noa_shp/DQLINE",
"DQTXT":"v0noa_shp/DQTXT",
"ELEVP":"v0noa_shp/ELEVP",
"EXTRACTA":"v0noa_shp/EXTRACTA",
"EXTRACTP":"v0noa_shp/EXTRACTP",
"GRASSA":"v0noa_shp/GRASSA",
"GROUNDA":"v0noa_shp/GROUNDA",
"HYDROTXT":"v0noa_shp/HYDROTXT",
"INDTXT":"v0noa_shp/INDTXT",
"INWATERA":"v0noa_shp/INWATERA",
"LANDICEA":"v0noa_shp/LANDICEA",
"LIBREF":"v0noa_shp/LIBREF",
"LIBREFT":"v0noa_shp/LIBREFT",
"MISCP":"v0noa_shp/MISCP",
"MISINDP":"v0noa_shp/MISINDP",
"MISPOPA":"v0noa_shp/MISPOPA",
"MISPOPP":"v0noa_shp/MISPOPP",
"MISTRANL":"v0noa_shp/MISTRANL",
"OCEANSEA":"v0noa_shp/OCEANSEA",
"PHYSTXT":"v0noa_shp/PHYSTXT",
"PIPEL":"v0noa_shp/PIPEL",
"POLBNDA":"v0noa_shp/POLBNDA",
"POLBNDL":"v0noa_shp/POLBNDL",
"POLBNDP":"v0noa_shp/POLBNDP",
"POPTXT":"v0noa_shp/POPTXT",
"RAILRDL":"v0noa_shp/RAILRDL",
"ROADL":"v0noa_shp/ROADL",
"RRYARDP":"v0noa_shp/RRYARDP",
"SEAICEA":"v0noa_shp/SEAICEA",
"STORAGEP":"v0noa_shp/STORAGEP",
"SWAMPA":"v0noa_shp/SWAMPA",
"TILEREF":"v0noa_shp/TILEREF",
"TILEREFT":"v0noa_shp/TILEREFT",
"TRAILL":"v0noa_shp/TRAILL",
"TRANSTRC":"v0noa_shp/TRANSTRC",
"TRANSTRL":"v0noa_shp/TRANSTRL",
"TRANSTXT":"v0noa_shp/TRANSTXT",
"TREESA":"v0noa_shp/TREESA",
"TUNDRAA":"v0noa_shp/TUNDRAA",
"UTILL":"v0noa_shp/UTILL",
"UTILP":"v0noa_shp/UTILP",
"UTILTXT":"v0noa_shp/UTILTXT",
"WATRCRSL":"v0noa_shp/WATRCRSL"}

VMAP0SASLayers = {
"AEROFACP":"v0sas_shp/AEROFACP",
"AQUECANL":"v0sas_shp/AQUECANL",
"BARRIERL":"v0sas_shp/BARRIERL",
"BNDTXT":"v0sas_shp/BNDTXT",
"BUILTUPA":"v0sas_shp/BUILTUPA",
"BUILTUPP":"v0sas_shp/BUILTUPP",
"COASTL":"v0sas_shp/COASTL",
"CONTOURL":"v0sas_shp/CONTOURL",
"CROPA":"v0sas_shp/CROPA",
"DANGERP":"v0sas_shp/DANGERP",
"DEPTHL":"v0sas_shp/DEPTHL",
"DQAREA":"v0sas_shp/DQAREA",
"DQLINE":"v0sas_shp/DQLINE",
"ELEVP":"v0sas_shp/ELEVP",
"EXTRACTA":"v0sas_shp/EXTRACTA",
"EXTRACTP":"v0sas_shp/EXTRACTP",
"FISHINDA":"v0sas_shp/FISHINDA",
"GRASSA":"v0sas_shp/GRASSA",
"GROUNDA":"v0sas_shp/GROUNDA",
"HYDROTXT":"v0sas_shp/HYDROTXT",
"INDTXT":"v0sas_shp/INDTXT",
"INWATERA":"v0sas_shp/INWATERA",
"LANDICEA":"v0sas_shp/LANDICEA",
"LIBREF":"v0sas_shp/LIBREF",
"LIBREFT":"v0sas_shp/LIBREFT",
"LNDFRML":"v0sas_shp/LNDFRML",
"MISCL":"v0sas_shp/MISCL",
"MISCP":"v0sas_shp/MISCP",
"MISINDP":"v0sas_shp/MISINDP",
"MISPOPA":"v0sas_shp/MISPOPA",
"MISPOPP":"v0sas_shp/MISPOPP",
"MISTRANL":"v0sas_shp/MISTRANL",
"OCEANSEA":"v0sas_shp/OCEANSEA",
"PHYSTXT":"v0sas_shp/PHYSTXT",
"PIPEL":"v0sas_shp/PIPEL",
"POLBNDA":"v0sas_shp/POLBNDA",
"POLBNDL":"v0sas_shp/POLBNDL",
"POLBNDP":"v0sas_shp/POLBNDP",
"POPTXT":"v0sas_shp/POPTXT",
"RAILRDL":"v0sas_shp/RAILRDL",
"ROADL":"v0sas_shp/ROADL",
"RRYARDP":"v0sas_shp/RRYARDP",
"SEAICEA":"v0sas_shp/SEAICEA",
"STORAGEP":"v0sas_shp/STORAGEP",
"SWAMPA":"v0sas_shp/SWAMPA",
"TILEREF":"v0sas_shp/TILEREF",
"TILEREFT":"v0sas_shp/TILEREFT",
"TRAILL":"v0sas_shp/TRAILL",
"TRANSTRC":"v0sas_shp/TRANSTRC",
"TRANSTRL":"v0sas_shp/TRANSTRL",
"TRANSTXT":"v0sas_shp/TRANSTXT",
"TREESA":"v0sas_shp/TREESA",
"TUNDRAA":"v0sas_shp/TUNDRAA",
"UTILL":"v0sas_shp/UTILL",
"UTILP":"v0sas_shp/UTILP",
"UTILTXT":"v0sas_shp/UTILTXT",
"WATRCRSL":"v0sas_shp/WATRCRSL"}

VMAP0SOALayers = {
"AEROFACP":"v0soa_shp/AEROFACP",
"AQUECANL":"v0soa_shp/AQUECANL",
"BNDTXT":"v0soa_shp/BNDTXT",
"BUILTUPA":"v0soa_shp/BUILTUPA",
"BUILTUPP":"v0soa_shp/BUILTUPP",
"COASTL":"v0soa_shp/COASTL",
"CONTOURL":"v0soa_shp/CONTOURL",
"CROPA":"v0soa_shp/CROPA",
"DANGERP":"v0soa_shp/DANGERP",
"DEPTHL":"v0soa_shp/DEPTHL",
"DQAREA":"v0soa_shp/DQAREA",
"DQLINE":"v0soa_shp/DQLINE",
"DQTXT":"v0soa_shp/DQTXT",
"ELEVP":"v0soa_shp/ELEVP",
"EXTRACTA":"v0soa_shp/EXTRACTA",
"EXTRACTP":"v0soa_shp/EXTRACTP",
"GRASSA":"v0soa_shp/GRASSA",
"GROUNDA":"v0soa_shp/GROUNDA",
"HYDROTXT":"v0soa_shp/HYDROTXT",
"INDTXT":"v0soa_shp/INDTXT",
"INWATERA":"v0soa_shp/INWATERA",
"LANDICEA":"v0soa_shp/LANDICEA",
"LIBREF":"v0soa_shp/LIBREF",
"LIBREFT":"v0soa_shp/LIBREFT",
"MISCL":"v0soa_shp/MISCL",
"MISCP":"v0soa_shp/MISCP",
"MISINDP":"v0soa_shp/MISINDP",
"MISPOPP":"v0soa_shp/MISPOPP",
"MISTRANL":"v0soa_shp/MISTRANL",
"OCEANSEA":"v0soa_shp/OCEANSEA",
"PHYSTXT":"v0soa_shp/PHYSTXT",
"PIPEL":"v0soa_shp/PIPEL",
"POLBNDA":"v0soa_shp/POLBNDA",
"POLBNDL":"v0soa_shp/POLBNDL",
"POLBNDP":"v0soa_shp/POLBNDP",
"POPTXT":"v0soa_shp/POPTXT",
"RAILRDL":"v0soa_shp/RAILRDL",
"ROADL":"v0soa_shp/ROADL",
"RRYARDP":"v0soa_shp/RRYARDP",
"SEAICEA":"v0soa_shp/SEAICEA",
"STORAGEP":"v0soa_shp/STORAGEP",
"SWAMPA":"v0soa_shp/SWAMPA",
"TILEREF":"v0soa_shp/TILEREF",
"TILEREFT":"v0soa_shp/TILEREFT",
"TRAILL":"v0soa_shp/TRAILL",
"TRANSTRC":"v0soa_shp/TRANSTRC",
"TRANSTRL":"v0soa_shp/TRANSTRL",
"TRANSTXT":"v0soa_shp/TRANSTXT",
"TREESA":"v0soa_shp/TREESA",
"TUNDRAA":"v0soa_shp/TUNDRAA",
"UTILL":"v0soa_shp/UTILL",
"UTILP":"v0soa_shp/UTILP",
"UTILTXT":"v0soa_shp/UTILTXT",
"WATRCRSL":"v0soa_shp/WATRCRSL"}

# aliases to one ore more VMAP0 shapefiles:
VMAP0AliasLayers = {
'VMAP0POL':'POLBNDA', 'vmap0Pol':'POLBNDA', 'vmap0pol':'POLBNDA',
'VMAP0H2O':'INWATERA,WATRCRSL,OCEANSEA,HYDROTXT,BNDTXT', 
'vmap0H2O':'INWATERA,WATRCRSL,OCEANSEA,HYDROTXT,BNDTXT',
'vmap0h2o':'INWATERA,WATRCRSL,OCEANSEA,HYDROTXT,BNDTXT',
'VMAP0POLH2O':'POLBNDA,INWATERA', 'Vmap0PolH2O':'POLBNDA,INWATERA','vmap0polh2o':'POLBNDA,INWATERA'}
 
# evidently concatination of dicts is not supported, a pity...
#VMAPOAllLayers = VMAP0NOALayers + VMAP0SOALayers + VMAP0EURLayers + VMAP0SASLayers
VMAPORegionLayers = {}
for k, v in VMAP0NOALayers.items():
  VMAPORegionLayers['noa'+k] = v

for k, v in VMAP0SOALayers.items():
  VMAPORegionLayers['soa'+k] = v

for k, v in VMAP0EURLayers.items():
  VMAPORegionLayers['eur'+k] = v

for k, v in VMAP0SASLayers.items():
  VMAPORegionLayers['sas'+k] = v

def vmap0Layer(layer):
  """
  Checks all VMAP0 layer names and aliases for layer arg. presence and
  returns list of all matches.
  """
# pylab.rcParams['image.aspect'] = wpix/hpix
  layername = layer
  layerlist = []
# check if layer is an alias
  if VMAP0AliasLayers.has_key(layer):
    layernames = VMAP0AliasLayers[layer]
    layerlist = FileKeyUtils.parseCommas(layernames)

  print >> FileKeyUtils.WMSlog, 'vmap0Layer> layer:', layer,', alias to list:', layerlist
  vmap0regionlist = [VMAP0NOALayers, VMAP0SOALayers, VMAP0SASLayers, VMAP0EURLayers]
  all = []

# check alias list expansion:
  if len(layerlist) > 0 :
    for layername in layerlist:
      for regionlayer in ('noa'+layername, 'soa'+layername, 'eur'+layername, 'sas'+layername):
        if VMAPORegionLayers.has_key(regionlayer): #  vmap0 shapefile name for layerlist ala alias
          all.append(VMAPORegionLayers[regionlayer])
    
    print >> FileKeyUtils.WMSlog, 'vmap0Layer> vmap0 shapefile(s):', all
    return all

# actual vmap0 shapefile name was provided as layer
# could be all continents or specific region
  for vmap0region in vmap0regionlist:
    if vmap0region.has_key(layername):
      all.append(vmap0region[layername])
    print >> FileKeyUtils.WMSlog, 'vmap0Layer> vmap0 shapefile(s):', all
  return all
# end vmap0Layer

# 8km files:
BMNG8kmPNGs = [
'world.topo.bathy.200401.3x5400x2700.png', 'world.topo.bathy.200402.3x5400x2700.png',
'world.topo.bathy.200403.3x5400x2700.png', 'world.topo.bathy.200404.3x5400x2700.png',
'world.topo.bathy.200405.3x5400x2700.png', 'world.topo.bathy.200406.3x5400x2700.png',
'world.topo.bathy.200407.3x5400x2700.png', 'world.topo.bathy.200408.3x5400x2700.png',
'world.topo.bathy.200409.3x5400x2700.png', 'world.topo.bathy.200410.3x5400x2700.png',
'world.topo.bathy.200411.3x5400x2700.png', 'world.topo.bathy.200412.3x5400x2700.png']

BMNG8kmlist = [
'world.topo.bathy.200401.3x5400x2700.tif', 'world.topo.bathy.200402.3x5400x2700.tif',
'world.topo.bathy.200403.3x5400x2700.tif', 'world.topo.bathy.200404.3x5400x2700.tif',
'world.topo.bathy.200405.3x5400x2700.tif', 'world.topo.bathy.200406.3x5400x2700.tif',
'world.topo.bathy.200407.3x5400x2700.tif', 'world.topo.bathy.200408.3x5400x2700.tif',
'world.topo.bathy.200409.3x5400x2700.tif', 'world.topo.bathy.200410.3x5400x2700.tif',
'world.topo.bathy.200411.3x5400x2700.tif', 'world.topo.bathy.200412.3x5400x2700.tif']

# 2km files:
BMNG2kmPNGs = [
'world.topo.bathy.200401.3x21600x10800.png', 'world.topo.bathy.200402.3x21600x10800.png',
'world.topo.bathy.200403.3x21600x10800.png', 'world.topo.bathy.200404.3x21600x10800.png',
'world.topo.bathy.200405.3x21600x10800.png', 'world.topo.bathy.200406.3x21600x10800.png',
'world.topo.bathy.200407.3x21600x10800.png', 'world.topo.bathy.200408.3x21600x10800.png',
'world.topo.bathy.200409.3x21600x10800.png', 'world.topo.bathy.200410.3x21600x10800.png',
'world.topo.bathy.200411.3x21600x10800.png', 'world.topo.bathy.200412.3x21600x10800.png']

BMNG2kmlist = [
'world.topo.bathy.200401.3x21600x10800.tif', 'world.topo.bathy.200402.3x21600x10800.tif',
'world.topo.bathy.200403.3x21600x10800.tif', 'world.topo.bathy.200404.3x21600x10800.tif',
'world.topo.bathy.200405.3x21600x10800.tif', 'world.topo.bathy.200406.3x21600x10800.tif',
'world.topo.bathy.200407.3x21600x10800.tif', 'world.topo.bathy.200408.3x21600x10800.tif',
'world.topo.bathy.200409.3x21600x10800.tif', 'world.topo.bathy.200410.3x21600x10800.tif',
'world.topo.bathy.200411.3x21600x10800.tif', 'world.topo.bathy.200412.3x21600x10800.tif']

# 8k and 2km layer dicts:
BMNG8kmLayers = {'WinterBMNG':BMNG8kmlist[0], 'Winter':BMNG8kmlist[0],
'BMNG02':BMNG8kmlist[1], 'BMNG03':BMNG8kmlist[2],
'BMNG04':BMNG8kmlist[3], 'BMNG05':BMNG8kmlist[4], 'BMNG06':BMNG8kmlist[5],
'SummerBMNG':BMNG8kmlist[6], 'Summer':BMNG8kmlist[6],
'BMNG08':BMNG8kmlist[7], 'BMNG09':BMNG8kmlist[8], 'BMNG10':BMNG8kmlist[9],
'BMNG11':BMNG8kmlist[10], 'BMNG12':BMNG8kmlist[11]}

BMNG2kmLayers = {'WinterBMNG':BMNG2kmlist[0], 'Winter':BMNG2kmlist[0],
'BMNG02':BMNG2kmlist[1], 'BMNG03':BMNG2kmlist[2],
'BMNG04':BMNG2kmlist[3], 'BMNG05':BMNG2kmlist[4], 'BMNG06':BMNG2kmlist[5],
'SummerBMNG':BMNG2kmlist[6], 'Summer':BMNG2kmlist[6],
'BMNG08':BMNG2kmlist[7], 'BMNG09':BMNG2kmlist[8], 'BMNG10':BMNG2kmlist[9],
'BMNG11':BMNG2kmlist[10], 'BMNG12':BMNG2kmlist[11]}

# BMNG raster input aliases and file lists
#BMNGAliasLayers = {'BMNG':'SummerBMNG', 'BMNG07':'SummerBMNG', 'BMNG00':'WinterBMNG', 'BMNG0':'WinterBMNG'}
BMNGAliasLayers = {'BMNG':'Summer', 'BMNG07':'Summer', 'BMNG00':'Winter', 'BMNG0':'Winter'}

def layerSizeBMNG(filename):
  """
  Checks filename (substring) for BMNG resolution/pixel-size naming convention
  and returns size = [width, height]
  """
  sz = [5400, 2700] # default to 8km
  try:
    if filename.index('21600') >= 0 :
      if filename.index('10800') >= 0 :
        sz = [21600, 10800]
  except: pass
  return sz

def layerFileBMNG(layer, bmngs, aliases):
  """
  Returns filename for layer arg. in BMNG hash dict. or layer alias
  """
  layername = layer
# check aliases
  if aliases.has_key(layer):
    layername = aliases[layer] # replace alias

  if bmngs.has_key(layername):
    return bmngs[layername]

# also compare case insensitive:
  layername = layer.upper()
  BMNGs = {}
  for b in aliases.keys():
    BMNGs[b.upper()] = aliases[b] # uppercase layername via alias

  for b in bmngs.keys():
    BMNGs[b.upper()] = bmngs[b] # uppercase layername

  if BMNGs.has_key(layername):
    return BMNGs[layername]
 
  return None
#end layerFileBMNG

def layerFileBMNG8km(layer):
  """
  Returns 8km filename for layer arg.
  """
  b8km = layerFileBMNG(layer, BMNG8kmLayers, BMNGAliasLayers)
  if b8km == None:
#   b8km = BMNG8kmLayers['Summer']
    print >> FileKeyUtils.WMSlog, 'GeoProj.layerFileBMNG8km> not 8km BMNG layer:', layer     
  return b8km
#end layerFileBMNG8km

def layerFileBMNG2km(layer):
  """
  Returns 2km filename for layer arg.
  """
  b2km = layerFileBMNG(layer, BMNG2kmLayers, BMNGAliasLayers)
  if b2km == None:
#   b2km = BMNG2kmLayers['Summer']
    print >> FileKeyUtils.WMSlog, 'GeoProj.layerFileBMNG2km> not 2km BMNG layer:', layer     
  return b2km
#end layerFileBMNG2km

# 500m:
BMNG500mPNGs = [
"world.topo.bathy.200401.3x21600x21600.A1.png",
"world.topo.bathy.200401.3x21600x21600.A2.png",
"world.topo.bathy.200401.3x21600x21600.B1.png",
"world.topo.bathy.200401.3x21600x21600.B2.png",
"world.topo.bathy.200401.3x21600x21600.C1.png",
"world.topo.bathy.200401.3x21600x21600.C2.png",
"world.topo.bathy.200401.3x21600x21600.D1.png",
"world.topo.bathy.200401.3x21600x21600.D2.png",
"world.topo.bathy.200402.3x21600x21600.A1.png",
"world.topo.bathy.200402.3x21600x21600.A2.png",
"world.topo.bathy.200402.3x21600x21600.B1.png",
"world.topo.bathy.200402.3x21600x21600.B2.png",
"world.topo.bathy.200402.3x21600x21600.C1.png",
"world.topo.bathy.200402.3x21600x21600.C2.png",
"world.topo.bathy.200402.3x21600x21600.D2.png",
"world.topo.bathy.200403.3x21600x21600.A1.png",
"world.topo.bathy.200403.3x21600x21600.A2.png",
"world.topo.bathy.200403.3x21600x21600.B1.png",
"world.topo.bathy.200403.3x21600x21600.B2.png",
"world.topo.bathy.200403.3x21600x21600.C1.png",
"world.topo.bathy.200403.3x21600x21600.C2.png",
"world.topo.bathy.200403.3x21600x21600.D1.png",
"world.topo.bathy.200403.3x21600x21600.D2.png",
"world.topo.bathy.200404.3x21600x21600.A1.png",
"world.topo.bathy.200404.3x21600x21600.A2.png",
"world.topo.bathy.200404.3x21600x21600.B1.png",
"world.topo.bathy.200404.3x21600x21600.B2.png",
"world.topo.bathy.200404.3x21600x21600.C1.png",
"world.topo.bathy.200404.3x21600x21600.C2.png",
"world.topo.bathy.200404.3x21600x21600.D2.png",
"world.topo.bathy.200405.3x21600x21600.A1.png",
"world.topo.bathy.200405.3x21600x21600.B1.png",
"world.topo.bathy.200405.3x21600x21600.B2.png",
"world.topo.bathy.200405.3x21600x21600.C1.png",
"world.topo.bathy.200405.3x21600x21600.C2.png",
"world.topo.bathy.200405.3x21600x21600.D1.png",
"world.topo.bathy.200405.3x21600x21600.D2.png",
"world.topo.bathy.200406.3x21600x21600.A1.png",
"world.topo.bathy.200406.3x21600x21600.A2.png",
"world.topo.bathy.200406.3x21600x21600.B2.png",
"world.topo.bathy.200406.3x21600x21600.C1.png",
"world.topo.bathy.200406.3x21600x21600.C2.png",
"world.topo.bathy.200406.3x21600x21600.D1.png",
"world.topo.bathy.200406.3x21600x21600.D2.png",
"world.topo.bathy.200407.3x21600x21600.A1.png",
"world.topo.bathy.200407.3x21600x21600.A2.png",
"world.topo.bathy.200407.3x21600x21600.B1.png",
"world.topo.bathy.200407.3x21600x21600.B2.png",
"world.topo.bathy.200407.3x21600x21600.C1.png",
"world.topo.bathy.200407.3x21600x21600.C2.png",
"world.topo.bathy.200407.3x21600x21600.D1.png",
"world.topo.bathy.200407.3x21600x21600.D2.png",
"world.topo.bathy.200408.3x21600x21600.A1.png",
"world.topo.bathy.200408.3x21600x21600.A2.png",
"world.topo.bathy.200408.3x21600x21600.B1.png",
"world.topo.bathy.200408.3x21600x21600.B2.png",
"world.topo.bathy.200408.3x21600x21600.C1.png",
"world.topo.bathy.200408.3x21600x21600.C2.png",
"world.topo.bathy.200408.3x21600x21600.D1.png",
"world.topo.bathy.200408.3x21600x21600.D2.png",
"world.topo.bathy.200409.3x21600x21600.A1.png",
"world.topo.bathy.200409.3x21600x21600.A2.png",
"world.topo.bathy.200409.3x21600x21600.B1.png",
"world.topo.bathy.200409.3x21600x21600.B2.png",
"world.topo.bathy.200409.3x21600x21600.C1.png",
"world.topo.bathy.200409.3x21600x21600.C2.png",
"world.topo.bathy.200409.3x21600x21600.D1.png",
"world.topo.bathy.200409.3x21600x21600.D2.png",
"world.topo.bathy.200410.3x21600x21600.A1.png",
"world.topo.bathy.200410.3x21600x21600.A2.png",
"world.topo.bathy.200410.3x21600x21600.B1.png",
"world.topo.bathy.200410.3x21600x21600.B2.png",
"world.topo.bathy.200410.3x21600x21600.C1.png",
"world.topo.bathy.200410.3x21600x21600.C2.png",
"world.topo.bathy.200410.3x21600x21600.D1.png",
"world.topo.bathy.200410.3x21600x21600.D2.png",
"world.topo.bathy.200411.3x21600x21600.A1.png",
"world.topo.bathy.200411.3x21600x21600.A2.png",
"world.topo.bathy.200411.3x21600x21600.B1.png",
"world.topo.bathy.200411.3x21600x21600.B2.png",
"world.topo.bathy.200411.3x21600x21600.C1.png",
"world.topo.bathy.200411.3x21600x21600.C2.png",
"world.topo.bathy.200411.3x21600x21600.D1.png",
"world.topo.bathy.200411.3x21600x21600.D2.png",
"world.topo.bathy.200412.3x21600x21600.A1.png",
"world.topo.bathy.200412.3x21600x21600.A2.png",
"world.topo.bathy.200412.3x21600x21600.B1.png",
"world.topo.bathy.200412.3x21600x21600.B2.png",
"world.topo.bathy.200412.3x21600x21600.C1.png",
"world.topo.bathy.200412.3x21600x21600.C2.png",
"world.topo.bathy.200412.3x21600x21600.D1.png",
"world.topo.bathy.200412.3x21600x21600.D2.png"]

BMNG500mlist = [
"world.topo.bathy.200401.3x21600x21600.A1.tif",
"world.topo.bathy.200401.3x21600x21600.A2.tif",
"world.topo.bathy.200401.3x21600x21600.B1.tif",
"world.topo.bathy.200401.3x21600x21600.B2.tif",
"world.topo.bathy.200401.3x21600x21600.C1.tif",
"world.topo.bathy.200401.3x21600x21600.C2.tif",
"world.topo.bathy.200401.3x21600x21600.D1.tif",
"world.topo.bathy.200401.3x21600x21600.D2.tif",
"world.topo.bathy.200402.3x21600x21600.A1.tif",
"world.topo.bathy.200402.3x21600x21600.A2.tif",
"world.topo.bathy.200402.3x21600x21600.B1.tif",
"world.topo.bathy.200402.3x21600x21600.B2.tif",
"world.topo.bathy.200402.3x21600x21600.C1.tif",
"world.topo.bathy.200402.3x21600x21600.C2.tif",
"world.topo.bathy.200402.3x21600x21600.D2.tif",
"world.topo.bathy.200403.3x21600x21600.A1.tif",
"world.topo.bathy.200403.3x21600x21600.A2.tif",
"world.topo.bathy.200403.3x21600x21600.B1.tif",
"world.topo.bathy.200403.3x21600x21600.B2.tif",
"world.topo.bathy.200403.3x21600x21600.C1.tif",
"world.topo.bathy.200403.3x21600x21600.C2.tif",
"world.topo.bathy.200403.3x21600x21600.D1.tif",
"world.topo.bathy.200403.3x21600x21600.D2.tif",
"world.topo.bathy.200404.3x21600x21600.A1.tif",
"world.topo.bathy.200404.3x21600x21600.A2.tif",
"world.topo.bathy.200404.3x21600x21600.B1.tif",
"world.topo.bathy.200404.3x21600x21600.B2.tif",
"world.topo.bathy.200404.3x21600x21600.C1.tif",
"world.topo.bathy.200404.3x21600x21600.C2.tif",
"world.topo.bathy.200404.3x21600x21600.D2.tif",
"world.topo.bathy.200405.3x21600x21600.A1.tif",
"world.topo.bathy.200405.3x21600x21600.B1.tif",
"world.topo.bathy.200405.3x21600x21600.B2.tif",
"world.topo.bathy.200405.3x21600x21600.C1.tif",
"world.topo.bathy.200405.3x21600x21600.C2.tif",
"world.topo.bathy.200405.3x21600x21600.D1.tif",
"world.topo.bathy.200405.3x21600x21600.D2.tif",
"world.topo.bathy.200406.3x21600x21600.A1.tif",
"world.topo.bathy.200406.3x21600x21600.A2.tif",
"world.topo.bathy.200406.3x21600x21600.B2.tif",
"world.topo.bathy.200406.3x21600x21600.C1.tif",
"world.topo.bathy.200406.3x21600x21600.C2.tif",
"world.topo.bathy.200406.3x21600x21600.D1.tif",
"world.topo.bathy.200406.3x21600x21600.D2.tif",
"world.topo.bathy.200407.3x21600x21600.A1.tif",
"world.topo.bathy.200407.3x21600x21600.A2.tif",
"world.topo.bathy.200407.3x21600x21600.B1.tif",
"world.topo.bathy.200407.3x21600x21600.B2.tif",
"world.topo.bathy.200407.3x21600x21600.C1.tif",
"world.topo.bathy.200407.3x21600x21600.C2.tif",
"world.topo.bathy.200407.3x21600x21600.D1.tif",
"world.topo.bathy.200407.3x21600x21600.D2.tif",
"world.topo.bathy.200408.3x21600x21600.A1.tif",
"world.topo.bathy.200408.3x21600x21600.A2.tif",
"world.topo.bathy.200408.3x21600x21600.B1.tif",
"world.topo.bathy.200408.3x21600x21600.B2.tif",
"world.topo.bathy.200408.3x21600x21600.C1.tif",
"world.topo.bathy.200408.3x21600x21600.C2.tif",
"world.topo.bathy.200408.3x21600x21600.D1.tif",
"world.topo.bathy.200408.3x21600x21600.D2.tif",
"world.topo.bathy.200409.3x21600x21600.A1.tif",
"world.topo.bathy.200409.3x21600x21600.A2.tif",
"world.topo.bathy.200409.3x21600x21600.B1.tif",
"world.topo.bathy.200409.3x21600x21600.B2.tif",
"world.topo.bathy.200409.3x21600x21600.C1.tif",
"world.topo.bathy.200409.3x21600x21600.C2.tif",
"world.topo.bathy.200409.3x21600x21600.D1.tif",
"world.topo.bathy.200409.3x21600x21600.D2.tif",
"world.topo.bathy.200410.3x21600x21600.A1.tif",
"world.topo.bathy.200410.3x21600x21600.A2.tif",
"world.topo.bathy.200410.3x21600x21600.B1.tif",
"world.topo.bathy.200410.3x21600x21600.B2.tif",
"world.topo.bathy.200410.3x21600x21600.C1.tif",
"world.topo.bathy.200410.3x21600x21600.C2.tif",
"world.topo.bathy.200410.3x21600x21600.D1.tif",
"world.topo.bathy.200410.3x21600x21600.D2.tif",
"world.topo.bathy.200411.3x21600x21600.A1.tif",
"world.topo.bathy.200411.3x21600x21600.A2.tif",
"world.topo.bathy.200411.3x21600x21600.B1.tif",
"world.topo.bathy.200411.3x21600x21600.B2.tif",
"world.topo.bathy.200411.3x21600x21600.C1.tif",
"world.topo.bathy.200411.3x21600x21600.C2.tif",
"world.topo.bathy.200411.3x21600x21600.D1.tif",
"world.topo.bathy.200411.3x21600x21600.D2.tif",
"world.topo.bathy.200412.3x21600x21600.A1.tif",
"world.topo.bathy.200412.3x21600x21600.A2.tif",
"world.topo.bathy.200412.3x21600x21600.B1.tif",
"world.topo.bathy.200412.3x21600x21600.B2.tif",
"world.topo.bathy.200412.3x21600x21600.C1.tif",
"world.topo.bathy.200412.3x21600x21600.C2.tif",
"world.topo.bathy.200412.3x21600x21600.D1.tif",
"world.topo.bathy.200412.3x21600x21600.D2.tif"]

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print >> FileKeyUtils.WMSlog, _modinfo
  help("GeoProj")

if __name__ ==  '__main__' :
# preserve argv -- evidently some modules need it
  arg0 = sys.argv[0] # do not use sys.argv.pop(0)!
  orign = 'C'
  cntrlatlon = [0.0, 0.0]
  bbox = [0.0, 0.0, 0.0, 0.0, 0.0] 
  orign = parseCmdln(cntrlatlon, bbox)
# print >> FileKeyUtils.WMSlog, 'GeoProj.py> parms:', orign, cntrlatlon, bbox
  printInfoDoc()

#end main
