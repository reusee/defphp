" Defphp Syntax File
" Language: Defphp
" Maintainer: reus <reusee@gmail.com>
" Filenames: *.def
" Version: 0.1

syntax case match

syn match Comment "//.*$" 
highlight link Comment Comment
syn region SingleQuote start=+'+ end=+'+ skip=+\\'+
highlight link SingleQuote String
syn region DoubleQuote start=+"+ end=+"+ skip=+\\"+
highlight link DoubleQuote String
syn match GlobalCommand "^\w*"
highlight link GlobalCommand Structure

syn keyword HandlerCommand extends do template js css redirect set include next from_post contained
syn match HandlerDefinition "^\(page\|post\|get\)\_.\{-}\n\( \{1,}\_.\{-}\n\|\n\)*" contains=HandlerCommand,GlobalCommand,Comment,SingleQuote,DoubleQuote
highlight link HandlerCommand Statement

syn match TemplateCommand "`\w*" 
highlight link TemplateCommand Statement

syn match CssSelector +^\s*\([#\.({].*\|a\|abbr\|address\|article\|aside\|audio\|b\|bdi\|bdo\|blockquote\|body\|button\|canvas\|caption\|cite\|code\|colgroup\|datalist\|dd\|del\|details\|dfn\|div\|dl\|dt\|em\|fieldset\|figcaption\|figure\|footer\|form\|h1\|h2\|h3\|h4\|h5\|h6\|head\|header\|hgroup\|html\|i\|iframe\|ins\|kbd\|label\|legend\|li\|map\|mark\|menu\|meter\|nav\|noscript\|object\|ol\|optgroup\|option\|output\|p\|pre\|progress\|q\|rp\|rt\|ruby\|s\|samp\|script\|section\|select\|small\|span\|strong\|style\|sub\|summary\|sup\|table\|tbody\|td\|textarea\|tfoot\|th\|thead\|time\|title\|tr\|u\|ul\|var\|video\|area\|base\|br\|col\|command\|embed\|hr\|img\|input\|keygen\|link\|meta\|param\|source\|track\|wbr\|a:hover\|a:link\|a:visited\)$+ contained
highlight link CssSelector Define
syn match CssDefinition "^defcss\_.\{-}\n\( \{1,}\_.\{-}\n\|\n\)*" contains=GlobalCommand,Comment,SingleQuote,DoubleQuote,CssSelector,TemplateCommand

let b:current_syntax = "defphp"
