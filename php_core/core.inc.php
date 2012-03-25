<?php

function arg_q_pather() {
  return "?q=" . implode('/', func_get_args());
}

function boot($func) {
  while (($func = $func()) != null) {
  }
}

function context() {
  global $CTX;

  $args = func_get_args();
  if (isset($args[1])) {
    $CTX[$args[0]] = $args[1]; # 单一set
  }
  else {
    if (is_array($args[0])) { # 多值get和set
      $ret = array();
      foreach ($args[0] as $key => $value) {
        if (is_int($key)) { # get
          $ret[$value] = isset($CTX[$value]) ? $CTX[$value] : null;
        }
        else { # set
          $CTX[$key] = $value;
          $ret[$key] = $value;
        }
      }
      return $ret;
    }
    else { # 单值get
      return isset($CTX[$args[0]]) ? $CTX[$args[0]] : null;
    }
  }
}

function redirect() {
  header('location: '.context('redirect'));
}
