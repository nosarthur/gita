[![PyPi version](https://img.shields.io/pypi/v/gita.svg?color=blue)](https://pypi.org/project/gita/)
[![Build Status](https://travis-ci.org/nosarthur/gita.svg?branch=master)](https://travis-ci.org/nosarthur/gita)
[![codecov](https://codecov.io/gh/nosarthur/gita/branch/master/graph/badge.svg)](https://codecov.io/gh/nosarthur/gita)
[![licence](https://img.shields.io/pypi/l/gita.svg)](https://github.com/nosarthur/gita/blob/master/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gita.svg)](https://pypistats.org/packages/gita)
[![English](https://img.shields.io/badge/-English-lightgrey.svg)](https://github.com/nosarthur/gita)

```
 _______________________________
(  ____ \__   __|__   __(  ___  )
| (    \/  ) (     ) (  | (   ) |
| |        | |     | |  | (___) |
| | ____   | |     | |  |  ___  |
| | \_  )  | |     | |  | (   ) |
| (___) |__) (___  | |  | )   ( |
(_______)_______/  )_(  |/     \|   v0.8
```

# git 啊：管理多个 git 库的命令行工具

老夫有两把刷子：

- 同时显示多个库的状态信息，比如树杈名，编辑状态，贡献信息
- 在任何目录下代理执行 git 指令

![gita screenshot](https://github.com/nosarthur/gita/raw/master/screenshot.png)

树杈的五色代表了本土和远程树杈相生相杀的关系：

- 青：远近一致
- 赤：本土已与远程分道扬镳
- 黄：本土落后于远程（宜和合merge）
- 白：没有远程
- 紫：本土超前于远程（宜推送push）

如果你知道蓝移和红移的道理，就会明白为什么黄色表示落后，紫色表示超前。

编辑状态符号：

- `+`: 已上台(staged)
- `*`：未上台(unstaged)
- `_`：未追踪(untracked)

基础指令：

- `gita add <repo-path(s)>`: 为老夫添加库
- `gita rm <repo-name(s)>`: 取消库（不会删除文件）
- `gita ll`: 显示所有库的信息
- `gita ls`: 显示所有库的名字
- `gita ls <repo-name>`: 显示一个库的绝对路径
- `gita -v`: 显示老夫的版本号

库的路径存在`$XDG_CONFIG_HOME/gita/repo_path` (多半是`~/.config/gita/repo_path`)。

代理执行的命令有两种格式：

- `gita <sub-command> [repo-name(s)]`: 可有可无的库名，没有库名即是所有库名
- `gita <sub-command> <repo-name(s)>`: 必须有库名

默认只有`fetch`和`pull`是第一种格式。如果输入了多个库名，
而且被代理的git指令不需要用户输入，
那么各个库的代理指令会被异步执行。

## 私人定制

定制的代理指令要放在`$XDG_CONFIG_HOME/gita/cmds.yml` (多半是`~/.config/gita/cmds.yml`)。
它们会覆盖掉默认的指令。

默认指令的定义可见
[cmds.yml](https://github.com/nosarthur/gita/blob/master/gita/cmds.yml).
举个栗子，`gita stat <repo-name(s)>`的定义是

```yaml
stat:
  cmd: diff --stat
  help: show edit statistics
```

它会执行`git diff --stat`.

如果被代理的指令是一个单词，`cmd`也可以省略。比如`push`。
如果要取消异步执行，把`disable_async`设成`true`。比如`difftool`。

如果你想让定制的命令跟`gita fetch`似的支持莫须有的库名，
把`allow_all`设成`true`。
举个栗子，下面这个定义会生成一个`gita comaster [repo-names(s)]`的定制命令

```yaml
comaster:
  cmd: checkout master
  allow_all: true
  help: checkout the master branch
```

## 超人模式

超人模式可以代理执行任何git命令。它的格式是

```
gita super [repo-name(s)] <any-git-command-with-or-without-options>
```

其中库名是可有可无的。举几个例子

- `gita super checkout master`会把所有库都弄到主树杈上
- `gita super frontend-repo backend-repo commit -am 'implement a new feature'`
  会对`frontend-repo`和`backend-repo`运行`git commit -am 'implement a new feature'`

## 先决条件

老夫用了[f-string](https://www.python.org/dev/peps/pep-0498/)
和[asyncio module](https://docs.python.org/3.6/library/asyncio.html)，所以必须要用Python 3.6或以上。

暗地里老夫用`subprocess`来代理执行git指令。所以git的版本有可能会影响结果。
经测试，`1.8.3.1`, `2.17.2`, 和`2.20.1`的结果是一致的。

## 安装指南

正常人类按装：

```
pip3 install -U gita
```

神奇码农安装：先下载源码，然后

```
pip3 install -e <gita-source-folder>
```

装完之后在命令行下执行`gita`可能还不行。可以把下面这个昵称放到`.bashrc`里。
```
alias gita="python3 -m gita"
```

## 自动补全

下载
[.gita-completion.bash](https://github.com/nosarthur/gita/blob/master/.gita-completion.bash)
并在`.bashrc`里点它。

## 有所作为

要想有所作为，你可以

- 报告/治理虫子
- 建议/实现功能
- 加星/推荐老夫

在本地跑单元测试可以直接用`pytest`。更多的细节可见
[design.md](https://github.com/nosarthur/gita/blob/master/design.md)。

## 他山之石

没用过，听说不错

- [myrepos](https://myrepos.branchable.com/)
- [repo](https://source.android.com/setup/develop/repo)
