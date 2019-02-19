
_gita_completions()
{

  local cur commands repos cmd

  cur=${COMP_WORDS[COMP_CWORD]}
  cmd=${COMP_WORDS[1]}

  # FIXME: this is somewhat slow
  commands=`gita -h | sed '2q;d' |sed 's/[{}.,]/ /g'`

  repos=`gita ls`
  # this doesn't work for two repos with the same basename
  #gita_path=${XDG_CONFIG_HOME:-$HOME/.config}/gita/repo_path
  #repos=`awk '{split($0, paths, ":")} END {for (i in paths) {n=split(paths[i],b, /\//); print b[n]}}' ${gita_path}`

  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=($(compgen -W "${commands}" ${cur}))
  elif [ $COMP_CWORD -gt 1 ]; then
    case $cmd in
      add)
        COMPREPLY=($(compgen -d ${cur}))
        ;;
      ll)
        return
        ;;
      *)
        COMPREPLY=($(compgen -W "${repos}" ${cur}))
        ;;
    esac
  fi

}

complete -F _gita_completions gita

