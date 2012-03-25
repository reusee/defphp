# coding: utf8

import sys, os

def init(M):
  sys.path.insert(0, os.path.join(M['framework_dir'], 'modules'))
  def load_modules():
    if 'import' in M['node dict']:
      for node in M['node dict']['import']:
        node.match('_ **names')
        for name in node.names:
          M.setup(name['value'])
      del M['node dict']['import']
  M.program(0, load_modules)
  M.hook('load modules', load_modules)
