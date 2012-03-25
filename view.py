# coding: utf8

from utils import *
from html_specification import *
from copy import deepcopy

class FormatterException(Exception): pass

one_line_tags = [ # 就是open和close的tag在一行。因为在多行的话，它不会忽略空格
  'title', 'textarea', 'a', 'li',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'span', 'script',
]
css_child_tags = [ # 这些被认为是css的selector
  'a:link', 'a:hover', 'a:visited',
]

def init(M):
  defaults = {
    'css_name': [], # 这个是定义所有page都包含的css
    'css_node': {},
    'css_text': {},
    'js_name': [],
    'templates': {},
    'template_node': {},
    'template_variables': {},
  }
  for k in defaults:
    M.setdefault(k, defaults[k])

  def interpret_template_and_css():
    M['var constants'] = {
      'encoding': M['encoding'],
    }
    reset_tmp()
    format_templates()
    M['var css_variables'] = {}
    format_csses()
  M.program(0, interpret_template_and_css)

  def reset_tmp():
    M['var variables'] = []
    M['var blocks'] = {}

  def format_templates():
    not_formatted = set(M['template_node'].keys())\
      - set(M['templates'].keys())
    while not_formatted:
      name = not_formatted.pop()
      info('formatting template %s' % name, 1)
      reset_tmp()
      M['var template_variables'] = set()
      M['templates'][name] = format_template(
        M['template_node'][name], 0)
      M['template_variables'][name] = M['var template_variables']
      not_formatted = set(M['template_node'].keys())\
        - set(M['templates'].keys())

  def format_template(nodes, indent):
    while len(nodes) > 0 and nodes[0]['value'] == 'extends': # 继承的模板
      for block in nodes[1:]:
        block_name = block['value']
        M['var blocks'][block_name] = block['children']
      base_name = nodes[0]['children'][0]['value']
      nodes = M['template_node'][base_name]
    return '\n'.join(handle_template_node(node, indent)
      for node in nodes)
  M.hook('format template', format_template)

  def handle_template_node(node, indent = 0):
    node_type = template_node_type(node)
    string = '<!-- NOT HANDLE -->'
    indent_str = ' ' * indent * M['tabstop']
    
    if node_type == 'literal':
      if node['value'] == 'doctype':
        string = '%s<!DOCTYPE %s>' % (indent_str,
          ''.join([handle_template_node(x, 0) for x in node['children']]),
          )
      else:
        string = '%s%s%s' % (indent_str,
          node['value'],
          ''.join([handle_template_node(x, 0) for x in node['children']]),
          )

    elif node_type == 'constant': 
      constant_name = node['value'][1:].lower()
      if M['var constants'].has_key(constant_name):
        string = '%s%s%s' % (indent_str,
          M['var constants'][constant_name],
          ''.join([handle_template_node(x, 0) for x in node['children']]),
          )
      else:
        raise NodeException(node, 'constant not assigned: %s' % constant_name)

    elif node_type == 'variable': 
      string = M.call('template variable', node, indent)
      
    elif node_type == 'command': 
      string = handle_command(node, indent)

    elif node_type == 'nstt' or node_type == 'stt':
      child_indent = indent + 1 if node['value'] not in one_line_tags else 0
      ret = []
      tag_id = None
      tag_classes = []
      attribute = []
      tag_closing_comment = ''
      has_child = False # 用于决定nstt是否是one_line_tag
      for child in node['children']:
        child_node_type = template_node_type(child)
        if child_node_type == 'literal':
          if child['value'][0] == '#':
            tag_id = '%s%s' % (child['value'][1:],
              ''.join(handle_template_node(x, 0) for x in child['children']),
              )
          elif child['value'][0] == '.':
            tag_classes.append('%s%s' % (child['value'][1:],
              ''.join(handle_template_node(x, 0) for x in child['children']),
              ))
          elif child['value'] in html_attributes and\
            (node['value'] in html_attributes[child['value']] or\
            html_attributes[child['value']] == '*')\
            or child['value'][0] == '@':
            attribute.append(' %s="%s"' % (
              child['value']\
                if child['value'][0] != '@' else child['value'][1:],
              ''.join(handle_template_node(x, 0) for x in child['children']),
              ))
          else:
            ret.append(handle_template_node(child, child_indent))
            has_child = True
        else: #子节点
          ret.append(handle_template_node(child, child_indent))
          has_child = True
      if tag_classes != []:
        attribute.insert(0, ' class="%s"' % ' '.join(tag_classes))
        if node_type == 'nstt':
          tag_closing_comment = '<!-- /.%s -->' % tag_classes[0]
      if tag_id is not None:
        attribute.insert(0, ' id="%s"' % tag_id)
        if node_type == 'nstt':
          tag_closing_comment = '<!-- /#%s -->' % tag_id

      if node_type == 'stt':
        string = '%s<%s%s />' % (indent_str,
          node['value'],
          ''.join(attribute))
      elif node_type == 'nstt':
        ret.insert(0, '%s<%s%s>' % (indent_str,
          node['value'],
          ''.join(attribute)))
        if node['value'] in one_line_tags or not has_child:
          ret.append('</%s>' % node['value'])
          string = ''.join(ret)
        else:
          ret.append('%s</%s>%s' % (indent_str,
            node['value'],
            tag_closing_comment))
          string =  '\n'.join(ret)

    elif node_type == 'code': 
      string = M.call('template code', node, indent)

    return string

  M.hook('template node', handle_template_node)

  def command_include(node, indent):
    name = node['children'][0]['value']
    if name in M['template_node']:
      return format_template(M['template_node'][name], indent)
    else:
      raise NodeException(node, 'template not found: %s' % name)
  M.hook('template command include', command_include)

  def command_block(node, indent):
    name = node['children'][0]['value']
    if name in M['var blocks']:
      return format_template(M['var blocks'][name], indent)
    else:
      return '%s<!-- block %s -->' % (
        ' ' * M['tabstop'] * indent,
        name)
  M.hook('template command block', command_block)

  def command_js(node, indent):
    if node['children'][0]['quote'] != '{': # 非代码
      name = ''.join(M.call('template node', x) for x in node['children'])
      name = name if name.endswith('.js') else '%s.js' % name
      return '%s<script type="text/javascript" src="%s"></script>' % (
        ' ' * indent * M['tabstop'],
        name)
    else: # 代码
      code = node['children'][0]['value']
      return '%s<script type="text/javascript">%s</script>' % (
        ' ' * indent * M['tabstop'],
        code,
        )
  M.hook('template command js', command_js)

  def command_css(node, indent):
    name = ''.join(M.call('template node', x) for x in node['children'])
    name = name if name.endswith('.css') else '%s.css' % name
    return '%s<link href="%s" rel="stylesheet" type="text/css" />' % (
      ' ' * indent * M['tabstop'],
      name)
  M.hook('template command css', command_css)

  def handle_command(node, indent):
    cmd = node['value'][1:]
    hook_name = 'template command %s' % cmd
    if M.has_hook(hook_name):
      info('interpreting template command %s' % cmd, 2)
      return M.call(hook_name, node, indent)
    else:
      warn('skipped template command %s' % cmd, 2)
      return '<!-- NOT HANDLE COMMAND %s -->' % cmd

  def template_node_type(node):
    if node['quote'] is None:
      if node['value'][0] in ['$', '%']:
        if len(node['value']) > 1:
          if node['value'][1].isupper():
            return 'constant'
          elif node['value'][1].islower():
            return 'variable'
          else:
            return 'literal'
        else:
          return 'literal'
      elif node['value'][0] == '`':
        return 'command'
      elif node['value'] in non_self_terminating_tags:
        return 'nstt'
      elif node['value'] in self_terminating_tags:
        return 'stt'
      else:
        return 'literal'
    elif node['quote'] in ['{', '(']:
      return 'code'
    elif node['quote'] in ['"', "'"]:
      return 'literal'
    else:
      return 'literal'

  def format_csses():
    for css_name in M['css_node']:
      info('formatting css %s' % css_name, 1)
      M['css_text'][css_name] = '\n'.join(handle_css_node(node)
        for node in M['css_node'][css_name]).strip()

  def handle_css_node(node, paths = None):
    if paths is None: paths = [] # paths里面每个元素都是[]，因为可能出现多个selector的情况，需要做笛卡儿积
    if node['value'] == '`var':
      for child in node['children']:
        if not child['children']:
          raise NodeException(child, 'no value for variable: %s' % child['value'])
        M['var css_variables'][child['value']] = ''.join(x['value']
          for x in child['children'])
      return ''
    ret = []
    ret.append('%s {' % ', '.join(
      reduce(lambda cum, elem: [x + ' ' + y
        for x in cum for y in elem],
        paths + [[x.strip() 
        for x in node['value'].split(',')]])))
    child_css = []
    for child in node['children']:
      if child['value'][0] in ['.', '#', '`'] or\
        child['value'].split('.')[0] in non_self_terminating_tags +\
        self_terminating_tags + css_child_tags or\
        child['quote'] == '(': # 嵌套的selector
        selectors = [x.strip() for x in node['value'].split(',')]
        child_css.append(handle_css_node(child, paths + [selectors]))
      else: # 属性
        ret.append('%s%s: %s;' % (
          ' ' * M['tabstop'] * 1,
          child['value'],
          ' '.join(replace_css_variables(x)
            for x in child['children'])))
    ret.append('}')
    ret.append(''.join(child_css))
    return '\n'.join(ret)

  def replace_css_variables(node):
    if node['quote'] == '{' and node['value'] in M['var css_variables']:
      return M['var css_variables'][node['value']]
    else:
      return node['value']
