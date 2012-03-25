# coding: utf8

from utils import *

def init(M):
  def global_command_model(node):
    node.match('_ *&name **cols')
    for col in node.cols:
      col.match('*&name *type, **type_args **attrs')
      #print col.name, col.type['value'], len(col.type_args), len(col.attrs)
  M.hook('global command model', global_command_model)

  def global_command_model_db(node):
    node.match('_ *&host *&user *&password *&database')
    #print node.host, node.user, node.password, node.database
  M.hook('global command model_db', global_command_model_db)
