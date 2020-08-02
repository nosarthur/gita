
_gita_completions()
{

  local cur commands repos cmd
  local COMP_CWORD COMP_WORDS  # 定义变量，cur表示当前光标下的单词
  read -cn COMP_CWORD  # 所有指令集
  read -Ac COMP_WORDS  # 当前指令的索引值

  cur=${COMP_WORDS[COMP_CWORD]}
  cmd=${COMP_WORDS[2]}

  # FIXME: this is somewhat slow
  commands=`gita -h | sed '2q;d' |sed 's/[{}.,]/ /g'`

  repos=`gita ls`
  # this doesn't work for two repos with the same basename
  #gita_path=${XDG_CONFIG_HOME:-$HOME/.config}/gita/repo_path
  #repos=`awk '{split($0, paths, ":")} END {for (i in paths) {n=split(paths[i],b, /\//); print b[n]}}' ${gita_path}`

  # FIXME(Steve-Xyh): the secondary auto-completion(such as `$repos`) contains first commands / 二级补全候选项中包含一级补全中的 `$commands`
  # XXX(Steve-Xyh): the auto-completion is currently case-sensitive / 当前的补全区分大小写, 应该改成大小写不敏感
  # (Steve-Xyh): args in zsh must be `reply` / zsh 中的参数必须为 `reply`
  if [ -z "$cmd" ]; then
    reply=($(compgen -W "${commands}" ${cur}))
  else
    cmd_reply=($(compgen -W "${commands}" ${cmd}))
    case $cmd in
      add)
        reply=(cmd_reply $(compgen -d ${cur}))
        ;;
      ll)
        return
        ;;
      *)
        reply=($cmd_reply $(compgen -W "${repos}" ${cur}))
        ;;
    esac
  fi

}

# (Steve-Xyh): functions in zsh must be `compctl` / zsh 中必须用 compctl 函数, -K 表示使用函数
compctl -K _gita_completions gita


