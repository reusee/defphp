import urllib2
import re
url = 'http://dev.w3.org/html5/spec/index.html#attributes-1'
content = urllib2.urlopen(url).read()

start = content.index('Attributes</h3>')
start = content.index('<tbody>', start)
end = content.index('</tbody>', start)
rows = content[start:end].split('<tr>')

attribute_dict = {}
for row in rows:
  cols = row.split('<td>')
  cols = [re.sub('<[^>]*>', '', col).strip() for col in cols]
  cols = [x for x in cols if x != '']
  if cols == []: continue
  attribute = cols[0]
  tags = [x.strip() for x in cols[1].split(';')]
  if not attribute_dict.has_key(attribute):
    attribute_dict[attribute] = []
  attribute_dict[attribute] += tags

start = content.index('Elements</h3>')
start = content.index('<tbody>', start)
end = content.index('</tbody>', start)
rows = content[start:end].split('<tr>')

non_self_terminating_tags = []
self_terminating_tags = []
for row in rows:
  cols = row.split('<td>')
  cols = [re.sub('<[^>]*>', '', col).strip() for col in cols]
  cols = [x for x in cols if x != '']
  if cols == []: continue
  elements = [x.strip() for x in cols[0].split(',')]
  if cols[4] == 'empty':
    self_terminating_tags += elements
  else:
    non_self_terminating_tags += elements

output_file = open('html_specification.py', 'w')

output_file.write('html_attributes = {\n')
for attribute in attribute_dict:
  output_file.write("  '%s': [\n" % attribute)
  for tag in attribute_dict[attribute]:
    if tag == 'HTML elements': tag = '*'
    output_file.write("    '%s',\n" % tag)
  output_file.write("    ],\n")
output_file.write('}\n')

output_file.write('self_terminating_tags = [\n')
for element in self_terminating_tags:
  output_file.write("  '%s',\n" % element)
output_file.write(']\n')

output_file.write('non_self_terminating_tags = [\n')
for element in non_self_terminating_tags:
  output_file.write("  '%s',\n" % element)
output_file.write(']\n')

output_file.close()
