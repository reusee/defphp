from utils import *

def init(M):
  def convert_post():
    M.setdefault('insert to handler begin', [])
    M['insert to handler begin'].append('''foreach ($_POST as &$value) {
    $value = htmlspecialchars(trim($value), ENT_QUOTES, 'UTF-8');
  }''')
  M.program(1, convert_post)
