# coding: utf8

from shutil import copytree
import os

def init(M):
  M.call('read def', os.path.join(M['framework_dir'], 'modules', 'securimage.def'))

  def generate_secureimage():
    copytree(os.path.join(M['framework_dir'], 'modules', 'securimage'),
      os.path.join(M['output_dir'], 'lib', 'securimage'))
  M.program(0, generate_secureimage)
