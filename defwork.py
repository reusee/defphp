#!/usr/bin/env python2
# coding: utf8

import os,sys
from machine import Machine

def main():
  if len(sys.argv) != 3:
    print 'usage: %s [input_directory] [output_directory]' % (
      sys.argv[0])
    sys.exit()

  input_dir = os.path.abspath(sys.argv[1])
  output_dir = os.path.abspath(sys.argv[2])
  os.path.exists(output_dir) or os.mkdir(output_dir)

  framework_dir = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), __file__)))
  os.chdir(framework_dir)

  m = Machine(
    input_dir = input_dir,
    output_dir = output_dir,
    framework_dir = framework_dir,
    program = [],
  )
  m.setup(
    'defaults',
    'exception',
    'parse',
    'modules',
    'php_backend',
    'php_view',
    'macro',
    'global_command',
    'guard',
    'handler',
    'view',
    'generate',
  )
  m.boot()

if __name__ == '__main__':
  main()
