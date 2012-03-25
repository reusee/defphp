#!/usr/bin/env python2
# coding: utf8

import pyinotify
import functools
import sys, os
from datetime import datetime

class OnWriteHandler(pyinotify.ProcessEvent):
  def my_init(self, input_directory, output_directory):
    self.input_directory = input_directory
    self.output_directory = output_directory
    self.count = 0
    self.untrack = ['.pyc']
  def process_default(self, event):
    if any([event.pathname.endswith(x) for x in self.untrack]):
      return

    self.count += 1
    t1 = datetime.now()
    print '=' * 10, '\033[1;33;40mgeneration %d\033[0m' % self.count, '=' * 10
    print '\033[1;33;40mchanged\033[0m', event.pathname
    ret = os.system('%s%sdefwork.py %s %s' % (
      os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), __file__))),
      os.sep,
      input_directory,
      output_directory))
    if ret == 0:
      print '\033[1;32;40m-' * 10, ' >_< ', '-' * 10, '\033[0m'
    print '\033[1;33;40musing\033[0m %.2fs' % (datetime.now() - t1).total_seconds()
    print

if len(sys.argv) != 3:
  print 'usage: %s [input_directory] [output_directory]' % (
    sys.argv[0])
  sys.exit()
input_directory = sys.argv[1]
output_directory = sys.argv[2]
print input_directory, output_directory

wm = pyinotify.WatchManager()
handler = OnWriteHandler(input_directory = input_directory,
  output_directory = output_directory)
notifier = pyinotify.Notifier(wm, default_proc_fun=handler)
wm.add_watch(input_directory, 
  #pyinotify.ALL_EVENTS,
  pyinotify.IN_CLOSE_WRITE
  |pyinotify.IN_MOVED_FROM
  |pyinotify.IN_DELETE,
  rec=True, auto_add=True)
#wm.add_watch(os.getcwd(), 
#  #pyinotify.ALL_EVENTS,
#  pyinotify.IN_CLOSE_WRITE
#  |pyinotify.IN_MOVED_FROM
#  |pyinotify.IN_DELETE,
#  rec=True, auto_add=True)

notifier.loop(daemon = True)
