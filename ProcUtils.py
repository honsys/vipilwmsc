#!/bin/env python
svnUrl = '$HeadURL: svn+ssh://hon@honsys.com/var/svnroot/ogcwms/trunk/pydocs/ProcUtils.py $'
svnId = rcsId = '$Name$ $Id: ProcUtils.py 24 2008-04-01 06:19:16Z hon $'
#
#"""@package docstring
__doc__ = _modinfo = \
"""
The ProcUtils module provides functions that support external daemon management,
specifically the memcached and the httpd. The unit test main can be used to
to (re)start and/or monitor memory utilization of the external daemons; and
a signal handler is provided to allow the memory monitor to run as an interruptable
daemon.
"""
#
import copy, errno, os, signal, socket, sys, time, subprocess
# note that both GeoImage and Raster now import vipsCC
# evidently vipsCC pops sys.argv! so first make a deep
# copy of it and restore it!
_argv = copy.deepcopy(sys.argv)

#import G3WMS.FileKeyUtils as FileKeyUtils
import FileKeyUtils


# globals:
_terminate = False
_interruptcnt = 0

def sighandler(signum, frame):
  """
  Interrupt handler allows suspension via SIGHUP and resumption via SIGCONT;
  and termination via SIGABRT, SIGINT, and/or preferably SIGTERM. 
  """
  global _terminate
  global _interruptcnt
  print >> FileKeyUtils.WMSlog, 'sighandler> ', signum
  ++_interruptcnt 
  if signum in(signal.SIGABRT, signal.SIGINT, signal.SIGTERM):
    print >> FileKeyUtils.WMSlog, 'sighandler> terminate pid: ', os.getpid(), signum
    _terminate = True
  elif signum in(signal.SIGHUP, signal.SIGTSTP):
    print >> FileKeyUtils.WMSlog, 'sighandler> suspend/stop/pause pid: ', os.getpid(), signum
    signal.pause()
  else:
    print >> FileKeyUtils.WMSlog, 'sighandler> resume/continue pid: ', os.getpid(), signum
    _terminate = False
# sys.stdout.write("exit? [y]: ")
# rep = "y"; rep = sys.stdin.readline(); rep = rep.strip()
# if len(rep) == 0 or rep == "y" :
#   print >> FileKeyUtils.WMSlog, "reply == "+rep
#   _terminate = True
#   sys.exit()
#end sighandler

def signals():
  """
  Establishes signal handler and returns hash dict. of signal names of interest.
  """
  sigdict = {'SIGABRT':'should cause (graceful) daemon exit', 'SIGCONT':'should cause daemon resume/continue after SIGHUP',
             'SIGHUP':'should suspend/pause daemon', 'SIGINT':'should cause (graceful) daemon exit',
             'SIGTERM':'should cause (graceful) daemon exit'}
  signal.signal(signal.SIGABRT, sighandler) 
  signal.signal(signal.SIGCONT, sighandler)
  signal.signal(signal.SIGHUP, sighandler)
  signal.signal(signal.SIGINT, sighandler)
  signal.signal(signal.SIGTERM, sighandler)
# signal.signal(signal.SIGTSTP, sighandler) ignore this for now to allow shell jobs
# print >> FileKeyUtils.WMSlog, sigdict
  return sigdict

def restartMemCached():
  """
  Uses os.system() to pkill and then starts 3 specific memcached procs. via the following:
  latlon projection tiles:    memcached -d -k -m 2048 -l 127.0.0.1 -p 11110
  north polar stereographic:  memcached -d -k -m 2048 -l 127.0.0.1 -p 11111
  south polar stereographic:  memcached -d -k -m 2048 -l 127.0.0.1 -p 11112
  """
  memcd0 = 'memcached -d -k -m 2048 -l 127.0.0.1 -p 11110 > /dev/null 2>&1' # send stdout and stderr to /dev/null
# memcd0 = 'memcached -d -k -M -m 2048 -l 127.0.0.1 -p 11110 > /dev/null 2>&1'
# memcd0 = 'memcached-debug -vv -k -M -m 2048 -l 127.0.0.1 -p 11110'
# os.system(memcd1)
  memcd1 = 'memcached -d -k -m 2048 -l 127.0.0.1 -p 11111 > /dev/null 2>&1'
# memcd1 = 'memcached -d -k -M -m 2048 -l 127.0.0.1 -p 11111 > /dev/null 2>&1'
# memcd1 = 'memcached-debug -vv -k -M -m 2048 -l 127.0.0.1 -p 11111 > /dev/null 2>&1'
  memcd2 = 'memcached -d -k -m 2048 -l 127.0.0.1 -p 11112 > /dev/null 2>&1'
# memcd2 = 'memcached -d -k -M -m 2048 -l 127.0.0.1 -p 11112 > /dev/null 2>&1'
# memcd2 = 'memcached-debug -vv -k -M -m 2048 -l 127.0.0.1 -p 11112 > /dev/null 2>&1'
  memcd = [memcd0, memcd1, memcd2]
  os.system('pkill memcached > /dev/null 2>&1') # kill any exisiting memcached?
  for cmd in memcd:
    os.system(cmd) # insure memcacheds are up, harmle
#end restartMemCached

