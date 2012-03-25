#!/usr/bin/env python
# coding: utf8

from utils import *
from weakref import proxy
import sys
import re

def init(M):
  M['node dict'] = {}
  M['node list'] = []
  def parse():
    def_files = [f[1] for f in listfiles(M['backend_dir'])
      + listfiles(M['input_dir'])
      if f[1].endswith('.def')
      and not f[0].endswith('_')]
    for f in def_files:
      M.call('read def', f)
  M.program(0, parse)

  def read_def(f):
    tree = parse_file(f)
    for node in tree['children']:
      M.call('categorize node', node)
  M.hook('read def', read_def)

  def categorize_node(node):
    if node['value'] in M['node dict keys']:
      if node['value'] not in M['node dict']:
        M['node dict'][node['value']] = []
      M['node dict'][node['value']].append(node)
    else:
      M['node list'].append(node)
  M.hook('categorize node', categorize_node)

  def node_repr(node):
    if node['quote'] in ['"', "'"]:
      return '%s%s%s' % (node['quote'], node['value'], node['quote'])
    else:
      return node['value']
  M.hook('node repr', node_repr)

debug = False

class ParseError(Exception):
  def __init__(self, msg, f = '<string>', lineno = 0, s = ''):
    self.msg = msg
    self.lineno = lineno
    self.s = s
    self.file = f

def parse_file(f):
  with open(f, 'r') as infile:
    source = infile.read()
  try:
    ret = Parser(source, f).root
    return ret
  except ParseError, e:
    print '文件%s第%d行错误：%s' % (e.file, e.lineno, e.msg)
    sys.exit(-1)

class Node(dict):
  def __init__(self, d = {}):
    self.update({
      'value': None,
      'quote': None,
      'indent': -1,
      'children': [],
      'lineno': 0,
      'file': None,
    })
    self.update(d)

  def dump(self, verbose = False, indent = 0):
    ret = []
    if verbose:
      ret.append('%s%s <quote: %s, len: %s, indent: %s, lineno: %s>' % (
        ' ' * indent,
        color(self['value'], GREEN),
        color(self['quote'], CYAN),
        color(len(self['value']), CYAN),
        color(str(self['indent']), CYAN),
        color(self['lineno'], CYAN),
        ))
    else:
      ret.append('%s%s' % (' ' * indent, self['value']))
    ret += [x.dump(verbose, indent + 4) for x in self['children']]
    return '\n'.join(ret)

  def match(self, *desc):
    match_string = '\n'.join(desc)
    matcher = Parser(match_string).root
    if matcher['value'] == 'ROOT' and self['value'] != 'ROOT':
      matcher = matcher['children'][0]
    match_type, match_result = self._match(self, matcher)
    if match_type in ['value', 'node']:
      return match_result
    elif match_type == 'matches':
      for k in match_result:
        setattr(self, k, match_result[k])
      return match_result
    elif match_type == 'not_match':
      raise ParseError('不匹配: %s' % repr(match_string))

  def to_list(self):
    ret = [self] + self['children']
    self['children'] = []
    return ret

  def _match(self, node, matcher):
    ret = {}
    value_matcher = matcher['value']
    name = None
    regex = None
    if value_matcher == '_': # 相当于.*
      regex = '.*'
    elif value_matcher[0] == '*':
      spec = value_matcher.split('/', 1)
      if len(spec) == 2:
        name, regex = spec
        name = name[1:]
      else:
        name = spec[0][1:]
      if name == '':
        return 'node', node
      elif name == '&':
        return 'value', node['value']
    else:
      regex = value_matcher
    if regex:
      if not re.match(regex, node['value']): # 如果不匹配则不继续了
        return 'not_match', ret
    if name: 
      if name[0] == '&' and len(name) > 2: # *&表示绑定此node的value而不是Node到此name
        ret[name[1:]] = node['value']
      else:
        ret[name] = node
    if matcher['children']:
      if matcher['children'][-1]['value'].startswith('**'): # 剩余匹配
        name = matcher['children'][-1]['value'][2:]
        ret[name] = node['children'][len(matcher['children']) - 1:]
      child_matchers = [x for x in matcher['children']
        if not x['value'].startswith('**')]
      child_ret = map(lambda arg: self._match(*reversed(arg)), zip(child_matchers, node['children']))
      for match_type, match_result in child_ret:
        if match_type in ['node', 'value', 'not_match']:
          return match_type, match_result
        elif match_type == 'matches':
          ret.update(match_result)
    return 'matches', ret

