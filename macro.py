# coding: utf8

from parse import Node
import re
from utils import *
from copy import deepcopy

def init(M):
  macros = {
    'global_macro': (False,
      lambda node: node['quote'] is None and node['value'] in M['global_macro'],
      lambda node: node['value']),
    'hdlr_macro': (False,
      lambda node: node['quote'] is None and node['value'] in M['hdlr_macro'],
      lambda node: node['value']),
    'tpl_macro': (True,
      lambda node: node['quote'] is None and node['value'][0] == '`' and node['value'][1:] in M['tpl_macro'],
      lambda node: node['value'][1:]),
    'no_macro': (True,
      lambda _: False,
      lambda _: None),
  }

  for macro in macros:
    M.setdefault(macro, {})

  M.setdefault('node dict keys', set())
  M['node dict keys'].update(macros.keys())

  def interpret_macros():
    for macro in macros:
      if macro in M['node dict']:
        for node in M['node dict'][macro]:
          if len(node['children']) < 2:
            raise NodeException(node, 'wrong argment numbers')
          node.match('_ *&name *&match **body')
          M[macro][node.name] = ('def', node.match, node.body)
        del M['node dict'][macro]
  M.program(0, interpret_macros)
  M.hook('interpret macros', interpret_macros)

  def expand_macros():
    expanded_node_list = expand_nodes(M['node list'], 'global_macro')
    M['node list'] = []
    for node in expanded_node_list:
      M.call('categorize node', node)
    M.call('load modules')
    M.call('interpret macros')

    for cmd in ['page', 'post', 'get']:
      if cmd in M['node dict']:
        for node in M['node dict'][cmd]:
          node['children'][1:] = expand_nodes(node['children'][1:], 'hdlr_macro')

    if 'template' in M['node dict']:
      M['node dict']['template'] = expand_nodes(
        M['node dict']['template'], 'tpl_macro')
  M.program(0, expand_macros)

  def isvar(node):
    return node['quote'] is None and node['value'][0] == ':' and node['value'][-1] == ':'

  def getvar(binding_stack, name):
    for binding in binding_stack:
      if hasattr(binding, name):
        return deepcopy(getattr(binding, name)) # 返回副本
    return False

  def listify(arg):
    if not isinstance(arg, list):
      return [arg]
    return arg

  def expand_nodes(nodes, macro_set, binding = None):
    if binding is None: binding = []
    if macro_set not in macros:
      raise RunException('macroset <%s> does not exist' % macro_set)
    recursive, predict, namegetter = macros[macro_set]
    i = 0
    while i < len(nodes):
      while i < len(nodes) and (predict(nodes[i]) or isvar(nodes[i])): # 如果是可以展开的node，则展开
        current_node = nodes[i]
        if predict(current_node): # macro node
          macro_name = namegetter(current_node)
          if macro_name in M[macro_set]:
            macro = M[macro_set][macro_name]
            if macro[0] == 'def': # def实现的macro
              _, match, body = macro
              body = deepcopy(body)
              current_node.match(match)
              nodes[i:i+1] = listify(expand_nodes(body, macro_set, [current_node] + binding))
            elif macro[0] == 'py': # py实现的macro
              nodes[i:i+1] = listify(expand_nodes(listify(macro[1](current_node)), macro_set, binding))
        elif isvar(current_node): # variable node
          var_name = current_node['value'][1:-1]
          var = getvar(binding, var_name)
          if isinstance(var, str):
            raise NodeException(current_node, 'use * for %s but not *&' % var_name)
          if var is not False:
            children = current_node['children'] # children都添加到第一个新node里
            new_nodes = listify(expand_nodes(listify(var), macro_set, binding))
            if len(new_nodes) > 0:
              new_nodes[0]['children'] += children
            nodes[i:i+1] = new_nodes
          else: # 未绑定的，不作处理
            break
      if i >= len(nodes): break # 如果一个node展开为[]，则会出现这种情况
      if nodes[i]['quote'] is not None: # in-string variable
        var_names = [x[1:-1] for x in 
          re.findall(':[a-zA-Z_][a-zA-Z0-9_]*:', nodes[i]['value'])]
        for var_name in var_names:
          var = getvar(binding, var_name)
          if var is not False:
            if isinstance(var, Node):
              var = var['value']
            nodes[i]['value'] = nodes[i]['value'].replace(':%s:' % var_name, var)
      if recursive: # 处理子元素
        nodes[i]['children'] = expand_nodes(nodes[i]['children'], macro_set, binding)
      else: # 只处理binding
        nodes[i]['children'] = expand_nodes(nodes[i]['children'], 'no_macro', binding)
      i += 1
    return nodes
  M.hook('expand nodes', expand_nodes)
