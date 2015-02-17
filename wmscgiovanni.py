#!/bin/env python
svnUrl = '$HeadURL$'
svnId = rcsId = '$Name$ $Id$'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
The wmscgiovanni module provides apache httpd mod_python handlers as entry
points into the OGC WMSC (with custom extensions).
"""
#
#from mod_python import apache
#OGCREST = apache.import_module('~/lib/OGCREST.py')
#import OGCREST, FileKeyUtils, PILMemCache, GeoProj, GeoImage
import G3WMS.OGCREST as OGCREST

def wmsc(req): # unbuffered BMNG input data
  """
  Handles WMSC requests without pre-loaded/buffered (in process RAM) images.
  The OGCREST module relies extensively (directly and indirectly via other
  modules) on a number of open source projects. While each of these projects
  also rely on an extensive stack of external modules (see devwmsc_install.csh),
  the principals are:

    http://www.pythonware.com/products/pil/
    http://mapnik.org/
    http://matplotlib.sourceforge.net/matplotlib.toolkits.basemap.basemap.html

  Note that the python imaging library (PIL) Image object is the principal object
  created and manipulated throughout the WMS module func.. However, there are
  limitations with its ability to handle large files, like the BMNG 2km and 500m
  resolution datasets. One potential alernative to PIL is the python bindings of
  VIPS:

    http://www.vips.ecs.soton.ac.uk  

  More information about (and links to) open source mapping software and datasets
  can be found in G3WebMapServiceIssuesAndInfolinks.html.
  """
  OGCREST.WMSModPyHandler(req)
  return

def wmsc8km(req): # pre-loads 8km 'bufferedImages' BMNG input data
  """
  Handles WMSC requests with pre-loaded/buffered 8km BMNG input data.
  """
  OGCREST.WMS8kmModPyHandler(req)
  return

def wmsc2km8km(req): # pre-loads 2km and 8km 'bufferedImages'
  """
  Handles WMSC requests with pre-loaded/buffered 2km and 8km BMNG input data.
  """
  OGCREST.WMS2km8kmModPyHandler(req)
  return

def wmsc500m(req): # pre-loads 500m 8 sector/quad. 'bufferedImages' 
  """
  Handles WMSC requests with pre-loaded/buffered 500m and 2km and 8km BMNG input data.
  """
  OGCREST.WMS500mModPyHandler(req)
  return
