import os
import requests
import sys
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import hashlib
import logging
import psutil  # 用于关闭主程序
import json
import webbrowser

# 创建log和temp目录
base_path = os.getcwd()
log_dir = os.path.join(base_path, 'log')
temp_dir = os.path.join(base_path, 'temp')
os.makedirs(log_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# 配置日志记录器，确保输出到文件和终端，并设置编码格式
log_file = os.path.join(log_dir, 'app_update.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file, encoding='utf-8'),
                        logging.StreamHandler(sys.stdout)
                    ])
logging.info(f'程序根目录：{base_path}')

DEFAULT_LOGO_URL = "https://gitee.com/xiaoqiangclub/xiaoqiangapps/raw/master/images/xiaoqiangclub_logo.png"
DEFAULT_LOGO_PATH = os.path.join(temp_dir, "logo.png")

root = None  # 全局变量，主窗口


def verify_update(file_path: str, expected_md5: str) -> bool:
    """
    验证更新包的完整性。

    :param file_path: 下载的更新包路径。
    :param expected_md5: 配置文件中提供的更新包的MD5值。
    :return: 如果验证通过返回True，否则返回False。
    """
    local_md5 = calculate_md5(file_path)
    return local_md5 == expected_md5


def calculate_md5(file_path: str) -> str:
    """
    计算文件的MD5哈希值。

    :param file_path: 文件的路径。
    :return: MD5哈希值。
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


def download_update(update_url: str, download_path: str, verify_md5: Optional[str] = None, progress_callback=None) -> \
        Optional[str]:
    """
    从指定的URL下载更新包。

    :param update_url: 更新包的URL。
    :param download_path: 下载更新包的路径。
    :param verify_md5: 校验文件的MD5值。
    :param progress_callback: 用于更新进度条的回调函数。
    :return: 如果成功，则为下载的更新包路径，否则为None。
    """
    try:
        logging.info(f"开始下载更新包：{update_url}")
        response = requests.get(update_url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(download_path, 'wb') as out_file:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024):
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded / total_size * 100, "正在下载更新...")

        if verify_md5:
            logging.info(f"开始验证更新包：{download_path}")
            if not verify_update(download_path, verify_md5):
                logging.error("更新包验证失败。")
                return None

        logging.info(f"下载更新包完成：{download_path}")
        return download_path
    except requests.RequestException as e:
        logging.error(f"下载更新失败: {e}")
        return None


def install_update(download_path: str, install_path: str, progress_callback=None) -> None:
    """
    安装已下载的更新包。

    :param download_path: 下载的更新包路径。
    :param install_path: 更新安装路径。
    :param progress_callback: 用于更新进度条的回调函数。
    """
    try:
        logging.info(f"开始安装更新包：{download_path} 到 {install_path}")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            for index, file in enumerate(zip_ref.infolist()):
                target_path = os.path.join(install_path, file.filename)
                logging.info(f"解压文件：{target_path}")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                if os.path.isdir(target_path):
                    import shutil
                    shutil.rmtree(target_path)
                elif os.path.isfile(target_path):
                    os.remove(target_path)
                zip_ref.extract(file, install_path)
                if progress_callback:
                    progress_callback((index + 1) / total_files * 100, "正在安装更新...")
        logging.info(f"安装更新包完成：{download_path}")
    except zipfile.BadZipFile as e:
        logging.error(f"解压更新失败: {e}")
        raise
    except PermissionError as e:
        logging.error(f"文件权限错误: {e}")
        raise
    except Exception as e:
        logging.error(f"安装更新过程中出现错误: {e}")
        raise


def center_window(window):
    """
    将窗口在屏幕中间显示。

    :param window: 窗口对象。
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


