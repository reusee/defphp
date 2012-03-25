# coding: utf8

from shutil import copytree
import os

def init(M):
  def oauth_generate():
    lib_dir = os.path.join(M['output_dir'], 'lib')
    if not os.path.exists(lib_dir):
      os.mkdir(lib_dir)
    copytree(os.path.join(M['framework_dir'], 'modules', 'oauth'),
      os.path.join(lib_dir, 'oauth'))
  M.program(0, oauth_generate)
