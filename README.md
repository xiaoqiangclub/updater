<p align="center"><a href="https://github.com/xiaoqiangclub/updater"><img width="200" src="img/app_logo.png" alt="Project logo"></a></p>

<p align="center">
  <a href="https://github.com/xiaoqiangclub/updater/releases"><img src="https://img.shields.io/github/release/xiaoqiangclub/updater" alt="Release version"></a>
  <a href="https://github.com/xiaoqiangclub/updater/actions/workflows/release.yml"><img src="https://github.com/xiaoqiangclub/updater/workflows/Build/badge.svg" alt="Build status"></a>
  <a href="https://github.com/xiaoqiangclub/updater/actions/workflows/beta-pack.yml"><img src="https://github.com/xiaoqiangclub/updater/workflows/Build%20Beta/badge.svg" alt="Build status"></a>
  <a href="https://www.python.org/downloads/release/python-3115/"><img src="https://img.shields.io/badge/Python-3.11.5-blue" alt="Python version"></a>
  <a href="https://github.com/xiaoqiangclub/updater/tree/dev"><img src="https://img.shields.io/github/package-json/v/xiaoqiangclub/updater/dev" alt="Dev branch version"></a>
  <a href="https://github.com/xiaoqiangclub/updater/blob/master/LICENSE"><img src="https://img.shields.io/github/license/xiaoqiangclub/updater" alt="License"></a>
</p>

# 自动更新模块

这是一个通用的自动更新模块，适用于任何Python项目。该模块包括一个独立的更新程序，能够检测、下载和安装更新，并重启主应用程序。

## 实现原理

该模块通过检查当前版本和最新版本之间的差异，从指定的URL下载更新包，并验证其完整性。然后将更新包解压到指定的安装路径，并重启主应用程序。

## 技术栈

- Python 3.11.5
- requests
- tkinter
- psutil

## 安装

使用 pip 安装：

```sh
pip install updater
```

## 使用说明

### 参数说明

使用更新程序 `updater.py` 时，可以指定以下参数：

- `--config <配置文件路径>`：配置文件路径（默认为 `updater_config.json`）。
- `--help`：显示此帮助信息并退出。

### 配置文件说明

示例配置文件 `updater_config.json` 的内容如下：

```json
{
  "current_version": "1.0.0",
  "latest_version": "1.1.0",
  "update_url": "http://example.com/updater.zip",
  "main_app": "app.exe",
  "verify_file_md5": "d41d8cd98f00b204e9800998ecf8427e",
  "logo_path": "path/to/logo.png",
  "open_current_version_on_fail": true,
  "install_dir": "path/to/install/directory"
}
```

### 配置项说明

- `current_version`：当前版本号。
- `latest_version`：最新版本号。
- `update_url`：更新包的下载URL。
- `main_app`：主程序的路径（相对路径：一般都是放在根目录下的exe入口文件）。
- `verify_file_md5`：更新包校验文件的MD5值。
- `logo_path`：图形用户界面的图标路径（可选）。
- `open_current_version_on_fail`：更新失败或取消时是否打开当前版本的程序。
- `install_dir`：软件解压更新的目录（可选）。默认是 `updater.exe` 所在的目录。

**注意：**

1. 模块会自动使用 `updater.exe` 文件所在的目录与设置的相对路径或目录名进行拼接！
2. 如果没有指定具体的配置文件路径，程序将自动在当前目录下遍历查找一个名叫 `updater_config.json` 的配置文件。

### 打包更新程序

你可以使用两种方式将 `updater.py` 打包成可执行文件。

#### 使用 PyInstaller 打包

1. 安装 PyInstaller：

    ```sh
    pip install pyinstaller
    ```

2. 使用 PyInstaller 打包命令：

    ```sh
    pyinstaller --onefile --noconsole --distpath=dist --name=updater --icon="path/to/icon.ico" updater.py
    ```

#### 使用 Nuitka 打包

1. 安装 Nuitka：

    ```sh
    pip install nuitka
    ```

2. 使用 Nuitka 打包命令：

    ```sh
    nuitka --onefile --windows-disable-console --output-dir=dist --output-filename=updater.exe --enable-plugin=tk-inter --windows-icon-from-ico="path/to/icon.ico" updater.py
    ```

### 在主程序中生成适合 `updater` 的配置文件

在主程序中生成一个适合 `updater` 的配置文件示例：

