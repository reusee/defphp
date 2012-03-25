# coding: utf8

from utils import *

def init(M):
  defaults = {
    'encoding': 'utf-8',
    'tabstop': 2,
    'timezone': 'Asia/Shanghai',
    'title': 'Untitled',
    'node dict keys': set(),
  }
  for k in defaults:
    M.setdefault(k, defaults[k])
  M['node dict keys'].update(['import', 'template'])

  def interpret_global_command():
    for cmd in M['node dict']:
      hook_name = 'global command %s' % cmd
      if M.has_hook(hook_name):
        info('interpreting global command %s' % cmd, 1)
        for node in M['node dict'][cmd]:
          M.call(hook_name, node)
      else:
        warn('skipped global command %s' % cmd, 1)
        todo('handle global command %s' % cmd)
    for node in M['node list']:
      cmd = node['value']
      hook_name = 'global command %s' % cmd
      if M.has_hook(hook_name):
        info('interpreting global command %s' % cmd, 1)
        M.call(hook_name, node)
      else:
        warn('skipped global command %s' % cmd, 1)
        todo('handle global command %s' % cmd)
  M.program(0, interpret_global_command)

  for attr in ['title', 'index', 'timezone', 'encoding']:
    def f(node):
      node.match('*&attr *&value')
      M[node.attr] = node.value
    M.hook('global command %s' % attr, f)

  def handler_command(node):
    node.match('_ *&name **defs')
    if node.name not in M['handler_node']:
      M['handler_node'][node.name] = node.defs
    else:
      M['handler_node'][node.name] += node.defs
    if node['value'] in ['page']:
      M['handler_type'][node.name] = 'page'
    else:
      M['handler_type'][node.name] = 'request'
    namespace = os.path.basename(node['file']).split('.')[0]
    M['handler_namespace'][node.name] = namespace
  for cmd in ['page', 'post', 'get']:
    M.hook('global command %s' % cmd, handler_command)

  def global_js(node):
    for child in node['children']:
      M['js_name'].append(child['value'])
  M.hook('global command js', global_js)

  def global_css(node):
    for child in node['children']:
      M['css_name'].append(child['value'])
  M.hook('global command css', global_css)

  def global_template(node):
    node.match('_ *&name **defs')
    M['template_node'][node.name] = node.defs
  M.hook('global command template', global_template)

  def global_defcss(node):
    node.match('_ *&name **defs')
    M['css_node'][node.name] = node.defs
  M.hook('global command defcss', global_defcss)
