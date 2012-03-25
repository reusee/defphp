# coding: utf8

import sys, os
from utils import *
import traceback

class Machine(dict):
  def __init__(self, **init_args):
    self.update(init_args)
    self.update({
      'setup_modules': set(),
    })
    self.hooks = {}
    self.logs = []
    self.log('initialized')

  def log(self, s):
    self.logs.append(s)

  def dump(self):
    return '\n'.join(self.logs)

  def boot(self):
    self.log('booting')
    i = 0
    while i < len(self['program']):
      j = 0
      while j < len(self['program'][i]):
        p = self['program'][i][j]
        info('running %s <%s>' % (color('program', GREEN), p.func_name))
        try:
          self.log('start running <%s>' % p.func_name)
          p()
          self.log('end running <%s>' % p.func_name)
          for k in self.keys():
            if k.startswith('var '):
              del self[k]
        except NodeException, e:
          self.call('exception node', e)
          sys.exit(-1)
        except RunException, e:
          self.call('exception', e)
          sys.exit(-1)
        except Exceptions, e:
          self.call('exceptions', e)
          sys.exit(-1)
        j += 1
      i += 1
    with open(os.path.join(self['framework_dir'], 'log'), 'w') as f:
      f.write(self.dump())

  def setup(self, *names):
    for name in names:
      if name in self['setup_modules']:
        return
      try:
        info('setuping %s <%s>' % (color('module', GREEN), name))
        self.log('start setuping <%s>' % name)
        __import__(name)
        self.log('end setuping <%s>' % name)
      except ImportError:
        error('module <%s> not found' % name)
        self.log('module <%s> not found' % name)
      self['setup_modules'].add(name)
      try:
        self.log('start init')
        self['var current module'] = name
        getattr(sys.modules[name], 'init')(self)
        self.log('end init')
      except AttributeError:
        pass

  def check_deps(self, *deps):
    for dep in deps:
      if dep not in self['setup_modules']:
        raise RunException('module %s depend on %s' % (
          self['var current module'], dep))

  def program(self, level, func):
    try:
      self['program'][level].append(func)
    except IndexError:
      for i in xrange(level - len(self['program']) + 1):
        self['program'].append([])
      self['program'][level].append(func)
    self.log('add program <%s> to level <%d>' % (func.func_name, level))

  def hook(self, name, func):
    if name not in self.hooks:
      self.hooks[name] = []
    self.hooks[name].append(func)
    self.log('add hook <%s> to <%s>' % (func.func_name, name))

  def call(self, name, *args, **kwargs):
    try:
      for func in self.hooks[name]:
        self.log('start calling <%s> at hook <%s>' % (
          func.func_name, name))
        ret = func(*args, **kwargs)
        self.log('end calling <%s> at hook <%s>' % (
          func.func_name, name))
        return ret
    except KeyError:
      raise RunException('hook <%s> does not exist' % name)

  def has_hook(self, name):
    return name in self.hooks

  def __getitem__(self, k):
    source_file, lineno, funcname, code = traceback.extract_stack(limit = 2)[0]
    self.log('get item <%s> in function %s at file %s line %s' % (
      k, funcname, source_file, lineno))
    return dict.__getitem__(self, k)

  def __setitem__(self, k, v):
    source_file, lineno, funcname, code = traceback.extract_stack(limit = 2)[0]
    self.log('set item <%s> to <%s> in function %s at file %s line %s' % (
      k, repr(v), funcname, source_file, lineno))
    return dict.__setitem__(self, k, v)
