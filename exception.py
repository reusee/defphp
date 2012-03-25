# coding: utf8

from utils import *
import traceback

def init(M):
  def exception_node(e):
    node = e.node
    print '%s at file %s line %s: %s' % (
      color('NodeException', RED),
      color(node['file'] if 'file' in node else '-', YELLOW),
      color(node['lineno'] if 'lineno' in node else '-', YELLOW),
      color(e.msg, GREEN),
      )
    M.log('<%s> at file <%s> line <%s>: <%s>' % (
      'NodeException',
      node['file'] if 'file' in node else '-',
      node['lineno'] if 'lineno' in node else '-',
      e.msg))
  M.hook('exception node', exception_node)

  def exception(e):
    print '%s: %s' % (
      color('RunException', RED),
      e.msg)
    M.log('<%s>: <%s>' % (
      'RunException',
      e.msg))
  M.hook('exception', exception)

  def exceptions(e):
    for exception in e.exceptions:
      if isinstance(exception, RunException):
        M.call('exception', exception)
      elif isinstance(exception, NodeException):
        M.call('exception node', exception)
  M.hook('exceptions', exceptions)
