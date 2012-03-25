# coding: utf8

from utils import *
from shutil import copyfile
import os

def init(M):
  M.check_deps('macro')

  def form_generate_program():
    copyfile(os.path.join(M['framework_dir'], 'modules', 'jquery.cookie.js'),
      os.path.join(M['output_dir'], 'js', 'jquery.cookie.js'))
    copyfile(os.path.join(M['framework_dir'], 'modules', 'jquery.autosave.js'),
      os.path.join(M['output_dir'], 'js', 'jquery.autosave.js'))
    M['before_boot'].append('''function validate_error($name, $message) {
  isset($_SESSION['validation_info'][$name]) or $_SESSION['validation_info'][$name] = array();
  $_SESSION['validation_info'][$name][] = $message;
}''')
  M.program(0, form_generate_program)

  def form(node): 
    node.match('_ *&form_name **cmds')
    for cmd in node.cmds:
      if cmd['value'] == 'template':
        template_nodes = cmd['children']
        def _f(command_node, indent): # 展开并解释
          command_node.match('_ *redirect')
          if not hasattr(command_node, 'redirect'):
            raise NodeException(command_node, 'form <%s> need a redirect target' % node.form_name)
          nodes = M.call('expand nodes', template_nodes, 'tpl_macro', [command_node])
          return ''.join(M.call('template node', x, indent) for x in nodes)
        M.hook('template command form.%s' % node.form_name, _f)
      elif cmd['value'] == 'handler':
        # 应对照handler模块的interpret_handlers来实现，因为需要修改program参数
        M['handler_type'][node.form_name] = 'request'
        handler = {
          'process': [],
          'namespace': os.path.basename(
            node['file'].split('.')[0]),
          'name': node.form_name,
        }
        handler['process'].append(('code', '''\
  //开始验证
  $_SESSION['validation_info'] = array();
''')) # 验证之前的代码 todo
        cmd['children'] = M.call('expand nodes', cmd['children'], 'hdlr_macro')
        M.call('interpret handler nodes', handler, cmd['children'])
        handler['process'].append(('code', '''\
  if (!empty($_SESSION['validation_info'])) {
    $redirect = '%(form_name)s';
    if (isset($_POST['redirect']) && valid_path($_POST['redirect'])) {
      $redirect = $_POST['redirect'];
    }
    context('redirect', call_user_func(context('pather'), $redirect) . '&haserror=1');
  }
  else {
    context('validation pass', true);
  }
  //结束验证
''' % {'form_name': node.form_name})) # 验证之后的代码 todo
        M.setdefault('handlers', {})
        M['handlers'][node.form_name] = handler
      else:
        warn('unknown command %s in form %s' % (
          cmd['value'], node.form_name))
  M.hook('global command form', form)

  # === validation ===
  def validate_command(node, handler):
    node.match('_ *&message *targets *&validator **args')
    targets = [x['value'] for x in node.targets.to_list()]
    ret = [M.call('validator %s' % node.validator,
      '$_POST', target, node)
      for target in targets]
    handler['process'] += [('code', code)
      for code in ret]
  M.hook('handler command validate', validate_command)

  def gen_restriction_code(restriction, name, message):
    return '''if (!(%(restriction)s)) {
    validate_error('%(name)s', '%(message)s');
  }''' % {
    'restriction': restriction,
    'name': name,
    'message': message,}

  # --- restriction ---
  def _required(array, key, node):
    return gen_restriction_code(
      '''isset(%(array)s['%(key)s']) && !empty(%(array)s['%(key)s'])''' % {
        'array': array, 'key': key },
      key, node.message)
  M.hook('validator required', _required)

  def _max_length(array, key, node):
    return gen_restriction_code(
      '''mb_strlen(%(array)s['%(key)s'], 'utf-8') <= %(length)s''' % {
        'array': array, 'key': key, 'length':
        node.args[0]['value']},
      key, node.message)
  M.hook('validator max_length', _max_length)

  def _min_length(array, key, node):
    return gen_restriction_code(
      '''mb_strlen(%(array)s['%(key)s'], 'utf-8') >= %(length)s''' % {
        'array': array, 'key': key, 'length':
        node.args[0]['value']},
      key, node.message)
  M.hook('validator min_length', _min_length)

  def _length(array, key, node):
    return gen_restriction_code(
      '''mb_strlen(%(array)s['%(key)s'], 'utf-8') == %(length)s''' % {
        'array': array, 'key': key, 'length':
        node.args[0]['value']},
      key, node.message)
  M.hook('validator length', _length)

  def _equal(array, key, node):
    return gen_restriction_code(
      '''%(array)s['%(key)s'] === %(array)s['%(arg)s']''' % {
        'array': array, 'key': key, 'arg': node.args[0]['value']},
      key, node.message)
  M.hook('validator equal', _equal)

  def _match(array, key, node):
    pattern = node.args[0]['value']
    if not pattern.startswith('/'):
      pattern = '/%s/' % pattern
    return gen_restriction_code(
      '''preg_match('%(pattern)s', %(array)s['%(key)s'])''' % {
        'array': array, 'key': key, 'pattern': pattern},
      key, node.message)
  M.hook('validator match', _match)

  def _in(array, key, node):
    values = ', '.join(M.call('node repr', x)
      for x in node.args)
    return gen_restriction_code(
      '''isset(%(array)s['%(key)s']) && in_array(%(array)s['%(key)s'], array(%(values)s))''' % {
        'array': array, 'key': key, 'values': values},
      key, node.message)
  M.hook('validator in', _in)

  def _email(array, key, node):
    return gen_restriction_code(
      '''filter_var(%(array)s['%(key)s'], FILTER_VALIDATE_EMAIL)''' % {
        'array': array, 'key': key},
      key, node.message)
  M.hook('validator email', _email)

  def _url(array, key, node):
    return '''\
  $url = %(array)s['%(key)s'];
  $l = mb_strlen($url, 'utf-8');
  if ($l !== strlen($url)) {
    $s = str_repeat(' ', $l);
    for ($i = 0; $i < $l; ++$i) {
      $ch = mb_substr($url, $i, 1, 'utf-8');
      $s[$i] = strlen($ch) > 1 ? 'X' : $ch;
    }
    $url = $s;
  }
  ''' % { 'array': array, 'key': key,
      } + gen_restriction_code(
      '''filter_var($url, FILTER_VALIDATE_URL)''',
      key, node.message)
  M.hook('validator url', _url)

  # --- purifier ---
  def _bool(array, key, node):
    return array
  M.hook('validator bool', _bool)

  def _date(array, key, node):
    return array
  M.hook('validator date', _date)

  def _int(array, key, node):
    return array
  M.hook('validator int', _int)

  def _float(array, key, node):
    return array
  M.hook('validator float', _float)
