
_gita_completions()
{

  local cur prev commands repos gita_path

  cur=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}

  gita_path=${XDG_CONFIG_HOME:-$HOME/.config}/gita/repo_path

  # this is somewhat slow
  commands=`gita -h | sed '2q;d' |sed 's/[{}.,]/ /g'`
  # this doesn't work for two repos with the same basename
  repos=`awk '{split($0, paths, ":")} END {for (i in paths) {n=split(paths[i],b, /\//); print b[n]}}' ${gita_path}`

  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=($(compgen -W "${commands}" ${cur}))
  elif [ $COMP_CWORD -gt 1 ]; then
    case $prev in
      add)
        COMPREPLY=($(compgen -d ${cur}))
        ;;
      *)
        COMPREPLY=($(compgen -W "${repos}" ${cur}))
        ;;
    esac
  fi

}

complete -F _gita_completions gita