def close_main_app(main_app_name: str):
    """
    尝试关闭主程序以确保文件不会被占用。

    :param main_app_name: 主程序名称。
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == main_app_name:
            logging.info(f"正在关闭主程序：{main_app_name} (PID: {proc.info['pid']})")
            proc.terminate()
            proc.wait(timeout=5)


def find_config_file() -> Optional[str]:
    """
    遍历查找配置文件。

    :return: 配置文件路径，如果找到则返回路径，否则返回None。
    """
    for root, dirs, files in os.walk(base_path):
        if "updater_config.json" in files:
            return os.path.join(root, "../updater_config.json")
    return None


def load_config(config_path: Optional[str] = None) -> dict:
    """
    加载配置文件。

    :param config_path: 配置文件路径，可选。
    :return: 配置字典。
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not os.path.isfile(config_path):
        messagebox.showerror("错误", f"未找到配置文件：{config_path or 'updater_config.json'}")
        logging.error(f"未找到配置文件：{config_path or 'updater_config.json'}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    for key in ['logo_path']:
        if key in config and config[key] and not os.path.isabs(config[key]):
            config[key] = os.path.join(base_path, config[key])

    if not config.get('logo_path'):
        if os.path.exists(DEFAULT_LOGO_PATH):
            config['logo_path'] = DEFAULT_LOGO_PATH
        else:
            config['logo_path'] = DEFAULT_LOGO_URL

    logging.info(f"使用的配置文件路径：{config_path}")

    return config


def show_error_window(parent, update_url, main_app, open_current_version_on_fail, logo_path, config_path):
    """
    显示错误窗口，提供重试、手动更新和取消选项。

    :param parent: 父窗口对象。
    :param update_url: 更新包的下载URL。
    :param main_app: 主程序的路径。
    :param open_current_version_on_fail: 是否在更新失败或取消后打开当前版本的程序。
    :param logo_path: 窗口图标路径。
    :param config_path: 配置文件路径。
    """

    def retry():
        error_window.destroy()
        updater(config_path)

    def manual_update():
        webbrowser.open(update_url)
        error_window.destroy()
        os.startfile(base_path)

    def cancel():
        error_window.destroy()
        if open_current_version_on_fail:
            subprocess.Popen([main_app])
        else:
            sys.exit()

    error_window = tk.Toplevel(parent)
    error_window.title("更新失败")

    if logo_path:
        try:
            error_window.iconphoto(False, tk.PhotoImage(file=logo_path))
        except Exception as e:
            logging.error(f"加载 logo 图片失败: {e}")

    message_label = ttk.Label(error_window, text="更新过程中发生错误，请选择操作：")
    message_label.pack(pady=10)

    button_frame = ttk.Frame(error_window)
    button_frame.pack(pady=10)

    retry_button = ttk.Button(button_frame, text="重试", command=retry)
    retry_button.grid(row=0, column=0, padx=5)

    manual_update_button = ttk.Button(button_frame, text="手动更新", command=manual_update)
    manual_update_button.grid(row=0, column=1, padx=5)

    cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
    cancel_button.grid(row=0, column=2, padx=5)

    center_window(error_window)
    error_window.transient(parent)
    error_window.grab_set()
    parent.wait_window(error_window)


def show_md5_mismatch_window(parent, update_url, main_app, download_path, install_path, logo_path, config_path):
    """
    显示MD5校验失败窗口，提供继续安装、手动安装更新和取消选项。

    :param parent: 父窗口对象。
    :param update_url: 更新包的下载URL。
    :param main_app: 主程序的路径。
    :param download_path: 下载的更新包路径。
    :param install_path: 安装路径。
    :param logo_path: 窗口图标路径。
    :param config_path: 配置文件路径。
    """

    def continue_install():
        md5_window.destroy()
        try:
            window = initialize_gui()
            message_label = ttk.Label(window, text="初始化...")
            message_label.pack(pady=10)

            progress = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
            progress.pack(pady=10)

            center_window(window)
            window.update()

            def update_progress(value, message):
                progress['value'] = value
                message_label.config(text=message)
                window.update()

            install_update(download_path, install_path, update_progress)
            os.remove(download_path)
            update_progress(100, "更新安装完成，正在重启主应用程序...")
            messagebox.showinfo("更新完成", "更新安装完成，程序即将重启。")
            logging.info("更新安装完成，程序即将重启。")
            logging.info(f'运行程序：{main_app}')
            subprocess.Popen([main_app])
            root.destroy()
        except Exception as e:
            logging.error(f"安装更新过程中出现错误: {e}")
            show_error_window(root, update_url, main_app, False, logo_path, config_path)

    def manual_update():
        webbrowser.open(update_url)
        md5_window.destroy()
        os.startfile(base_path)

    def cancel():
        md5_window.destroy()
        subprocess.Popen([main_app])
        sys.exit()

    md5_window = tk.Toplevel(parent)
    md5_window.title("MD5校验失败")

    if logo_path:
        try:
            md5_window.iconphoto(False, tk.PhotoImage(file=logo_path))
        except Exception as e:
            logging.error(f"加载 logo 图片失败: {e}")

    message_label = ttk.Label(md5_window, text="MD5校验失败，继续安装可能有风险，请选择操作：")
    message_label.pack(pady=10)

    button_frame = ttk.Frame(md5_window)
    button_frame.pack(pady=10)

    continue_button = ttk.Button(button_frame, text="继续安装", command=continue_install)
    continue_button.grid(row=0, column=0, padx=5)

    manual_update_button = ttk.Button(button_frame, text="手动更新", command=manual_update)
    manual_update_button.grid(row=0, column=1, padx=5)

    cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
    cancel_button.grid(row=0, column=2, padx=5)

    center_window(md5_window)
    md5_window.transient(parent)
    md5_window.grab_set()
    parent.wait_window(md5_window)


def initialize_gui() -> tk.Tk:
    """
    初始化并返回主GUI窗口。
    """
    global root
    if root is None:
        root = tk.Tk()
        root.title("自动更新")
    return root


def set_logo(window, logo_path):
    """
    设置窗口的logo图标。

    :param window: 窗口对象。
    :param logo_path: logo路径。
    """
    if logo_path.startswith("http://") or logo_path.startswith("https://"):
        try:
            response = requests.get(logo_path)
            response.raise_for_status()
            with open(DEFAULT_LOGO_PATH, 'wb') as logo_file:
                logo_file.write(response.content)
            logo_path = DEFAULT_LOGO_PATH
        except requests.RequestException as e:
            logging.error(f"下载 logo 图片失败: {e}")
            logo_path = None

    if logo_path:
        try:
            window.iconphoto(False, tk.PhotoImage(file=logo_path))
        except Exception as e:
            logging.error(f"加载 logo 图片失败: {e}")


def updater(config_path: Optional[str] = None) -> None:
    """
    执行更新过程的主函数。

    :param config_path: 配置文件路径，可选。
    """
    config = load_config(config_path)

    current_version = config.get("current_version")
    latest_version = config.get("latest_version")
    update_url = config.get("update_url")
    main_app = config.get("main_app")
    verify_file_md5 = config.get("verify_file_md5")
    logo_path = config.get("logo_path")
    open_current_version_on_fail = config.get("open_current_version_on_fail", False)
    install_dir = config.get("install_dir")

    # 如果 install_dir 未定义或为空字符串，则将其设置为 base_path
    if not install_dir:
        install_dir = base_path
    elif not os.path.isabs(install_dir):
        install_dir = os.path.join(base_path, install_dir)

    if current_version is None or latest_version is None or update_url is None or main_app is None or verify_file_md5 is None:
        messagebox.showerror("错误", "配置文件中缺少必要的参数。")
        logging.error("配置文件中缺少必要的参数。")
        sys.exit(1)

    logging.info(f"当前版本：{current_version}，最新版本：{latest_version}")
    if current_version >= latest_version:
        logging.info("当前已是最新版本，无需更新。")
        return

    main_app = os.path.join(install_dir, main_app)

    main_app_name = os.path.basename(main_app)
    close_main_app(main_app_name)

    window = initialize_gui()
    set_logo(window, logo_path)

    message_label = ttk.Label(window, text="初始化...")
    message_label.pack(pady=10)

    progress = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=10)

    center_window(window)
    window.update()

    def update_progress(value, message):
        progress['value'] = value
        message_label.config(text=message)
        window.update()

    download_path = os.path.join(temp_dir, "updater.zip")
    update_progress(0, "正在下载更新...")
    downloaded_file = download_update(update_url, download_path, verify_file_md5, update_progress)
    if downloaded_file is None:
        show_md5_mismatch_window(window, update_url, main_app, download_path, install_dir, logo_path, config_path)
        return

    update_progress(0, "正在安装更新...")
    try:
        install_update(downloaded_file, install_dir, update_progress)
    except Exception as e:
        logging.error(f"安装更新过程中出现错误: {e}")
        show_error_window(window, update_url, main_app, open_current_version_on_fail, logo_path, config_path)
        return

    os.remove(downloaded_file)

    update_progress(100, "更新安装完成，正在重启主应用程序...")
    messagebox.showinfo("更新完成", "更新安装完成，程序即将重启。")
    logging.info("更新安装完成，程序即将重启。")
    logging.info(f'运行程序：{main_app}')
    subprocess.Popen([main_app])

    window.destroy()


