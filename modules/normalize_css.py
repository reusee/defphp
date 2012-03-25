from shutil import copyfile
import os

def init(M):
  def normalizecss_generate():
    copyfile(os.path.join(M['framework_dir'], 'modules', 'normalize.css'),
      os.path.join(M['output_dir'], 'css', 'normalize.css'))
  M.program(0, normalizecss_generate)

  def command(node, indent):
    return ' ' * M['tabstop'] * indent +\
      '<link rel="stylesheet" href="css/normalize.css" />'
  M.hook('template command normalize_css', command)
    