```python
import json
import os


def generate_config():
    config = {
        "current_version": "1.0.0",
        "latest_version": "使用代码从服务器或其他方式获取",
        "update_url": "使用代码从服务器或其他方式获取",
        "main_app": "path/to/main_app.exe",  # 主程序的入口文件，确保每个版本的主程序入口文件名都相同
        "verify_file_md5": "使用代码从服务器或其他方式获取",  # 可以调用模块的calculate_md5()方法来生成md5再放到服务器
        "logo_path": "path/to/logo.png",  # 升级程序的logo图标，可以省略
        "open_current_version_on_fail": True,  # 如果更新失败，是否打开当前版本的应用程序
        "install_dir": ""  # 可选，默认值为updater所在目录
    }
    config_path = os.path.join(os.getcwd(), "updater_config.json")
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=4)
    print(f"配置文件已生成：{config_path}")


if __name__ == "__main__":
    generate_config()
```

### 调用打包后的可执行文件

在主应用程序中调用打包后的可执行文件：

```python
import os
import subprocess
import sys


def updater():
   try:
      updater_path = os.path.join(os.getcwd(), "tests/updater.exe")
      subprocess.Popen([updater_path, "--config", "path/to/updater_config.json"])
      sys.exit()
   except Exception as e:
      print(f"检查更新时出错: {e}")


if __name__ == "__main__":
   updater()
```

### 直接调用 `updater.py` 中的 `updater` 函数（仅用于测试）

在主程序中直接调用 `updater.py` 中的 `updater` 函数进行测试：

```python
import sys
from updater import handle_arguments


def updater():
   try:
      handle_arguments()
      sys.exit()
   except Exception as e:
      print(f"检查更新时出错: {e}")


if __name__ == "__main__":
   updater()
```

**注意**：直接调用 `updater.py` 中的 `handle_arguments` 函数只能用于测试。在生产环境中，请调用打包后的exe文件，以避免文件占用等问题。

### 示例

假设配置文件路径为 `path/to/updater_config.json`，使用以下命令启动更新程序：

```sh
updater.exe --config path/to/updater_config.json
```

在开发过程中，如果主程序尚未打包成可执行文件，可以传递 `.py` 文件路径作为 `main_app` 参数。

### 测试示例

以下是一个测试示例，展示如何在主程序中调用 `updater.py` 进行测试：

```python
# _*_ coding : UTF-8 _*_
# 开发人员： Xiaoqiang
# 微信公众号: xiaoqiangclub
# 开发时间： 2024/5/25 11:01
# 文件名称： app.py
# 项目描述： 测试程序
# 开发工具： PyCharm
import os
import json
import subprocess
import sys
import tkinter as tk
from tkinter import ttk


def app():
   root = tk.Tk()
   root.title("XiaoqiangClub")

   # 设置窗口大小
   root.geometry("400x200")

   # 设置窗口图标
   try:
      root.iconphoto(True, tk.PhotoImage(file="xiaoqiangclub_logo.png"))
   except Exception as e:
      print(f"Error loading logo: {e}")

   # 创建标签
   label = ttk.Label(root, text="XiaoqiangClub v1.0.0", font=("Helvetica", 24))
   label.pack(expand=True)

   root.mainloop()


def generate_config():
   config = {
      "current_version": "1.0.0",
      "latest_version": "使用代码从服务器或其他方式获取",
      "update_url": "使用代码从服务器或其他方式获取",
      "main_app": "path/to/main_app.exe",  # 主程序的入口文件，确保每个版本的主程序入口文件名都相同
      "verify_file_md5": "使用代码从服务器或其他方式获取",  # 可以调用模块的calculate_md5()方法来生成md5再放到服务器
      "logo_path": "path/to/logo.png",  # 升级程序的logo图标，可以省略
      "open_current_version_on_fail": True,  # 如果更新失败，是否打开当前版本的应用程序
      "install_dir": ""  # 可选，默认值为updater所在目录
   }
   config_path = os.path.join(os.getcwd(), "updater_config.json")
   with open(config_path, 'w', encoding='utf-8') as config_file:
      json.dump(config, config_file, ensure_ascii=False, indent=4)
   print(f"配置文件已生成：{config_path}")


# 用于生产环境调用exe文件
def main():
   try:
      # 生成配置文件
      generate_config()
      updater_path = os.path.join(os.getcwd(), "tests/updater.exe")
      subprocess.Popen([updater_path])
      sys.exit()
   except Exception as e:
      print(f"检查更新时出错: {e}")


# 仅用于测试，调用updater.py中的handle_arguments函数
from updater import handle_arguments


def main_test():
   try:
      # 生成配置文件
      generate_config()
      handle_arguments()
      sys.exit()
   except Exception as e:
      print(f"检查更新时出错: {e}")


if __name__ == "__main__":
   # 生产环境使用：
   # main()

   # 测试使用：
   main_test()
```

## 注意事项

- 请确保更新URL和文件路径正确，并且更新包完整。
- 为了确保安全，建议验证下载文件的完整性。
- 请根据实际情况修改主应用程序中的更新检查逻辑和参数配置。