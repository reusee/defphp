<?php
define('ENTRANCE', true);
session_start();
date_default_timezone_set('<<timezone>>'); //时区设置

global $CTX;
$CTX = array();

context(array(
  'start time' => microtime(true),
  'title' => '<<title>>',
  'index page' => '<<index>>',
  'pather' => 'arg_q_pather',
));

<<before_boot_includes>>

<<before_boot>>

$handlers = array(
  <<handlers>>
);

function valid_path($path) {
  global $handlers;
  return array_key_exists($path, $handlers);
}

boot(function() use ($handlers) {
  isset($_GET['q']) and $query = trim($_GET['q']);
  !empty($query) or $query = context('index page');
  list($query) = explode('/', $query);
  if (!isset($handlers[$query])) {
    $query = 'not_found';
  }
  context('query path', $query);
  require "handlers/$query.php";
  return "handler_$query";
});
<<core>>
