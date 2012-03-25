<?php defined('ENTRANCE') or die('Deny');

function handler_<<handler_name>>() {
  <<handler_code>>
  return context('next step');
}

<<funcs_code>>

function template() {
  extract(context(array(<<template_variable_keys>>)));
?><<template_code>><?php
}

<<include_code>>