def print_logo():
    """
    打印程序的logo。
    """
    logo_text = """
            /$$   /$$ /$$                               /$$                                /$$$$$$  /$$           /$$      
           | $$  / $$|__/                              |__/                               /$$__  $$| $$          | $$      
           |  $$/ $$/ /$$  /$$$$$$   /$$$$$$   /$$$$$$  /$$  /$$$$$$  /$$$$$$$   /$$$$$$ | $$  \__/| $$ /$$   /$$| $$$$$$$ 
            \  $$$$/ | $$ |____  $$ /$$__  $$ /$$__  $$| $$ |____  $$| $$__  $$ /$$__  $$| $$      | $$| $$  | $$| $$__  $$
             >$$  $$ | $$  /$$$$$$$| $$  \ $$| $$  \ $$| $$  /$$$$$$$| $$  \ $$| $$  \ $$| $$      | $$| $$  | $$| $$  \ $$
            /$$/\  $$| $$ /$$__  $$| $$  | $$| $$  | $$| $$ /$$__  $$| $$  | $$| $$  | $$| $$    $$| $$| $$  | $$| $$  | $$
           | $$  \ $$| $$|  $$$$$$$|  $$$$$$/|  $$$$$$$| $$|  $$$$$$$| $$  | $$|  $$$$$$$|  $$$$$$/| $$|  $$$$$$/| $$$$$$$/
           |__/  |__/ \_______/ \______/  \____  $$|__/ \_______/|__/  |__/ \____  $$ \______/ |__/ \______/ |_______/ 
                                                   | $$                         /$$  \ $$                                  
                                                   | $$                        |  $$$$$$/                                  
                                                   |__/                         \______/                                   
           """
    print(logo_text)


def print_usage():
    """
    打印程序的用法信息，并展示配置文件示例。
    """

    usage_text = """
    配置文件示例 (updater_config.json):
    {
        "current_version": "1.0.0",
        "latest_version": "1.1.0",
        "update_url": "http://example.com/update.zip",
        "main_app": "path/to/main_app.exe",
        "verify_file_md5": "d41d8cd98f00b204e9800998ecf8427e",
        "logo_path": "path/to/logo.png",
        "open_current_version_on_fail": true,
        "install_dir": "path/to/install/directory"  # 可选，默认值为updater所在目录
    }

    调用方法：
    updater.exe <config_path>
    config_path: 配置文件的路径。例如，updater.exe C:\\path\\to\\updater_config.json

    可选参数：
    --help, -h: 显示此帮助信息并退出
    """
    print(usage_text)


def handle_arguments():
    """
    处理命令行参数。
    """
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print_logo()
            print_usage()

            sys.exit(0)
        else:
            config_path = sys.argv[1]
            updater(config_path)
    else:
        print_logo()
        updater()


if __name__ == "__main__":
    handle_arguments()
