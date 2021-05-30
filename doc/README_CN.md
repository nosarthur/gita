[![PyPi version](https://img.shields.io/pypi/v/gita.svg?color=blue)](https://pypi.org/project/gita/)
[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
[![codecov](https://codecov.io/gh/nosarthur/gita/branch/master/graph/badge.svg)](https://codecov.io/gh/nosarthur/gita)
[![licence](https://img.shields.io/pypi/l/gita.svg)](https://github.com/nosarthur/gita/blob/master/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gita.svg)](https://pypistats.org/packages/gita)
[![Gitter](https://badges.gitter.im/nosarthur/gita.svg)](https://gitter.im/nosarthur/gita?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![English](https://img.shields.io/badge/-English-lightgrey.svg)](https://github.com/nosarthur/gita)

```
 _______________________________
(  ____ \__   __|__   __(  ___  )
| (    \/  ) (     ) (  | (   ) |
| |        | |     | |  | (___) |
| | ____   | |     | |  |  ___  |
| | \_  )  | |     | |  | (   ) |
| (___) |__) (___  | |  | )   ( |
(_______)_______/  )_(  |/     \|   v0.13
```

# Gita：一个管理多个 git 库的命令行工具

这个工具有两个功能:

- 并排显示多个库的状态信息，比如分支名，编辑状态，提交信息等
- 在任何目录下（批处理）代理执行 git 指令

![gita screenshot](https://github.com/nosarthur/gita/raw/master/doc/screenshot.png)

本地和远程分支之间的关系有5种情况，在这里分别用5种颜色对应着：

- 绿色：本地和远程保持一致
- 红色：本地和远程产生了分叉
- 黄色：本地落后于远程（适合合并merge）
- 白色：本地没有指定远程
- 紫色：本地超前于远程（适合推送push）

为什么选择了紫色作为超前以及黄色作为落后，绿色作为基准 的理由在这两篇文章中解释：
[blueshift](https://en.wikipedia.org/wiki/Blueshift)、[redshift](https://en.wikipedia.org/wiki/Redshift)

额外的状态符号意义：

- `+`: 暂存(staged)
- `*`： 未暂存（unstaged）
- `_`： 未追踪（untracked）

基础指令：

- `gita add <repo-path(s)>`: 添加库
- `gita add -r <repo-parent-path(s)>`:
- `gita clone <config-file>`:
- `gita context`: 情境命令
    - `gita context`: 显示当前的情境
    - `gita context none`: 去除情境
    - `gita context <group-name>`: 把情境设置成`group-name`, 之后所有的操作只作用到这个组里的库
- `gita color`:
    - `gita color [ll]`:
    - `gita color set <situation> <color>`:
- `gita flags`:
    - `gita flags set <repo-name> <"flags">`:
    - `gita flags [ll]`:
- `gita freeze`
- `gita group`: 组群命令
    - `gita group add <repo-name(s)>`: 把库加入新的或者已经存在的组
    - `gita group [ll]`: 显示已有的组和它们的库
    - `gita group ls`: 显示已有的组名
    - `gita group rename <group-name> <new-name>`: 改组名
    - `gita group rm group(s): 删除组
    - `gita group rmrepo -n <group-name>:
- `gita info`: 显示已用的和未用的信息项
    - `gita info [ll]`
    - `gita info add <info-item>`
    - `gita info rm <info-item>`
- `gita ll`: 显示所有库的状态信息
- `gita ll <group-name>`: 显示一个组群中库的状态信息
- `gita ls`: 显示所有库的名字
- `gita ls <repo-name>`: 显示一个库的绝对路径
- `gita rename <repo-name> <new-name>`: 重命名一个库
- `gita rm <repo-name(s)>`: 移除库（不会删除文件）
- `gita -v`: 显示版本号

库的路径存在`$XDG_CONFIG_HOME/gita/repo_path` (多半是`~/.config/gita/repo_path`)。

代理执行的子命令有两种格式：

- `gita <sub-command> [repo-name(s) or group-name(s)]`: 库名或组群名是可选的，缺失表示所有库
- `gita <sub-command> <repo-name(s) or group-name(s)>`: 必须有库名或组群名

默认只有`fetch`和`pull`是第一种格式。

如果输入了多个库名，
而且被代理的git指令不需要用户输入，
那么各个库的代理指令会被异步执行。

## 安装指南

正常人类按装：

```
pip3 install -U gita
```

神奇码农安装：先下载源码，然后

```
pip3 install -e <gita-source-folder>
```

装完之后在命令行下执行`gita`可能还不行。那就把下面这个昵称放到`.bashrc`里。
```
alias gita="python3 -m gita"
```

Windows用户可能需要额外的设置来支持彩色的命令行， 见[这个帖子](https://stackoverflow.com/questions/51680709/colored-text-output-in-powershell-console-using-ansi-vt100-codes)。

## 自动补全

下载
[.gita-completion.bash](https://github.com/nosarthur/gita/blob/master/.gita-completion.bash)
并在`.bashrc`里点它。

## 超人模式

超人模式可以代理执行任何git命令/别名。它的格式是

```
gita super [repo-name(s) or group-name(s)] <any-git-command-with-or-without-options>
```

其中库名或组群名是可有可无的。举几个例子

- `gita super checkout master`会把所有库都弄到主库杈上
- `gita super frontend-repo backend-repo commit -am 'implement a new feature'`
  会对`frontend-repo`和`backend-repo`运行`git commit -am 'implement a new feature'`

## 私人定制

定制的代理子命令要放在`$XDG_CONFIG_HOME/gita/cmds.yml` (多半是`~/.config/gita/cmds.yml`)。
如果存在命名冲突，它们会覆盖掉默认的指令。

默认代理子指令的定义可见
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml)。
举个栗子，`gita stat <repo-name(s)>`的定义是

```yaml
stat:
  cmd: diff --stat
  help: show edit statistics
```

它会执行`git diff --stat`。

如果被代理的指令是一个单词，`cmd`也可以省略。比如`push`。
如果要取消异步执行，把`disable_async`设成`true`。比如`difftool`。

如果你想让定制的命令跟`gita fetch`等命令一样，可以作用于所有的库，
就把`allow_all`设成`true`。
举个栗子，`gita comaster [repo-names(s)]`会生成一个新的定制命令，对于这个命令，库名是可选输入。comaster的解释如下：

```yaml
comaster:
  cmd: checkout master
  allow_all: true
  help: checkout the master branch
```
另一个自定义功能是针对`gita ll`展示的信息项。
`gita info`可以展示所有用到的和没用到的信息项，并且可以通过修改`$XDG_CONFIG_HOME/gita/info.yml`支持自定义。举个栗子，默认的信息项显示配置相当于是：

```yaml
- branch
- commit_msg
- commit_time
```
为了创建自己的信息项，命名一个目录为`extra_info_items`。
在`$XDG_CONFIG_HOME/gita/extra_repo_info.py`中，要把信息项的名字作为字符串映射到方法中，该方法将库的路径作为输入参数。举个栗子：

```python
def get_delim(path: str) -> str:
    return '|'

extra_info_items = {'delim': get_delim}
```
如果没有遇到问题，你会在`gita info`的输出内容中的`unused`小节中看到这些额外信息项。

## 先决条件

因为用了[f-string](https://www.python.org/dev/peps/pep-0498/)
和[asyncio module](https://docs.python.org/3.6/library/asyncio.html)，系统必须要用Python 3.6或以上。

暗地里老夫用`subprocess`来代理执行git指令。所以git的版本有可能会影响结果。
经测试，`1.8.3.1`, `2.17.2`, 和`2.20.1`的结果是一致的。

## 有所作为

要想有所作为，你可以

- 报告/治理虫子
- 建议/实现功能
- 加星/推荐本作

聊天请入[![Join the chat at https://gitter.im/nosarthur/gita](https://badges.gitter.im/nosarthur/gita.svg)](https://gitter.im/nosarthur/gita?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

在本地跑单元测试可以直接用`pytest`。更多的细节可见
[design.md](https://github.com/nosarthur/gita/blob/master/doc/design.md)。

如果你愿意资助我，请访问[GitHub Sponsors](https://github.com/sponsors/nosarthur)。

## 他山之石

没用过，听说不错

- [myrepos](https://myrepos.branchable.com/)
- [repo](https://source.android.com/setup/develop/repo)
