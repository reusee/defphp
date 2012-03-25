from shutil import copyfile
import os
from utils import *

def init(M):
  def redbean_generate():
    copyfile(os.path.join(M['framework_dir'], 'modules', 'rb.php'),
      os.path.join(M['output_dir'], 'lib', 'rb.php'))
    M.call('set default', 'before_boot_includes')
    M['before_boot_includes']['lib/rb.php'] = True
  M.program(0, redbean_generate)

  def rb_setup(node):
    node.match('_ *&host *&user *&password *&database')
    M.setdefault('before_boot', [])
    M['before_boot'].append('R::setup("mysql:host=%s;dbname=%s", "%s", "%s");' % (
      node.host, node.database, node.user, node.password))
  M.hook('global command rb_setup', rb_setup)

  def fuse_command(node):
    M.setdefault('fuse', {})
    node.match('_ *&model **actions')
    M['fuse'].setdefault(node.model, {})
    for action in node.actions:
      M['fuse'][node.model][action['value']] = action['children'][0]['value']
  M.hook('global command fuse', fuse_command)

  def fuse_generate():
    if not 'fuse' in M: return
    ret = ['<?php defined("ENTRANCE") or die("Deny");']
    for model in M['fuse']:
      ret.append('class Model_%s extends RedBean_SimpleModel {' % (
        model.capitalize()))
      for action in M['fuse'][model]:
        ret.append('public function %s() {' % action)
        ret.append(M['fuse'][model][action].strip())
        ret.append('}')
      ret.append('}')
    ret.append('?>')
    with open(os.path.join(M['output_dir'], 'fuse.php'), 'w') as f:
      f.write('\n'.join(ret))
    M.call('set default', 'before_boot_includes')
    M['before_boot_includes']['fuse.php'] = True
  M.program(1, fuse_generate)
