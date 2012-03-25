<?php

function douban_oauth() {
  include 'lib/oauth/OAuthStore.php';
  include 'lib/oauth/OAuthRequester.php';
  define('DOUBAN_KEY', '0df3d98366dc5c4829db8c8a349514d8');
  define('DOUBAN_SECRET', 'e6265a67126d5895');

  define('DOUBAN_REQUEST_TOKEN_URL',
    'http://www.douban.com/service/auth/request_token');
  define('DOUBAN_AUTHORIZE_URL',
    'http://www.douban.com/service/auth/authorize');
  define('DOUBAN_ACCESS_TOKEN_URL',
    'http://www.douban.com/service/auth/access_token');

  define('OAUTH_TMP_DIR', function_exists('sys_get_temp_dir') ? 
    sys_get_temp_dir() : realpath($_ENV['TMP']));

  $options = array(
    'consumer_key' => DOUBAN_KEY,
    'consumer_secret' => DOUBAN_SECRET,
    'server_uri' => 'http://api.douban.com/',
    'request_token_uri' => DOUBAN_REQUEST_TOKEN_URL,
    'authorize_uri' => DOUBAN_AUTHORIZE_URL,
    'access_token_uri' => DOUBAN_ACCESS_TOKEN_URL,
  );

  OAuthStore::instance('Session', $options);
}

function douban_login() {
  define('BASEURL', 'http://' . 
    $_SERVER['HTTP_HOST'] . dirname($_SERVER['PHP_SELF']) . '/');
  $options = array(
    'oauth_as_header' => false,
  );
  $tokenResultParams = OAuthRequester::requestRequestToken(
    DOUBAN_KEY, 0, array(), 'POST', $options);
  $_SESSION['oauth_token'] = $tokenResultParams['token'];
  context('redirect', 
    DOUBAN_AUTHORIZE_URL . '?oauth_token=' . $tokenResultParams['token'] .
    '&oauth_callback='.BASEURL.'index.php?q=douban_oauth_callback');
}

function douban_callback() {
  OAuthRequester::requestAccessToken(DOUBAN_KEY, $_SESSION['oauth_token'], 0,
    'POST', $options = array(
      'oauth_verifier' => $_SESSION['oauth_token'],
    ));
  $req = new OAuthRequester('http://api.douban.com/people/'.urlencode('@me'),
    'get');
  $res = $req->doRequest();
  $user_data = new SimpleXMLElement($res['body']);

  $uid = array_pop(explode('/', $user_data->id));
  $auth_type = 'douban';

  $auth = R::findOne('oauth', "uid=? AND type=?", array($uid, $auth_type));
  if (!$auth) {
    $auth = R::dispense('oauth');
    $auth->uid = $uid;
    $auth->type = $auth_type;
    $encrypt_key = rand(100000, 999999);
    $auth->secret = $encrypt_key;
  }
  else {
    $encrypt_key = $auth->secret;
  }
  $cookie_str = sha1(implode('', array(
    $uid,
    $auth_type,
    $_SERVER['REMOTE_ADDR'],
    $_SERVER['HTTP_USER_AGENT'],
    $encrypt_key,
  )));
  $expire = time() + 3600 * 24 * 365;
  setcookie('s', $cookie_str, $expire);
  setcookie('auth_type', $auth_type, $expire);
  setcookie('uid', $uid, $expire);

  $auth->setMeta('buildcommand.unique', array(
    array('uid', 'type'),
  ));
  $auth->setMeta('buildcommand.indexes', array(
    'uid' => 'uid',
  ));
  R::store($auth);
}
