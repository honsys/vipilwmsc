#!/bin/csh -f
# please note this has not been tested and may very well have typos and/or cut-and-paste errors
# from my savehist session(s)
# install all python modules (under /devstore/lib/python2.5/site-packages)
wget -nd http://www.python.org/ftp/python/2.5.1/Python-2.5.1.tar.bz2
tar xjvf Python-2.5.1.tar.bz2
pushd Python-2.5.1 
./configure --enable-shared --with-signal-module
make; make install # under /devstore
popd ; rehash
wget -nd http://peak.telecommunity.com/dist/ez_setup.py
python ez_setup.py ; rehash
easy_install scons # a python build tool, required to build mapnik
easy_install jonpy # mapnik's 'ogcserver' uses this fastcgi module
easy_install flup # tilecache uses this with Paste in its fastcgi rendition
easy_install Paste
easy_install TileCache
easy_install lxml # sometimes fails, but is not all that necessary
easy_install numpy # many packages rely on this, although pyhdf relies on the older Numeric
#easy_install Numeric fails
# follow the link here http://people.csail.mit.edu/jrennie/python/numeric/ to sourceforge download
tar zxvf Numeric-24.2.tar.gz
pushd Numeric-24.2
python setup.py build; python setup.py install
popd
#easy_install matplotlib seems to install an outdated version, deal with this further below
#easy_install PIL fails, but the old fashion python setp.py build install works..
wget -nd http://effbot.org/downloads/Imaging-1.1.6.tar.gz
python setup.py build
python setup.py install
popd
# ok that should provide the required python environmenmt
# I'm not sure how to use wget with sourceforge, but now that python
# has been setup, we can try to use its urllib module to retireve items from sourceforge...
# this provides an allegedly faster alternative to mod_python as well as fastcgi:
python -c 'from urllib import *; urlretrieve("http://sourceforge.net/project/downloading.php?groupname=webware&filename=Webware-0.9.4.tar.gz","Webware-0.9.4.tar.gz")'
tar xzvf Webware-0.9.4.tar.gz
pushd Webware-0.9.4
python setup.py build ; python setup.py install
popd
#
# if fully successful, the above should provide all the needed Python requirements
# now all the other c/c+ stuff
# download the c++ boost libs:
# from http://sourceforge.net/projects/boost
python -c 'from urllib import *; urlretrieve("http://sourceforge.net/project/downloading.php?groupname=boost&filename=boost_1_34_1.tar.bz2","boost_1_34_1.tar.bz2")'
tar xjvf boost_1_34_1.tar.bz2
pushd boost_1_34_1
./configure --with-python=/devstore/bin/python ; make; make install # under /devstore
popd
wget -nd ftp://ftp.remotesensing.org/proj/proj-4.5.0.tar.gz
tar xzvf proj-4.5.0.tar.gz
pushd proj-4.5.0;./configure; make; make install # under /devstore
popd
# manually download the ogdi lib from http://sourceforge.net/projects/ogdi
python -c 'from urllib import *; urlretrieve("http://sourceforge.net/project/downloading.php?groupname=ogdi&filename=ogdi-3.1.5.tar.gz","ogdi-3.1.5.tar.gz")'
tar xzvf ogdi-3.1.5.tar.gz
pushd ogdi-3.1.5;
setenv TOPDIR `pwd`
set origldpath = $LD_LIBRARY_PATH
setenv LD_LIBRARY_PATH $TOPDIR/bin/Linux':'$LD_LIBRARY_PATH
./configure --with-projlib=/devstore/lib/libproj.so --with-projinc=/devstore/include
make; make install # under /devstore
unsetenv TOPDIR ; setenv LD_LIBRARY_PATH $origldpath
popd
wget -nd http://download.osgeo.org/gdal/gdal-1.4.2.tar.gz
tar xzvf gdal-1.4.2.tar.gz
pushd gdal-1.4.2
./configure --prefix=/devstore --without-libtool --with-ogdi --with-python
make; make install # under /devstore
popd
# fetch the latest stable release of mapnik
wget -nd http://prdownload.berlios.de/mapnik/mapnik_src-0.5.0.tar.gz
# or fetch the current source from the svn trunk:
svn co svn://svn.mapnik.org/trunk mapnik
pushd mapnik
/devstore/bin/python scons/scons BOOST_INCLUDES=/devstore/include/boost-1_34_1 BOOST_LIBS=/devstore/lib BOOST_TOOLKIT=gcc34 GDAL_INCLUDES=/devstore/include GDAL_LIBS=/devstore/lib
/devstore/bin/python scons/scons BOOST_INCLUDES=/devstore/include/boost-1_34_1 BOOST_LIBS=/devstore/lib BOOST_TOOLKIT=gcc34 GDAL_INCLUDES=/devstore/include GDAL_LIBS=/devstore/lib install
popd
# while mapnik provides superior rendering of shapefiles into the flat latlong projection
# i have been unable to get it to process PNG files (although it may handle TIFF), nor
# have i been able to get it to create polar projections
# consequently i have installed python matplotlib and its matplotlib.basemap
# 'toolkit', which does not render with quite the same quality as mapnik, but
# it supports a variety of projections as well as shapefile and PNG 'raster' inputs:
# download both from http://sourceforge.net/projects/matplotlib
# click on'browse all files and download the latest
# as of jan. 2008: basemap-0.9.9.tar.gz and matplotlib-0.91.2.tar.gz 
# matplotlib and basemap support user selection of 'back-end renderers
# these include pygtk, agg, gd, imagemagick, and more
# for the moment we can do without pygtk, but assume that agg was not installed with mapnik:
wget -nd http://www.antigrain.com/agg-2.5.tar.gz
tar zxvf agg-2.5.tar.gz
pushd agg-2.5
./configure --prefix=/devstore
make; make install
popd
# get and install the latest libgd and imagemagick then install the python modules: 
# if GD and ImageMagick are not available onder /usr/lib...
wget -nd http://www.libgd.org/releases/gd-2.0.35.tar.bz2
tar jxvf gd-2.0.35.tar.bz2
pushd gd-2.0.35
./configure --prefix=/devstore
make; make install
popd
wget -nd http://newcenturycomputers.net/projects/download.cgi/gdmodule-0.56.tar.gz
tar zxvf gdmodule-0.56.tar.gz
pushd gdmodule-0.56
python setup.py build; python setup.py install
popd
wget -nd ftp://ftp.imagemagick.org/pub/ImageMagick/ImageMagick-6.3.9-4.tar.gz
tar zxvf ImageMagick-6.3.9-4.tar.gz
pushd ImageMagick-6.3.9-4
./configure --prefix=/devstore
make; make install
popd
wget -nd http://www.imagemagick.org/download/python/PythonMagick-0.7.tar.gz
# or if there are problems with this version, the older 0.6 is still available:
# wget -nd http://www.imagemagick.org/download/python/PythonMagick-0.6.tar.gz
tar zxvf PythonMagick-0.7.tar.gz
pushd PythonMagick-0.7
python setup.py build; python setup.py install
popd
# now matplotlib and basemap can be installed:
tar zxvf matplotlib-0.91.2.tar.gz
pushd matplotlib-0.91.2
python setup.py build; python setup.py install
popd
# basemap also requires libgeos...
# basemap comes with an older version (geos-2.2.3), but try using the latest:
#wget -nd http://geos.refractions.net/downloads/geos-3.0.0.tar.bz2 # or whatever is latest
#tar jxvf geos-3.0.0.tar.bz2
#pushd geos-3.0.0
#./configure -prefix=/devstore --enable-python
#make; make install
#popd
# evidently basemape preferes its own (older) version of libgeos:
tar zxvf basemap-0.9.9.tar.gz
pushd basemap-0.9.9
setenv GEOS_DIR /devstore
pushd geos-2.2.3
./configure --prefix=$GEOS_DIR
make; make install
popd
python setup.py build; python setup.py install
popd
# next up is the apache httpd webserver configured with 
# mod_python and mod_fastcgi and plain old cgi:
# use the latest apache httpd (2.2.8 or higher) 
# the apache httpd.conf file will be provided separately
# once apache is installed (under /devstore/apache2) then download
# configure & make the fcgi and python modules 
wget -nd http://www.apache.org/dist/httpd/httpd-2.2.8.tar.bz2
tar jxvf httpd-2.2.8.tar.bz2
pushd httpd-2.2.8
./configure --prefix=/devstore/apache2.2.8 --enable-rewrite=shared --enable-speling=shared --enable-imagemap --enable-cgi --enable-cgid --enable-info --enable-version --enable-example
make ; make install
popd
# the above should have created /devstore/apache2.2.8 and I recommend creating the following sym-link:
ln -s /devstore/apache2.2.8 /devstore/apache2
wget -nd http://www.apache.org/dist/httpd/modpython/mod_python-3.3.1.tgz
pushd mod_python-3.3.1
./configure --with-apxs=/devstore/apache2.2.8/bin/apxs
make ; make install # under /devstore/apache2.2.8/modules
popd
# never got this to work:
python -c 'from urllib import *; urlretrieve("http://prdownloads.sourceforge.net/mod-fcgid/mod_fcgid.2.1.tar.gz?download","mod_fcgid.2.1.tar.gz")'
tar xzvf mod_fcgid.2.1.tar.gz
pushd mod_fcgid.2.1
make; make install # works with the provided Makefile is /devstore/apache2 exists..
popd
# however there is a newer version of the original fastcgi implementation
# that i have been able to get working:
wget -nd http://www.fastcgi.com/dist/mod_fastcgi-2.4.6.tar.gz
tar zxvf mod_fastcgi-2.4.6.tar.gz
pushd mod_fastcgi-2.4.6 # we are using apache2.x.y and this default install is /devstore/apache2
cp -p Makefile.AP2 Makefile; # edit it to change the install location
make; make install
popd
# the alternative to fastcgi is mod_python:
wget -nd http://www.trieuvan.com/apache/httpd/modpython/mod_python-3.3.1.tgz
tar zxvf mod_python-3.3.1.tgz
pushd mod_python-3.3.1
./configure --with-apxs=/devstore/apache2.2.8/bin/apxs --prefix=/devstore/apache2.2.8
make; make install
popd
# both the mod_python and the fastcgi rendition of web services can
# make use of memory caching via the memcached
# installing memcached requires first installing libevent:
wget -nd http://www.monkey.org/~provos/libevent/libevent-1.4.2-rc.tar.gz
tar zxvf libevent-1.4.2-rc.tar.gz
pushd libevent-1.4.2-rc
configure --prefix=/devstore
make; make install
popd
wget -nd http://www.danga.com/memcached/download.bml/memcached-1.2.5.tar.gz
tar zxvf memcached-1.2.5.tar.gz
pushd memcached-1.2.5
configure --prefix=/devstore
make; make install
popd
# easy_install has no knowledge of the python memcached module, so...
wget -nd ftp://ftp.tummy.com/pub/python-memcached/python-memcached-1.40.tar.gz
tar zxvf python-memcached-1.40.tar.gz
pushd python-memcached-1.40
python setup.py build; python setup.py install
popd
#
# and important item(s) below!
# may need to run ldconfig to insure that all the shared libs
# are made available to the httpd, and I can provide a local.conf file to
# place under /etc/ld.so.conf.d
#
# and equally important to all of this are the GIS 'datasource' files -- the VMAP0
# data needs to be downloaded and placed in a convenient (permanent) location
#
wget -nd http://frederic.cs.dal.ca/pub/STDW/VMAP0/DCW_Europe_North-Asia_shp.tar.gz
wget -nd http://frederic.cs.dal.ca/pub/STDW/VMAP0/DCW_North-America_shp.tar.gz
wget -nd http://frederic.cs.dal.ca/pub/STDW/VMAP0/DCW_South-America_Africa_shp.tar.gz
wget -nd http://frederic.cs.dal.ca/pub/STDW/VMAP0/DCW_South-Asia_Australia_shp.tar.gz
# and untar'd, etc.
# other data sources are listed in the docs.
#
# libVIPS:
# dependencies for libVIPS installed in this order:
# note that a dep. may reside under /usr/lib and its pkg_config
# under /usr/lib/pkgconfig -- if so, simply create a sym-link to it
# under /devstore/lib/pkgconfig ...
# pkg_config (0.23 or higher), bison, glib (2.14.6 or higher), fontconfig, freetype,
# libtiff (3.8.2 or higher), pixman, atk, cairo and pycairo (which may require libpng12), pango,
# libxml-2.x, libgtk via gtk+ (2.12.9 or higher), vips, and nip2 (gtk gui to test libvips)...
# also there may be some compiler error/complaints with the swigged vips c++ regarding
# assignment of char* var = const char* whatever -- just edit the left-had-side to: 
# const char* var = whatever
# fetch/download; untar; configure --prefix=/devstore; make; make install ... 
# http://pkgconfig.freedesktop.org/releases/
# http://www.gtk.org/download-linux.html
# atk-1.22.0.tar.bz2
# bison-2.3.tar.bz2
# cairo-1.6.4.tar.gz
# fontconfig-2.5.91.tar.gz
# freetype-2.3.5.tar.bz2
# glib-2.14.6.tar.bz2
# gtk+-2.12.9.tar.bz2
# libxml2-2.6.32.tar.gz
# nip2-7.14.3.tar.gz
# OpenLayers-2.6.tar.gz
# pango-1.18.4.tar.bz2
# pixman-0.10.0.tar.gz
# pkg-config-0.23.tar.gz
# pycairo-1.4.12.tar.gz
# tiff-3.8.2.tar.gz
# tilecache-2.02.tar.gz
# vips-7.14.3.tar.gz
