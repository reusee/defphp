# coding: utf8

def init(M):
  M['defaults'] = {}
  def setdefault(name):
    M.setdefault(name, M['defaults'][name]())
  M.hook('set default', setdefault)
