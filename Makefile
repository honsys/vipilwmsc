SHELL := /bin/tcsh -f

HOST := $(shell hostname)

ifndef PYINSTALL
# PYINSTALL := /devstore
  PYINSTALL := $(shell which python | sed 's/\/bin\/python//g')
endif
ifndef HTINSTALL
# HTINSTALL := /devstore
  HTINSTALL := $(shell which httpd | sed 's/\/bin\/httpd//g')
endif

# override this via make PKGREL=9x or via env. var.
ifndef PKGREL
# PKGREL := 98
  PKGREL := 95
endif

# override this via make CACHEDIR='pngcache' or via env. var.
ifndef CACHEDIR
  CACHEDIR := pngcache
# CACHEDIR := imgcache
# CACHEDIR := scratch/imgcache
endif

PYSRC = wmscgiovanni.py VIPILTest.py \
        Raster.py FileKeyUtils.py GeoImage.py GeoProj.py OGCREST.py PILMemCache.py ProcUtils.py
PYC := $(patsubst %.py, %.pyc, $(PYSRC))
PYMOD := $(patsubst %.py, %, $(PYSRC))

OPNLAYRS := OpenLayers/lib OpenLayers/art OpenLayers/img OpenLayers/tools OpenLayers/theme OpenLayers/examples
HTTPCONF := httpd.conf$(PKGREL)
HTTPDOC := $(HTINSTALL)/htdocs$(PKGREL)
HTTPLOG := $(HTINSTALL)/logs$(PKGREL)
WMSDIR := $(HTTPDOC)/wmsc
PYLIB := $(PYINSTALL)/lib/python2.5/site-packages
ifeq ($(HOST),honsys)
  PYLIB := $(PYINSTALL)/lib/python2.4/site-packages
endif
PYPKG := $(PYLIB)/G3WMS$(PKGREL)
PYWMS := wmscgiovanni.py

#HTML := WMSC700x500.html WMSNorthPole.html  WMSSouthPole.html

HTML := WMSC700x500.html

RM := /bin/rm -rf

all: doc
	@echo 'made all docs ...'

doc: clean doxydoc pytxtdoc
	@echo made doxygen html docs. and python pydoc txt.
	@echo use \'uninstall\' targets with env. PKGREL == 98,99,88,etc. to uninstall':' $(PYPKG)

showenv:
	@echo PYINSTALL == $(PYINSTALL)
	@echo PKGREL == $(PKGREL)
	@echo HTTPDOC == $(HTTPDOC)
	@echo HTTPCONF == $(HTTPCONF)
	@echo WMSDIR == $(WMSDIR)
#	@echo PYLIB == $(PYLIB)
	@echo PYPKG == $(PYPKG)
	@echo PYWMS == $(PYWMS)

doxydoc:
	doxygen doxy.conf

pytxtdoc:
	$(foreach m, $(PYMOD), python -c 'import $m ; help("$m")' >> docs/Pydoc.txt;)
# note the following assume each module provides printInfoDoc()
#	$(foreach m, $(PYMOD), python -c 'from $m import * ; printInfoDoc() ' >> docs/Pydoc.txt;)

clean:
	-$(RM) *.pyc .docs
	-mv docs .docs

realclean: clean uninstall
	@echo 'all scrubbed...'

editme:
	-sed 's^EditMePkgRel^$(PKGREL)^g' < .OGCREST.py > OGCREST.py
	-sed 's^EditMePNGCacheDir^$(CACHEDIR)^g' < .FileKeyUtils.py > FileKeyUtils.py

g3wms: editme pytxtdoc uninstall
	-@mkdir -p $(PYPKG)
	-@chmod +x $(PYSRC) $(PYC)
#	-cp -pf $(PYSRC) $(PYC) $(PYPKG)
	-cp -pf $(PYSRC) $(PYPKG)
	-touch $(PYPKG)/__init__.py
	-@chmod -R ug+rwx $(PYPKG)

http:
	-@mkdir -p $(WMSDIR) $(HTTPLOG)
ifeq ($(HOST),gdev) 
	-sed 's/usr\/local/devstore/g' < .httpd.conf00 > .$(HTTPCONF)
else
	-@cp -pf .httpd.conf00 .$(HTTPCONF)
endif
	-sed 's/00/$(PKGREL)/g' < .$(HTTPCONF) > $(HTTPCONF)
	-sed 's/User hon/User $(USER)/g' < $(HTTPCONF) > .$(HTTPCONF) 
	-sed 's/Group elston/Group $(GROUP)/g' < .$(HTTPCONF) > $(HTTPCONF)
	-cp -pf $(HTTPCONF) $(HTINSTALL)/conf/ ; $(RM) .$(HTTPCONF)
	-pushd $(HTTPDOC) ; $(foreach i, $(OPNLAYRS), ln -s ../$i;) ; popd

install: doc g3wms http
	-sed 's/G3WMS/G3WMS$(PKGREL)/g' < $(PYWMS) > $(WMSDIR)/$(PYWMS)
ifeq ($(HOST),gdev) 
	$(foreach i, $(HTML), sed 's/hon00:0000/$(HOST).sci.gsfc.nasa.gov:$(PKGREL)$(PKGREL)/g' < $i > $(HTTPDOC)/$i;)
else
	$(foreach i, $(HTML), sed 's/hon00:0000/$(HOST):$(PKGREL)$(PKGREL)/g' < $i > $(HTTPDOC)/$i;)
endif
	@echo installed $(PYPKG) and $(HTTPDOC) and $(HTTPCONF) and $(WMSDIR)

uninstall:
	-$(RM) $(PYPKG) $(HTTPDOC)