def pidHTTPd(htconf):
  """
  Returns the parent pid of the process group associated with the Apache httpd web server
  running with the indicated config: httpd.conf90 or httpd.conf98 or httpd.conf99, etc.
  """
# pcmd = "/bin/ps -ef|/bin/grep " + htconf + "|/bin/grep -v grep|/bin/awk '{print $3}'|sort -u"
# pcmd = '/bin/ps -ef'
# pcmd = 'ps -eo pid,ppid,rss,vsize,pcpu,pmem,cmd -ww --sort=pid'
  pcmd = 'ps -eo pid,ppid,rss,cmd'
# produces something like the following (when selecting htconf == httpd.conf99)
#30645     1 4420 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30646 30645 1640 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30647 30645 2628 /devstore/apache2/bin/fcgi- -f /devstore/apache2/conf/httpd.conf99
#30648 30645 37216 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30649 30645 3064 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30650 30645 3064 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30651 30645 3064 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30652 30645 3064 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
#30656 30645 3064 /devstore/apache2/bin/httpd -f /devstore/apache2/conf/httpd.conf99
# the 3rd column is ram util. in units of kbytes, kill the entire set of httpd pids
# (by killing parent proc) if any one thread exceeds 1,000,000 kbytes (> 1gb)
  pid = os.popen(pcmd, "r")
  ppids = [] ; pids = [] ; memuse = [] ; vals = [] 
  parentpid = -1
  restart = False
  try:
    for p in pid.xreadlines():
      p.rstrip()
      vals = p.split()
      conf = vals[-1] # last val should be confile
      try:
        if conf.index(htconf) >= 0 :
          pids.append(int(vals[0]))
          ppids.append(int(vals[1]))
          memuse.append(int(vals[2])) 
#         print >> FileKeyUtils.WMSlog, 'pidHTTPd> pids: ', pids, ', ppids: ', ppids, ' memuse: ', memuse
          if int(vals[1]) == 1 : parentpid = int(vals[0])
          if int(vals[2]) > 1000000 : restart = True
      except:
#       print >> FileKeyUtils.WMSlog, 'pidHTTPd> vals: ', vals
        pass
  except: pass

  print >> FileKeyUtils.WMSlog, 'pidHTTPd>', htconf, ' parentpid:', parentpid, ', memuse:', memuse
  if restart: # return parentpid
    return parentpid

  return -1

def restartHTTPd(htconf):
  """
  Uses os.system() to pkill and then invokes the Apache httpd with the specified
  config: httpd.conf90 or httpd.conf98 or httpd.conf99, etc.
  """
  parentpid = pidHTTPd(htconf)
  if parentpid <= 1:
    return
# hopefulle killing the parent proc. will do the trick
  print >> FileKeyUtils.WMSlog, 'restartHTTPd> kill parentpid:', parentpid
  os.system('kill -TERM '+repr(parentpid))
  apache = '/devstore/apache2/bin/httpd -f /devstore/apache2/conf/' + htconf
  print >> FileKeyUtils.WMSlog, 'restartHTTPd> via:', apache
  time.sleep(0.5) # give it time to complete proc. termination
  os.system('/devstore/apache2/bin/httpd -f /devstore/apache2/conf/' + htconf)
#end restartHTTPd

def printInfoDoc():
  """
  Printout global _modinfo text, followed by module help().
  """
  global _modinfo
  print _modinfo
  help("ProcUtils")

if __name__ ==  '__main__' :
  """
  The unit test main can be used to (re)start the memcahed and the apache httpd. The
  httpd can also be monitored for memory utilization and restarted if it grows too
  large. A signal handler is provided to allow the memory monitor to run as an interruptable
  daemon.
  """
# global _terminate
  arg = app = _argv.pop(0)
  host = socket.gethostname()
  FileKeyUtils.openWMSlog(logfile='/devstore/apache2/logs/WMSmonitor.log')
  print >> FileKeyUtils.WMSlog, "host= "+host+", argv0= "+arg

  ldpath = os.getenv("LD_LIBRARY_PATH")
  if (ldpath == None) :
    print >> FileKeyUtils.WMSlog, "LD_LIBRARY_PATH is not defined..."
#   sys.exit()
#end if
# print >> FileKeyUtils.WMSlog, "ldpath= "+ldpath

  pypath = os.getenv("PYTHONPATH")
  if (pypath == None) :
    print >> FileKeyUtils.WMSlog, "PYTHONPATH is not defined..."
#   sys.exit()
#end if
#  print >> FileKeyUtils.WMSlog, "pypath= "+pypath
  if len(_argv) > 0:
   arg = _argv[0]
   if arg in ('-memrun', '-runmem', '-memkill', '-killmem'):
     restartMemCached()
     FileKeyUtils.closeWMSlog()
     sys.exit(0)

  print >> FileKeyUtils.WMSlog, 'manageHTTPd> pid:', os.getpid()
  for key, val in signals().items():
    print >> FileKeyUtils.WMSlog, 'ProcUtils>', key, val

  slp = 10.0
  if len(_argv) > 0 :
    slp = float(_argv.pop(0))

  print >> FileKeyUtils.WMSlog, 'ProcUtils> check mem. usage every:', slp, 'sec. ...'

  while _terminate == False:
    restartHTTPd('httpd.conf99')
    restartHTTPd('httpd.conf90')
    time.sleep(30.0)

  FileKeyUtils.closeWMSlog()