class State(dict):
  def __init__(self, d):
    self.update(d)
    self.stack = []
    self.last_node = None
  def push(self):
    self.stack.append(dict(self))
  def pop(self):
    self.update(self.stack.pop())

class SourceIterator(str):
  def __init__(self, s):
    str.__init__(self, s)
    self.iter = iter(s)
    self.lineno = 1
    self.index = -1
    self.last_c = None
  def __call__(self):
    self.index += 1
    if self.last_c in NEWLINE:
      self.lineno += 1
    try:
      c = self.iter.next()
      self.last_c = c
      return c
    except StopIteration:
      return False

SPACE = [' ', '\t']
NEWLINE = ['\n', '\r']
QUOTE = {
  '"': '"',
  "'": "'",
  '(': ')',
  '{': '}',
}
class Parser:
  def __init__(self, source, f = '<string>'):
    self.tabstop = 2
    self.file = f
    self.root = Node({'file': f, 'value': 'ROOT'})
    self.state = State({
      'context': 'LINE_START',
      'indent': -1,
      'port': proxy(self.root),
      'in_list': False,
      'quote': None,
      'in_nest': False,
    })
    self.s = SourceIterator(source)

    self.parse()
    self.strip(self.root)

  def strip(self, node):
    if 'parent' in node:
      del node['parent']
    for child in node['children']:
      self.strip(child)

  def dump_state(self):
    def d(state):
      print color(state['context'], GREEN),
      print 'port:', color(state['port']['value'], CYAN),
      print 'indent:', color(state['indent'], CYAN),
      print 'quote:', color(state['quote'], CYAN),
      print 'in_list:', color(state['in_list'], CYAN),
      print 'in_nest:', color(state['in_nest'], CYAN)
    d(self.state)
    for state in reversed(self.state.stack):
      d(state)

  def node(self, value): # 增加一个node
    indent =  self.state['indent']
    while indent <= self.state['port']['indent']:
      self.state['port'] = self.state['port']['parent']
    node = Node({
      'value': value,
      'indent': self.state['indent'],
      'quote': self.state['quote'],
      'parent': self.state['port'],
      'lineno': self.s.lineno,
      'file': self.file,
    })
    self.state['port']['children'].append(node)
    self.state.last_node = node
    if debug:
      print color('Add node', BLUE), node['value']
    return node

  def parse(self):
    s = self.s
    no = 1
    c = s()
    while c:
      context = self.state['context']

      if debug:
        print '=' * 15, color('state', RED), color(no, YELLOW), '=' * 15
        no += 1
        self.dump_state()
        print '-' * 15, '%s - line: %s' % (color(repr(c), GREEN), 
          color(self.s.lineno, YELLOW)), '-' * 15
        print repr(s[s.index:s.index+30])
        print '-' * 30
        print self.root.dump(True)
        print

      if context == 'LINE_START':
        if s[s.index:s.index+2] == '//': # 注释
          self.state['context'] = 'COMMENT'
          continue
        elif c in NEWLINE: # 空行
          c = s()
          continue
        else: # HEAD
          self.state['indent'] = 0
          while c and c in SPACE:
            c = s()
            self.state['indent'] += 1
          if not c: break
          if c in NEWLINE: continue
          self.state['context'] = 'HEAD'
          continue

      elif context == 'COMMENT':
        while c:
          c = s()
          if s[s.index - 1] in NEWLINE: break # 忽略到下一行
        self.state['context'] = 'LINE_START'
        continue

      elif context == 'HEAD':
        self.state['in_list'] = False # 重置此状态
        if s[s.index:s.index+2] == '//': # 注释
          self.state['context'] = 'COMMENT'
          continue
        elif c in QUOTE: # quoted
          self.state['context'] = 'HEAD_END'
          self.state.push()
          self.state['context'] = 'QUOTE'
          self.state['quote'] = c
          c = s()
          continue
        elif c == '[': # 嵌套开始
          self.state['indent'] += self.tabstop # 这个是为TAIL准备的
          self.state['context'] = 'TAIL' # 也是为TAIL准备的
          self.state.push()
          self.state['in_nest'] = True
          self.state['indent'] -= self.tabstop # head自己用的indent
          self.state['context'] = 'HEAD' 
          c = s()
          while c.isspace():
            c = s()
          continue
        else:
          tok_start = s.index
          while c and \
            ((not c.isspace() and c != ']' and self.state['in_nest']) or\
            (not c.isspace() and not self.state['in_nest'])):
            c = s()
          node = self.node(s[tok_start:s.index])
          if not c: break
        self.state['context'] = 'HEAD_END'
        continue

      elif context == 'HEAD_END':
        self.state['port'] = proxy(self.state.last_node)
        while c in SPACE: c = s() # 跳过空格
        if c in NEWLINE: # 下一行了
          c = s()
          if self.state['in_nest']: # 在嵌套环境下，所有换行都类同空格
            self.state['indent'] += self.tabstop
            self.s.lineno += 1
            self.state['context'] = 'TAIL'
          else:
            self.state['context'] = 'LINE_START'
          continue
        elif c == ']': # 嵌套结束
          self.state.pop()
          self.state['port'] = proxy(self.state.last_node) # port应该指向新生成的node
          self.state['context'] = 'TAIL'
          c = s()
          # 处理in_list
          if not self.state['in_list']:
            if c == ',': # []不能有孙子，想有就直接放括号里面
              raise ParseError('请把子元素写在括号里面，而不是用逗号语法',
                self.file, self.s.lineno)
          else:
            if c != ',': # 是阿叔
              self.state['port'] = self.state['port']['parent']
              self.state['indent'] -= self.tabstop
              self.state['in_list'] = False
          continue
        else:
          self.state['indent'] += self.tabstop
          self.state['context'] = 'TAIL'
          continue

      elif context == 'QUOTE':
        quote_balance = 1
        tok_start = s.index
        while quote_balance != 0:
          if not c:
            raise ParseError('不匹配的引用', self.file, self.s.lineno)
          elif c == QUOTE[self.state['quote']] and s[s.index-1] != '\\':
            quote_balance -= 1
          elif c == self.state['quote'] and s[s.index-1] != '\\':
            quote_balance += 1
          c = s()
        node = self.node(s[tok_start:s.index-1])
        self.state.pop()
        self.state.last_node = node
        continue

      elif context == 'TAIL':
        if self.state['in_nest']: # nest环境下所有换行都视作空格，也就是不使用缩进来表示关系
          while c and c.isspace() or c == ',': 
            if c in NEWLINE: self.s.lineno += 1
            c = s()
        else:
          while c in SPACE or c == ',': c = s() # 跳过空格和逗号
        if c in NEWLINE and not self.state['in_nest']: # 下一行
          self.state['context'] = 'LINE_START'
          c = s()
          continue
        elif s[s.index:s.index+2] == '//': # 注释
          self.state['context'] = 'COMMENT'
          continue
        elif c in QUOTE:
          self.state['context'] = 'TAIL_END'
          self.state.push()
          self.state['context'] = 'QUOTE'
          self.state['quote'] = c
          c = s()
          continue
        elif c == '[': # 嵌套开始
          self.state['context'] = 'TAIL' # 为TAIL准备的
          self.state.push()
          self.state['in_nest'] = True
          self.state['context'] = 'HEAD' 
          c = s()
          while c.isspace():
            c = s()
          continue
        else:
          tok_start = s.index
          while c and\
            ((not c.isspace() and c != ']' and self.state['in_nest']) or
            (not c.isspace() and not self.state['in_nest'])):
            c = s()
          if tok_start != s.index: 
            node = self.node(s[tok_start:s.index])
          if not c: break
        self.state['context'] = 'TAIL_END'
        continue

      elif context == 'TAIL_END':
        if self.state['in_nest']: # 在nest的环境下，换行也跳过，视作空格
          try:
            while c.isspace(): 
              if c in NEWLINE: self.s.lineno += 1
              c = s()
          except AttributeError, e:
            if "object has no attribute 'isspace'" in e.message:
              raise ParseError('不匹配的括号', self.file, self.s.lineno)
        else:
          while c in SPACE: c = s() # 跳过空格
        if c in NEWLINE and not self.state['in_nest']: # 下一行
          self.state['context'] = 'LINE_START'
          c = s()
          continue
        elif c == ']': # 结束嵌套
          self.state.pop()
          self.state['port'] = proxy(self.state.last_node) # port应该指向新生成的node
          c = s()
          # 处理in_list
          if not self.state['in_list']:
            if c == ',':
              raise ParseError('请把子元素写在括号里面，而不是用逗号语法', self.file, self.s.lineno)
          else:
            if c != ',': # 是阿叔
              self.state['port'] = self.state['port']['parent']
              self.state['indent'] -= self.tabstop
              self.state['in_list'] = False
          continue
        else: # 继续TAIL
          last_node = self.state.last_node
          if not self.state['in_list']:
            if c == ',': # 这个是quote后跟,的情况
              c = s()
              self.state['port'] = proxy(last_node)
              self.state['indent'] += self.tabstop
              self.state['in_list'] = True
            elif last_node['quote'] is None and last_node['value'][-1] == ',': # 只有quote是None的才可以有孙子
              last_node['value'] = last_node['value'][:-1]
              self.state['port'] = proxy(last_node)
              self.state['indent'] += self.tabstop
              self.state['in_list'] = True
          else:
            if c == ',': # 继续孙子，这是quote后跟,的情况
              c = s()
            elif last_node['value'] and last_node['value'][-1] == ',': # 继续孙子, 这里不管quote
              last_node['value'] = last_node['value'][:-1]
            else: # 后面的是叔叔了
              self.state['port'] = self.state['port']['parent']
              self.state['indent'] -= self.tabstop
              self.state['in_list'] = False
          self.state['context'] = 'TAIL'
          continue

