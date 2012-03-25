import os
from shutil import copytree

def init(M):
  def kint_generate():
    M['before_boot_includes'][
      os.path.join('lib', 'kint', 'Kint.class.php')] = True
    copytree(os.path.join(M['framework_dir'], 'modules', 'kint'),
      os.path.join(M['output_dir'], 'lib', 'kint'))
  M.program(1, kint_generate)
