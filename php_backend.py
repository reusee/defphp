# coding: utf8

from utils import *
import re
from collections import OrderedDict

def init(M):
  defaults = {
    'before_boot_includes': OrderedDict(),
    'functions': {},
    'backend_dir': 'php_core',
  }
  for k in defaults:
    M.setdefault(k, defaults[k])
  M['defaults']['before_boot_includes'] = OrderedDict

  def global_command_function(node):
    namespace =  os.path.basename(node['file']).split('.')[0]
    if len(node['children']) == 3:
      node.match('_ *&name *&args *&body')
      name = node.name
      args = '%s%s%s' % ('(', node.args, ')')
    else:
      node.match('_ *&sig *&body')
      name, _, args = node.sig.partition('(')
      args = '(' + args
    if name in M['functions']:
      raise NodeException(node, 'function redefined: %s' % name)
    node.body += '}'
    if namespace not in M['functions']:
      M['functions'][namespace] = {}
    M['functions'][namespace][name] = (args, node.body)
  M.hook('global command function', global_command_function)

  M.setdefault('before_boot', [])
  def global_command_before_boot(node):
    M['before_boot'].append(node.match('_ *&'))
  M.hook('global command before_boot', global_command_before_boot)

  def handler_command_include(node, handler):
    handler['process'].append(('include', '.'.join(M.call('node repr', x) for x in node['children'])))
  M.hook('handler command include', handler_command_include)

  def handler_command_next(node, handler):
    handler['process'].append(('next', '.'.join(M.call('node repr', x) for x in node['children'])))
  M.hook('handler command next', handler_command_next)

  def php_code(node, handler):
    handler['process'].append(('{code', node['value']))
  M.hook('handler quote {', php_code)

  def template_variable(node, indent): # 处理模板中的变量
    var_string = node['value'][1:]
    variable_name = re.match('([a-zA-Z_][a-zA-Z0-9_]*)', var_string).group(0)
    if node['value'][0] == '$':
      var_string = "$%s" % var_string
      M['var template_variables'].add(variable_name)
    elif node['value'][0] == '%':
      var_string = '$%s' % var_string
    for child in node['children']: # 过滤器或者后缀
      if child['quote'] in ['"', "'"]:
        var_string = '%s.%s%s%s' % (var_string,
          child['quote'], child['value'], child['quote'])
      else:
        if '$$' in child['value']:
          var_string = child['value'].replace('$$', var_string)
        else:
          var_string = '%s(%s)' % (child['value'], var_string)
    return "%s<?php echo %s; ?>" % (
      ' ' * M['tabstop'] * indent,
      var_string,
      )
  M.hook('template variable', template_variable)

  def template_code(node, indent): # 处理模板中的代码
    if node['value'][0] == '=':
      node['value'] = 'echo %s' % node['value'][1:]
    return '%s<?php %s;%s; ?>' % (
      ' ' * M['tabstop'] * indent,
      node['value'],
      ';'.join(M.call('template node', x, 0) for x in node['children']),
      )
  M.hook('template code', template_code)

  def php_generate(): # 后端的生成函数
    for p in [
      load_functions, 
      generate_entrance_file, 
      generate_templates, 
      generate_handlers,
      ]:
      p()
  M.program(9, php_generate)

  def load_functions():
    php_files = [f[1] for f in listfiles(M['input_dir'])
      if f[1].endswith('.php')
      and not f[0].endswith('_')
      and not f[0].startswith(os.path.join(M['input_dir'], 'static'))]

    for filename in php_files:
      M.call('read php', filename)

  def read_php(filename):
    func_name = None
    func_args = None
    func_body = []
    lineno = 0
    namespace =  os.path.basename(filename).split('.')[0]
    if namespace not in M['functions']:
      M['functions'][namespace] = {}
    for line in open(filename, 'r').readlines():
      lineno += 1
      if line.lstrip()[:2] in ['<?', '?>']: continue # 忽略php标记
      if line.lstrip()[:8] == 'function' and line.rstrip().endswith('{'): # 函数头
        if func_name:
          M['functions'][namespace][func_name] = (func_args, ''.join(func_body))
          func_name = None
          func_args = None
          func_body = []
        func_name = line.lstrip().split(' ')[1]
        if '(' in func_name:
          func_name = func_name[:func_name.index('(')]
        if func_name in M['functions'][namespace]:
          raise RunException('function redefined at %s line %d: %s' % (filename, lineno, func_name))
        func_args = line[line.index('('):line.rindex('{')].strip()
      else:
        if func_name and line.strip() != '':
          func_body.append(line)
    if func_name:
      M['functions'][namespace][func_name] = (func_args, ''.join(func_body))
  M.hook('read php', read_php)

  def generate_entrance_file():
    gen_file({
      'timezone': M['timezone'],
      'handlers': ('\n%s' % (' ' * M['tabstop'] * 2)).join("'%s' => 1," % k
        for k in M['handlers']
        ),
      'title': M['title'],
      'index': M['index'],
      'core': ''.join(open(os.path.join(M['backend_dir'], 'core.inc.php'), 'r').readlines()[1:]),
      'before_boot': '\n\n'.join(M['before_boot']),
      'before_boot_includes': '\n\n'.join('include "%s";' % f
        for f in M['before_boot_includes']),
      }, 
      os.path.join(M['backend_dir'], 'index.php'), 
      os.path.join(M['output_dir'], 'index.php'))

  def generate_templates():
    css_dir = os.path.join(M['output_dir'], 'css')
    js_dir = os.path.join(M['output_dir'], 'js')
    os.path.exists(css_dir) or os.mkdir(css_dir)
    os.path.exists(js_dir) or os.mkdir(js_dir)

    open(os.path.join(css_dir, 'global.css'), 'w').write(
      '\n'.join([M['css_text'][x] for x in M['css_name']]))

    open(os.path.join(js_dir, 'global.js'), 'w').write(
      '\n'.join([open(os.path.join(M['input_dir'], 'static',
        '%s%s' % (x, '' if x.endswith('.js') else '.js'))
      , 'r').read()
      for x in M['js_name']]))

    for handler in M['handlers']:
      if M['handlers'][handler].has_key('css_name'):
        open(os.path.join(css_dir, 'page_%s_style.css' % handler)
          , 'w').write('\n'.join([
          M['css_text'][css_name] 
          for css_name in M['handlers'][handler]['css_name']]))
      if M['handlers'][handler].has_key('js_name'):
        open(os.path.join(js_dir, 'page_%s_script.js' % handler)
          , 'w').write('\n'.join([
          open(os.path.join(M['input_dir'], '%s%s' % (x,
            '' if x.endswith('.js') else '.js'))
          , 'r').read()
          for x in M['handlers'][handler]['js_name']]))

  def generate_handlers():
    handler_dir = os.path.join(M['output_dir'], 'handlers')
    os.path.exists(handler_dir) or os.mkdir(handler_dir)
    for handler in M['handlers']:
      handler_definition = M['handlers'][handler]

      if 'include_files' not in handler_definition:
        handler_definition['include_files'] = []

      handler_code = []
      funcs = set()
      template = None
      redirect = None
      next_pipe = None

      if 'insert to handler begin' in M:
        handler_code += M['insert to handler begin']

      for step in handler_definition['process']:
        step_type = step[0]
        if step_type == 'funcall': 
          func_name = step[1]
          func_args = step[2]
          handler_code.append('%s(%s);' % (func_name, ','.join(['%s' % arg
            for arg in func_args])))
          if handler_definition['namespace'] in M['functions']\
            and func_name in M['functions'][handler_definition['namespace']]:
            funcs.add(func_name)
          else:
            raise RunException('function %s not found for handler %s' % (func_name, handler))
        elif step_type == 'code' or step_type == '{code': 
          handler_code.append('%s;' % step[1].strip());
        elif step_type == 'template': 
          template = step[1]
        elif step_type == 'redirect': 
          redirect_nodes = step[1]
          if redirect_nodes[0]['quote'] is None and redirect_nodes[0]['value'] == 'path': # 传递给pather
            redirect = "call_user_func(context('pather'), %s)" % ','.join(M.call('node repr', x)
              for x in redirect_nodes[1:])
          else:
            redirect = '.'.join(M.call('node repr', x) for x in redirect_nodes)
          handler_code.append("context('redirect', %s);" % redirect)
        elif step_type == 'include': 
          handler_code.append('include %s;' % step[1])
        elif step_type == 'set': 
          handler_code.append('%s = %s;' % (step[1], step[2]))
        elif step_type == 'next':
          next_pipe = step[1]
          handler_code.append("context('next step', %s);" % next_pipe)
        else:
          raise RunException('unknown step: %s' % step_type)

      template_code = ''
      template_variable_keys = ''

      handler_type = M['handler_type'][handler]
      if handler_type == 'page':
        if template is None:
          template = handler
        if template not in M['templates']:
          template = 'default'
          warn('using default template for page %s' % handler)
        if next_pipe is None:
          handler_code.insert(0, "context('next step', 'template');")
        template_code = M['templates'][template]
        template_variable_keys = ','.join(['"%s"' % x
          for x in M['template_variables'][template]])
      elif handler_type == 'request':
        if redirect is None:
          redirect = '?'
          handler_code.insert(0, "context('redirect', '?');")
        if next_pipe is None:
          handler_code.insert(0, "context('next step', 'redirect');")

      funcs_code = []
      for func_name in funcs:
        func_args, func_body = M['functions'][handler_definition['namespace']][func_name]
        funcs_code.append('function %s%s {\n%s' % (
          func_name,
          func_args,
          func_body))

      include_code = []
      for f in handler_definition['include_files']:
        code = open(f, 'r').read()
        code = '\n'.join(x for x in code.splitlines() if x[:2] != '<?')
        include_code.append(code)

      gen_file({
        'handler_name': handler,
        'handler_code': '\n  '.join(handler_code),
        'funcs_code': '\n'.join(funcs_code),
        'template_variable_keys': template_variable_keys,
        'template_code': template_code,
        'include_code': '\n'.join(include_code)
        },
        os.path.join(M['backend_dir'], 'handler.inc.php'),
        os.path.join(M['output_dir'], 'handlers', '%s.php' % (
          handler)))

  def backend_node_exception(e):
    node = e.node
    msg = '''
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
      <style rel="stylesheet" type="text/css">
        html {
          background-color: #000;
          font-weight: bold;
          font-size: 20px;
        }
      </style>
      <div>
      <p style="color: red;">%s</p> 
      <p style="color: yellow;">at %s line %s:</p>
      <p style="color: cyan;">%s</p>
      </div>''' % (
      e.__class__.__name__,
      node['file'] if 'file' in node else '-',
      node['lineno'] if 'lineno' in node else '-',
      e.msg,
      )
    open(os.path.join(M['output_dir'], 'index.php'),
      'w').write(msg)
  M.hook('exception node', backend_node_exception)

  def backend_exception(e): # exception hook
    msg = '''
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
      <style rel="stylesheet" type="text/css">
        html {
          background-color: #000;
          font-weight: bold;
          font-size: 20px;
        }
      </style>
      <div>
      <p style="color: cyan;">%s</p>
      </div>''' % e
    open(os.path.join(M['output_dir'], 'index.php'),
      'w').write(msg)
  M.hook('exception', backend_exception)
