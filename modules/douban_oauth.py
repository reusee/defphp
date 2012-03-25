# coding: utf8

from utils import *
import os

def init(M):
  M.check_deps('redbean')

  M.call('read def', os.path.join(
    M['framework_dir'], 'modules', 'douban_oauth.def'))
  M.call('read php', os.path.join(
    M['framework_dir'], 'modules', 'douban_oauth.php'))

  def add_douban_oauth_code(node):
    M.setdefault('before_boot', [])
    M['before_boot'].append('''{
  $logined = false;
  if (isset($_COOKIE['s']) && !empty($_COOKIE['s'])
    && isset($_COOKIE['uid']) && !empty($_COOKIE['uid'])
    && isset($_COOKIE['auth_type']) && !empty($_COOKIE['auth_type'])) { //验证cookie
    $auth = R::findOne('oauth', 'uid=? AND type=?', array(
      $_COOKIE['uid'], $_COOKIE['auth_type']));
    $encrypt_key = $auth->secret;
    if ($_COOKIE['s'] == sha1(implode('', array(
      $_COOKIE['uid'],
      $_COOKIE['auth_type'],
      $_SERVER['REMOTE_ADDR'],
      $_SERVER['HTTP_USER_AGENT'],
      $encrypt_key,
    )))) {
      $logined = true;
      context('auth', $auth);
    }
  }
  context('logined', $logined);
}''')
  M.hook('global command add_douban_oauth_code', add_douban_oauth_code)
