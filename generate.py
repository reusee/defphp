# coding: utf8

from utils import *
import os, sys
from shutil import rmtree, copyfile, copytree

def init(M):
  def generate():
    if not os.path.exists(M['output_dir']):
      os.mkdir(M['output_dir'])
    # 清空输出目录
    for root, dirs, files in os.walk(M['output_dir']):
      for f in files:
        os.unlink(os.path.join(root, f))
      for d in dirs:
        rmtree(os.path.join(root, d))
    # 直接复制到目标目录的文件
    source_directory = os.path.join(M['input_dir'], 'static')
    if os.path.exists(source_directory):
      for f in os.listdir(source_directory):
        if os.path.isdir(os.path.join(source_directory, f)):
          copytree(os.path.join(source_directory, f), os.path.join(M['output_dir'], f))
        else:
          copyfile(os.path.join(source_directory, f), os.path.join(M['output_dir'], f))
    # 骨架
    for dirr in ['js', 'css', 'lib']:
      if not os.path.exists(os.path.join(M['output_dir'], dirr)):
        os.mkdir(os.path.join(M['output_dir'], dirr))
  M.program(0, generate)