def main():
  from tempfile import NamedTemporaryFile
  f = NamedTemporaryFile('rw+')
  f.write('''\
//comment
  //comment
  
  [foo] [bar [baz]]
  foo bar, baz
  foo 'bar', 'baz'
  foo
    [bar  
    baz 
    foo]
  foo bar, [baz] foo, [bar baz] foo
  foo 'bar', 'baz', 'foo' bar foo, bar, baz
  {{foo}} //bar
  ''')
  f.flush()
  node = parse_file(f.name)
  node.dump(True)
  node.dump()
  node.match('_ *foo *&bar **baz')
  node.foo.match('*')
  node.foo.match('*&')
  node.foo.match('*&foo')
  node.foo.match('*foo *&')
  try: node.foo.match('foobarbaz')
  except ParseError: pass
  node.match('*foo/foo')
  node.match('_ _ *')
  f.seek(0)
  f.write('foo [bar], baz')
  f.flush()
  try: parse_file(f.name)
  except: pass
  f.seek(0)
  f.write('{foo')
  f.flush()
  try: parse_file(f.name)
  except: pass
  f.seek(0)
  f.write('foo [bar bar] baz')
  f.flush()
  try: parse_file(f.name)
  except: pass

if __name__ == '__main__':
  debug = True
  main()

