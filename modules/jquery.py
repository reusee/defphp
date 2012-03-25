from shutil import copyfile
import os

def init(M):
  M.call('read def', os.path.join(M['framework_dir'], 'modules',
    'jquery.def'))

  def jquery_generate():
    copyfile(os.path.join(M['framework_dir'], 'modules', 'jquery.js'),
      os.path.join(M['output_dir'], 'js', 'jquery.js'))
  M.program(0, jquery_generate)
