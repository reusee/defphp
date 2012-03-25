# coding: utf8

def init(M):
  def command_if(node, indent):
    ret = []
    condition = node['children'][0]['value']
    ret.append('<?php if (%s): ?>' % condition)
    ret.append('\n'.join(M.call('template node', x, indent)
      for x in node['children'][1:]))
    ret.append('<?php endif; ?>')
    return ''.join(ret)
  M.hook('template command if', command_if)

  def command_elif(node, indent):
    ret = []
    condition = node['children'][0]['value']
    ret.append('<?php elseif (%s): ?>' % condition)
    ret.append('\n'.join(M.call('template node', x, indent)
      for x in node['children'][1:]))
    return '\n'.join(ret)
  M.hook('template command elif', command_elif)

  def command_else(node, indent):
    ret = []
    ret.append('<?php else: ?>')
    ret.append('\n'.join(M.call('template node', x, indent)
      for x in node['children']))
    return '\n'.join(ret)
  M.hook('template command else', command_else)

  def command_loop(node, indent):
    ret = []
    name = node['children'][0]['value']
    if node['children'][0]['quote'] == '(': # 直接的代码
      var_str = name
    else:
      M['var template_variables'].add(name)
      var_str = '$%s' % name
    if node['children'][1]['children']: # key => value
      k = node['children'][1]['value']
      v = node['children'][1]['children'][0]['value']
      ret.append("<?php foreach (%s as $%s => $%s): ?>" % (
        var_str, k, v))
    else:
      v = node['children'][1]['value']
      ret.append("<?php foreach (%s as $%s): ?>" % (
        var_str, v))
    ret.append('\n'.join(M.call('template node', x, indent)
      for x in node['children'][2:]))
    ret.append('<?php endforeach; ?>')
    return '\n'.join(ret)
  M.hook('template command loop', command_loop)

  def command_switch(node, indent):
    ret = []
    condition = node['children'][0]['value']
    ret.append('<?php switch (strval(%s)):' % condition)
    for case in node['children'][1:]:
      if case['value'] == 'default':
        ret.append('default: ?>')
      else:
        ret.append('case "%s": ?>' % case['value'])
      ret.append('\n'.join(M.call('template node', x, indent)
        for x in case['children']))
      ret.append('<?php break;')
    ret.append('endswitch; ?>')
    return '\n'.join(ret)
  M.hook('template command switch', command_switch)

  def command_path(node, indent):
    return "<?php echo call_user_func(context('pather'), %s); ?>" % ','.join(M.call('node repr', x)
      for x in node['children'])
  M.hook('template command path', command_path)
