# coding: utf8

from shutil import copytree
import os

def init(M):
  M.check_deps('jquery')

  M.call('read def', os.path.join(M['framework_dir'], 'modules', 
    'jquery_validation.def'))

  def jquery_validation_generate():
    js_dir = os.path.join(M['output_dir'], 'js')
    copytree(os.path.join(M['framework_dir'], 'modules', 'jquery-validation'),
      os.path.join(js_dir, 'jquery-validation'))
  M.program(0, jquery_validation_generate)
