# Overleaf同步工具

## 介绍

这是一个基于python selenium+watchdog开发的Overleaf同步工具。Overleaf的编辑器已经无力再吐槽，然而它强大的实时编译和渲染又使得我们很难拒绝它。这个项目可以使你在本地编辑器写latex并实时将数据同步到Overleaf中，使得你既能在本地的编辑器写又能用上Overleaf的实时编译、渲染。

## 环境配置

### Chromedriver配置

项目使用了Chromedriver作为Overleaf的浏览器，使用之前请先配置好Chromedriver，如果你是windows用户请参考[配置方法](https://blog.csdn.net/harry5508/article/details/89226253)，其他平台的用户大概都是Geeker直接默认会了。

###安装依赖包

该程序依赖于<code>requests + watchdog + fire + selenium</code>，在使用前请先安装好这写依赖包，可以通过以下命令

```bash
pip install -r requirements.txt
```

或者自行安装。

## 使用方法

1. 在命令行中执行

```bash
python main.py \
--work_dir=/path/to/your/latex/project \
--url=<your overleaf website url> \
--email=<your overleaf email> \
--password=<your overleaf password>
```

其中work_dir为你的latex项目路径默认为当前路径，<code>url</code>、<code>email</code>、<code>password</code>为你的overleaf地址、用户邮箱、密码，这三项仅为方便登陆使用，可以不设置。

2. 如果你配置好了Chromedriver，程序运行后会弹出Chrome浏览器窗口。如果你设置了<code>url</code>、<code>email</code>和<code>password</code>，程序将会自动登录。
3. 在Overleaf中进入任意的一个project页面，程序自动监测到该页面后便开始监听你所设置的工作路径，当工作路径内文件发生变化时，文件会自动同步到Overleaf网页端中。
4. 创建一个.tex文件试试吧！

# Overleaf Synchonizer

## Introduction

This is a synchonizing tools that can automatically synchonize your local latex code and your online Overleaf project. It's developed by python selenium + watchdog

## Setup

### Chromedriver Setup

If you haven't setup chromedriver, you can setup followd by [this page](https://blog.testproject.io/2019/07/16/installing-selenium-webdriver-using-python-chrome/).

### Install the requirements

Run the following command in your shell.

```bash
pip install -r requirements.txt
```

Or you can install the requirements listed in the <code>requirements.txt</code> by yourself.

## Usage

1. Run

```bash
python main.py \
--work_dir=/path/to/your/latex/project \
--url=<your overleaf website url> \
--email=<your overleaf email> \
--password=<your overleaf password>
```

where <code>work_dir</code> is the directory of you latex project. <code>url</code>, <code>email</code>, <code>password</code> are your overleaf url, email, password separetely.

2. If you have correctly setuped chromedriver and have passed url, email and password, there will be a new Chrome window and it will directly login.

3. Enter a project and then the file watcher will start.

4. Create your first tex file and try it out.