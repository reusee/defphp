# coding: utf8

import os

def init(M):
  M.check_deps('redbean')

  M.call('read def', os.path.join(M['framework_dir'], 'modules', 'user.def'))

  def add_user_init_code(node):
    M.setdefault('before_boot', [])
    M['before_boot'].append('''{
  $_SESSION['uid'] = 0;
  if (context('logined')) {
    $auth = context('auth');
    $user = R::relatedOne($auth, 'user');
    if (!$user) {
      $user = R::dispense('user');
      R::associate($user, $auth);
    }
    if (empty($user->name)) {
      $user->name = '来自' . $_COOKIE['auth_type'] . '的' . $_COOKIE['uid'];
      R::store($user);
    }
    context('user_name', $user->name);
    context('user', $user);
    $_SESSION['uid'] = $user->id;
  }
}''')
  M.hook('global command add_user_init_code', add_user_init_code)
