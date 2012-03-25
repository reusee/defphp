# coding: utf8

from utils import *

def init(M):
  defaults = {
    'handlers': {},
    'handler_node': {},
    'handler_type': {},
    'handler_namespace': {},
  }
  for k in defaults:
    M.setdefault(k, defaults[k])

  M.setdefault('node dict keys', set())
  M['node dict keys'].update(['page', 'get', 'post'])

  def interpret_handlers():
    while M['handler_node'] != {}:
      name = M['handler_node'].keys()[0]
      info('interpreting handler %s' % name, 1)
      nodes = M['handler_node'].pop(name)
      handler = {
        'process': [],
        'namespace': M['handler_namespace'][name],
        'name': name,
      }
      interpret_handler_nodes(handler, nodes)
      M['handlers'][name] = handler
  M.program(0, interpret_handlers)

  def interpret_handler_nodes(handler, nodes):
    for node in nodes:
      if node['quote'] is None:
        cmd = node['value']
        hook_name = 'handler command %s' % cmd
        if M.has_hook(hook_name):
          M.call(hook_name, node, handler)
        else:
          warn('skipped handler command %s at file %s line %s' % (
          cmd, node['file'], node['lineno']), 2)
      else:
        M.call('handler quote %s' % node['quote'], node, handler)
  M.hook('interpret handler nodes', interpret_handler_nodes)

  def command_do(node, handler):
    for func in node['children']:
      if func['quote'] is None: # 外部函数
        function = ('funcall', func['value'], [])
        for arg in func['children']:
          if arg['quote'] is not None:
            function[2].append('%s%s%s' % (arg['quote'], arg['value'], arg['quote']))
          else:
            function[2].append(arg['value'])
      elif func['quote'] == '{': # 代码
        function = ('{code', func['value'])
      handler['process'].append(function)
  M.hook('handler command do', command_do)

  def command_template(node, handler):
    handler['process'].append(('template', node.match('_ *&')))
  M.hook('handler command template', command_template)

  def command_js(node, handler):
    if not handler.has_key('js_name'):
      handler['js_name'] = []
    handler['js_name'] += [x['value'] for x in node['children']
      if x['value'] not in handler['js_name']]
  M.hook('handler command js', command_js)

  def command_css(node, handler):
    if not handler.has_key('css_name'):
      handler['css_name'] = []
    handler['css_name'] += [x['value'] for x in node['children']
      if x['value'] not in handler['css_name']]
  M.hook('handler command css', command_css)

  def command_redirect(node, handler):
    handler['process'].append(('redirect', node['children']))
  M.hook('handler command redirect', command_redirect)

  def command_todo(node, handler):
    todo('implement handler %s' % handler['name'])
  M.hook('handler command todo', command_todo)
