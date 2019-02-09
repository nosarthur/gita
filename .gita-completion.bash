
_gita_completions()
{

  local cur=${COMP_WORDS[COMP_CWORD]}

  # this is slow
  commands=`gita -h | sed '2q;d' |sed 's/[{}.,]/ /g'`
  # this doesn't work for two repos with the same basename
  repos=`awk '{split($0, paths, ":")} END {for (i in paths) {n=split(paths[i],b, /\//); print b[n]}}' ~/.config/gita/repo_path`

  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=($(compgen -W "${commands}" ${cur}))
  elif [ $COMP_CWORD -eq 2 ]; then
    COMPREPLY=($(compgen -W "${repos}" ${cur}))
  fi

}

complete -F _gita_completions gita

