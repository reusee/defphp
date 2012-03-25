# coding: utf8

import sys, os
from utils import *

verbose = False

class NodeException():
  def __init__(self, node, msg):
    self.node = node
    self.msg = msg

class RunException():
  def __init__(self, msg):
    self.msg = msg

class Exceptions():
  def __init__(self, exceptions):
    self.exceptions = exceptions

GREY, RED, GREEN, YELLOW, BLUE, PINK, CYAN, WHITE = range(30, 38)
def color(s, color):
  return '\033[1;%d;40m%s\033[0m' % (color, str(s))

def error(s):
  print color('error:', RED), s
  sys.exit(-1)

def info(s, indent = 0):
  if verbose:
    print '%s%s %s' % (' ' * 4 * indent, color('info:', YELLOW), s)
  else:
    pass

def warn(s, indent = 0):
  if verbose:
    print '%s%s %s' % (' ' * 4 * indent, color('warn:', PINK), s)
  else:
    print '%s %s' % (color('warn:', PINK), s)

def todo(s, indent = 0):
  print '%s %s' % (color('todo:', GREEN), s)

def listfiles(directory):
  ret = []
  for root, dirs, files in os.walk(directory):
    ret += [(root, os.path.join(root, f)) for f in files]
  return ret

def gen_file(var, input_file, output_file):
  with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    content = infile.read()
    for key in var:
      content = content.replace('<<%s>>' % key, var[key])
    outfile.write(content)
