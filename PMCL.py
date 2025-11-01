import minecraft_launcher_lib
import subprocess
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
from PIL import Image, ImageTk
import threading
import urllib.error
import urllib.request
import urllib.parse
import json
import uuid
import time

class MinecraftLauncherGUI:
    def __init__(self, root):
        try:
            # 创建窗口
            self.root = root
            self.root.title("Python Minecraft Launcher")
            self.root.geometry(f"800x700+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-700)/2)}")
            
            # 记录日志
            self.start_time = int(time.time())

            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
                print(f"[{time.asctime()}] 程序开始运行")
                f.write(f"[{time.asctime()}] 程序开始运行\n")
            
            # 使用 PIL 打开PNG图片
            image = Image.open(self.resource_path('PMCL.png'))
            photo = ImageTk.PhotoImage(image)
            
            # 设置窗口图标
            self.root.iconphoto(True, photo)

            # 绑定退出事件
            self.root.protocol("WM_DELETE_WINDOW", self._exit)
            
            # Minecraft目录
            # self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            self.minecraft_directory = f'{os.path.abspath("")}/.minecraft'

            
            # 初始化设置
            self.use_custom_java = True
            self.use_java = False
            self.java_path = None
            self.skin_path = None
            self.memory = None

            # 启动器配置文件
            if not os.path.exists(f'{self.minecraft_directory}'):
                os.makedirs(self.minecraft_directory)
            if not os.path.exists(f'{self.minecraft_directory}/launcher_profiles.json'):
                with open(f'{self.minecraft_directory}/launcher_profiles.json','w') as launcher_profiles:
                    launcher_profiles.write("""{
  "profiles":  {
    "PMCL": {
      "icon": "Grass",
      "name": "PMCL",
      "lastVersionId": "latest-release",
      "type": "latest-release",
      "lastUsed": "2025-08-27T08:09:00.0000Z"
    }
  },
  "selectedProfile": "PMCL",
  "clientToken": "23323323323323323323323323323333"
}""")
        
            # 初始化版本列表
            self.version_list = []
            self.installed_versions = []

            # 初始化版本隔离
            self.isolation_var = tk.BooleanVar()
            self.isolation_dir = ''
            
            # 创建界面
            self.create_widgets()

            # 创建菜单
            self.create_menu()
            
            # 获取版本列表
            self.load_installed_versions()

            # 尝试从配置文件加载设置
            self.load_settings()
            
            # 加载LittleSkin设置
            self.load_littleskin_credentials()

            # 检查更新
            self.check_update(False)
        except Exception as e:
            messagebox.showerror("错误", f"程序初始化失败：{e}")
            sys.exit(-1)

    def resource_path(self, relative_path):
        """获取资源的绝对路径"""
        try:
            # Nuitka 打包后，__file__ 指向临时目录或可执行文件位置
            base_path = os.path.dirname(os.path.abspath(__file__))
        except:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def get_from_server(self, url):
        """从PMCL服务器获取文件"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        req = urllib.request.Request(url, headers=headers)
    
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read()
            
            # 返回获取到的数据
            return data
        except Exception as e:
            self.log(f"请求失败: {e}", "ERROR")
            messagebox.showerror("错误", f"请求失败: {e}")

    def check_update(self, from_menu):
        """检查更新"""
        try:
            # 获取最新版本
            check_update = self.get_from_server('https://pmcldownloadserver.dpdns.org/latest_version.json').decode('utf-8')
            
            current_version = '1.1.1.1'
            have_later_version = False

            # 获取更新日志
            patch_notes = json.loads(check_update).get('patch_notes', '')
            
            # 一级一级版本号比对
            for i, version_name in enumerate(json.loads(check_update).get('latest_version', '0')):
                if i % 2 == 0:
                    if int(version_name) > int(current_version[i]):
                        have_later_version = True

            # 如果存在更新版本，下载它
            if have_later_version:
                version = json.loads(check_update).get('latest_version')
                if messagebox.askyesno("提示", f"存在新版本：{version[:-2] if not int(version[6]) else version[:-2] + '-hotfix.' + version[-1]}，更新内容：{patch_notes}，是否更新？"):
                    # 创建一个顶层窗口来显示进度条
                    progress_window = tk.Toplevel(self.root)
                    progress_window.title("下载进度")
                    progress_window.geometry("300x100")

                    progress_window.resizable(False, False)
                    progress_window.transient(self.root)
                    progress_window.grab_set()
                    
                    # 添加进度条
                    progress_label = ttk.Label(progress_window, text="正在下载最新版本...")
                    progress_label.pack(pady=5)

                    progress_info_label = ttk.Label(progress_window, text="")
                    progress_info_label.pack(pady=5)
                    
                    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=280, mode="determinate")
                    progress_bar.pack(pady=10)
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                    }
                    req = urllib.request.Request('https://pmcldownloadserver.dpdns.org/PMCL.exe', headers=headers)
                    response = urllib.request.urlopen(req)
                    
                    # 获取文件大小
                    total_size = int(response.info().get('Content-Length', '0'))
                    progress_bar["maximum"] = total_size

                    # 下载文件并更新进度条
                    def download_with_progress():
                        downloaded = 0
                        with open('update.exe', 'wb') as f:
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress_info_label["text"] = f"{self.format_file_size(downloaded)}/{self.format_file_size(total_size)} {downloaded / total_size * 100:.1f}%"
                                progress_bar["value"] = downloaded
                                progress_window.update_idletasks()

                        # 下载完成后关闭进度窗口并继续更新过程
                        progress_window.destroy()
                        self.install_update()

                    # 在新线程中下载更新
                    download_update_thread = threading.Thread(target=download_with_progress)
                    download_update_thread.daemon = True
                    download_update_thread.start()

            elif from_menu:
                messagebox.showinfo("提示", "已是最新版本")
        except Exception as e:
            self.log(f"检查或更新新版本失败：{e}", "ERROR")
            messagebox.showerror("错误", f"检查或更新新版本失败：{e}")

        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="你好，用户！——Python Minecraft Launcher", font=("宋体", 20))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 启动版本选择框架
        launch_frame = ttk.LabelFrame(main_frame, text="启动版本", padding="10")
        launch_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 启动版本选择
        ttk.Label(launch_frame, text="选择要启动的版本:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.launch_version_var = tk.StringVar()
        self.launch_version_combobox = ttk.Combobox(launch_frame, textvariable=self.launch_version_var, state="readonly", width=35)
        self.launch_version_combobox.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.version_settings_button = ttk.Button(launch_frame, text="设置", width=5, command=self.create_version_settings_widgets)
        self.version_settings_button.grid(row=1, column=1, padx=(5, 0), pady=(0, 10))
        
        
        
        # 登录选项框架
        login_frame = ttk.LabelFrame(main_frame, text="登录选项", padding="10")
        login_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.offline_frame = ttk.Frame(login_frame)
        self.offline_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0,10))
        
        # 登录方式选择
        ttk.Label(login_frame, text="登录方式:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.login_method_var = tk.StringVar(value="离线模式")
        self.login_method_combobox = ttk.Combobox(login_frame, textvariable=self.login_method_var, 
                                                  values=["离线模式", "LittleSkin"], state="readonly", width=35)
        self.login_method_combobox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.login_method_combobox.bind("<<ComboboxSelected>>", self.on_login_method_change)
        
        # 用户名输入
        ttk.Label(self.offline_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.offline_frame, textvariable=self.username_var, width=40)
        self.username_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # LittleSkin登录相关控件（默认隐藏）
        self.littleskin_frame = ttk.Frame(login_frame)
        self.littleskin_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.littleskin_frame.grid_remove()  # 默认隐藏
        
        ttk.Label(self.littleskin_frame, text="LittleSkin邮箱:").grid(row=0, column=0, sticky=tk.W, pady=(5, 5))
        self.littleskin_email_var = tk.StringVar()
        self.littleskin_email_entry = ttk.Entry(self.littleskin_frame, textvariable=self.littleskin_email_var, width=40)
        self.littleskin_email_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(self.littleskin_frame, text="LittleSkin密码:").grid(row=2, column=0, sticky=tk.W, pady=(5, 5))
        self.littleskin_password_var = tk.StringVar()
        self.littleskin_password_entry = ttk.Entry(self.littleskin_frame, textvariable=self.littleskin_password_var, 
                                                   show="*", width=40)
        self.littleskin_password_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 启动按钮
        self.launch_button = ttk.Button(main_frame, text="启动Minecraft", command=self.launch_minecraft)
        self.launch_button.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        launch_frame.columnconfigure(0, weight=1)
        login_frame.columnconfigure(1, weight=1)
        self.offline_frame.columnconfigure(0, weight=1)
        self.littleskin_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log(self, message, level):
        """在日志区域显示消息"""
        print(f"[{time.asctime()}] [root/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [root/{level}] {message}\n")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
    def on_login_method_change(self, event=None):
        """当登录方式改变时"""
        if self.login_method_var.get() == "LittleSkin":
            self.littleskin_frame.grid()
            # 如果之前保存过LittleSkin信息，则填充
            self.load_littleskin_credentials()
            self.offline_frame.grid_remove()
        else:
            self.littleskin_frame.grid_remove()
            self.offline_frame.grid()
            
    def load_littleskin_credentials(self):
        """从配置文件加载LittleSkin凭证"""
        try:
            settings_file = f"./pmcl_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    self.littleskin_email_var.set(settings.get("littleskin_email", ""))
        except Exception as e:
            self.log(f"加载LittleSkin凭证失败: {str(e)}", "ERROR")
            
    def save_littleskin_credentials(self):
        """保存LittleSkin凭证到配置文件"""
        try:
            settings_file = f"./pmcl_settings.json"
            # 先加载现有设置
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
            
            # 更新LittleSkin设置
            settings["littleskin_email"] = self.littleskin_email_var.get()
            
            # 保存设置
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            self.log(f"保存LittleSkin凭证失败: {str(e)}", "ERROR")
            
    def authenticate_with_littleskin(self, email, password):
        """使用LittleSkin进行认证"""
        try:
            self.log("正在连接到LittleSkin服务器...", "INFO")
            
            # LittleSkin Yggdrasil API端点
            auth_url = "https://littleskin.cn/api/yggdrasil/authserver/authenticate"
            
            # 构造认证请求数据
            client_token_str = uuid.uuid4().hex
            
            auth_data = {
                "agent": {
                    "name": "Minecraft",
                    "version": 1
                },
                "username": email,
                "password": password,
                "clientToken": client_token_str,
                "requestUser": True
            }
            
            # 将数据转换为JSON并编码
            data = json.dumps(auth_data).encode('utf-8')
            
            # 创建请求
            req = urllib.request.Request(
                auth_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'PMCL/1.1.1 (Python Minecraft Launcher)'
                }
            )
            
            # 发送请求并获取响应
            response = urllib.request.urlopen(req)
            response_data = json.loads(response.read().decode('utf-8'))
            
            # 检查是否有错误
            if "error" in response_data:
                error_message = response_data.get("errorMessage", "未知错误")
                self.log(f"LittleSkin认证失败: {error_message}", "ERROR")
                messagebox.showerror("认证失败", f"LittleSkin认证失败: {error_message}")
                return None
            
            # 提取认证信息
            access_token = response_data.get("accessToken", "")
            client_token = response_data.get("clientToken", "")
            
            # 获取可用的角色列表
            available_profiles = response_data.get("availableProfiles", [])
            
            # 如果有多个角色，让用户选择
            if len(available_profiles) > 1:
                selected_profile = self.select_littleskin_profile(available_profiles)
                if not selected_profile:
                    self.log("用户取消了角色选择", "INFO")
                    return None
            else:
                # 如果只有一个角色或没有角色，使用默认选择
                selected_profile = response_data.get("selectedProfile", {})
                if not selected_profile and available_profiles:
                    selected_profile = available_profiles[0]
            
            # 获取用户信息
            username = selected_profile.get("name", email.split("@")[0])
            user_uuid = selected_profile.get("id", "")
            
            self.log(f"LittleSkin认证成功: {username}", "INFO")
            
            return {
                "username": username,
                "uuid": user_uuid,
                "access_token": access_token,
                "client_token": client_token
            }
            
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.log(f"LittleSkin认证HTTP错误: 用户名或密码错误", "WARN")
                messagebox.showwarning("警告", f"LittleSkin认证失败: 用户名或密码错误")
            else:
                self.log(f"LittleSkin认证HTTP错误: {e.code} - {e.reason}", "ERROR")
                messagebox.showerror("认证失败", f"LittleSkin认证失败: HTTP {e.code} - {e.reason}")
            return None
        except Exception as e:
            self.log(f"LittleSkin认证失败: {str(e)}", "ERROR")
            messagebox.showerror("认证失败", f"LittleSkin认证失败: {str(e)}")
            return None
        
    def select_littleskin_profile(self, profiles):
        """选择LittleSkin角色"""

        if not profiles:
            return None
        
        # 创建选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择角色")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        dialog.geometry(f"500x300+{(dialog.winfo_screenwidth() // 2) - (500 // 2)}+{(dialog.winfo_screenheight() // 2) - (300 // 2)}")
        
        # 标签
        tk.Label(dialog, text="请选择一个角色:").pack(pady=10)
        
        # 列表框
        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
        for profile in profiles:
            listbox.insert(tk.END, profile.get("name", "未知角色"))
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 选择的值
        selected_profile = [None]
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                selected_profile[0] = profiles[index]
                dialog.destroy()
        
        def on_cancel():
            selected_profile[0] = None
            dialog.destroy()
        
        # 按钮
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="确定", command=on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # 等待对话框关闭
        dialog.wait_window()
        
        return selected_profile[0]
        
    def browse_java_path(self):
        """浏览Java路径"""
        java_path = filedialog.askopenfilename(
            title="选择Java可执行文件",
            filetypes=[("Java Executable", ("java.exe", "javaw.exe")), ("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if java_path:
            self.java_path_var.set(java_path)
            self.java_path = java_path
            
    def browse_skin_path(self):
        """浏览皮肤路径"""
        skin_path = filedialog.askopenfilename(
            title="选择皮肤文件",
            filetypes=[("Skin Files", "*.png"), ("All Files", "*.*")]
        )
        if skin_path:
            self.skin_path_var.set(skin_path)
            self.skin_path = skin_path
            
    def load_installed_versions(self):
        """加载已安装的版本列表"""
        try:
            # 获取已安装的版本
            if os.path.exists(f"{self.minecraft_directory}/versions"):
                self.installed_versions = os.listdir(f"{self.minecraft_directory}/versions")
                # 更新启动版本下拉列表
                self.launch_version_combobox['values'] = self.installed_versions
                
                # 设置默认选中版本
                if self.installed_versions:
                    self.launch_version_var.set(self.installed_versions[0])
        except Exception as e:
            self.log(f"加载已安装版本列表失败: {str(e)}", "ERROR")

    def create_version_settings_widgets(self):
        """创建版本设置窗口的界面"""
        version = self.launch_version_var.get()
        if not version:
            messagebox.showwarning("警告", "请先选择一个版本")
            return
            
        self.version_settings_window = tk.Toplevel(self.root)
        self.version_settings_window.title(f"{version} 设置")
        self.version_settings_window.geometry(f"300x400+{int((self.root.winfo_screenwidth()-300)/2)}+{int((self.root.winfo_screenheight()-400)/2)}")
        
        self.version_settings_window.grab_set()
        self.version_settings_window.resizable(False, False)
        
        vmain_frame = ttk.Frame(self.version_settings_window, padding="10")
        vmain_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(vmain_frame, text=f"{version} 设置", font=("微软雅黑", 18))
        title_label.pack(pady=(0, 10))
        
        # 按钮框架
        button_frame = ttk.Frame(vmain_frame)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 跳转到版本文件夹按钮
        version_folder_button = ttk.Button(button_frame, text="打开版本文件夹", command=lambda: self.open_folder(f"{self.minecraft_directory}/versions/{version}"))
        version_folder_button.pack(fill=tk.X, pady=5)
        
        # 跳转到存档文件夹按钮
        saves_folder_button = ttk.Button(button_frame, text="打开存档文件夹", command=lambda: self.open_folder(f"{self.isolation_dir}/saves"))
        saves_folder_button.pack(fill=tk.X, pady=5)

        # 跳转到资源包文件夹按钮
        resourcepack_folder_button = ttk.Button(button_frame, text="打开资源包文件夹", command=lambda: self.open_folder(f"{self.isolation_dir}/resourcepacks"))
        resourcepack_folder_button.pack(fill=tk.X, pady=5)

        # 跳转到模组文件夹按钮
        mods_folder_button = ttk.Button(button_frame, text="打开模组文件夹", command=lambda: self.open_folder(f"{self.isolation_dir}/mods"))
        mods_folder_button.pack(fill=tk.X, pady=5)

        # 跳转到光影文件夹按钮
        shaderpack_folder_button = ttk.Button(button_frame, text="打开光影包文件夹", command=lambda: self.open_folder(f"{self.isolation_dir}/shaderpacks"))
        shaderpack_folder_button.pack(fill=tk.X, pady=5)

        # 模组管理按钮
        mod_manager_button = ttk.Button(button_frame, text="模组管理", command=lambda: self.open_mod_manager(version))
        mod_manager_button.pack(fill=tk.X, pady=5)
        
        # 版本隔离选项
        isolation_checkbox = ttk.Checkbutton(button_frame, text="启用版本隔离", variable=self.isolation_var, 
                                           command=lambda: self.toggle_version_isolation(version))
        isolation_checkbox.pack(fill=tk.X, pady=5)
        
        # 重命名版本按钮
        rename_version_button = ttk.Button(button_frame, text="重命名版本", command=lambda: self.rename_version(version, None))
        rename_version_button.pack(fill=tk.X, pady=5)
        
        # 删除版本按钮
        delete_version_button = ttk.Button(button_frame, text="删除此版本", command=lambda: self.delete_version(version))
        delete_version_button.pack(fill=tk.X, pady=5)
        
        # 初始化版本隔离复选框状态
        self.init_isolation_state(version)
        
    def open_folder(self, folder_path):
        """打开指定文件夹"""
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            # 如果文件夹不存在，创建它
            try:
                os.makedirs(folder_path)
                os.startfile(folder_path)
            except Exception as e:
                self.log(f"无法打开或创建文件夹: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"无法打开或创建文件夹: {str(e)}")
                
    def open_mod_manager(self, version):
        """打开模组管理窗口"""
        self.init_isolation_state(version)
        mods_dir = f"{self.isolation_dir}/mods"
        
        # 如果模组文件夹不存在，创建它
        if not os.path.exists(mods_dir):
            os.makedirs(mods_dir)
        
        # 创建模组管理窗口
        self.mod_manager_window = tk.Toplevel(self.root)
        self.mod_manager_window.title(f"{version} 模组管理")
        self.mod_manager_window.geometry(f"800x550+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-550)/2)}")
        
        self.mod_manager_window.grab_set()
        self.mod_manager_window.resizable(False, False)

        # 绑定关闭事件
        def on_exit():
            self.version_settings_window.destroy()
            self.mod_manager_window.destroy()
        self.mod_manager_window.protocol("WM_DELETE_WINDOW", on_exit)
        
        # 模组管理窗口主框架
        mod_manager_main_frame = ttk.Frame(self.mod_manager_window, padding="10")
        mod_manager_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(mod_manager_main_frame, text=f"{version} 模组管理", font=("微软雅黑", 18))
        title_label.pack(pady=(0, 10))
        
        # 搜索框架
        search_frame = ttk.Frame(mod_manager_main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索模组:").pack(side=tk.LEFT)
        self.mod_search_var = tk.StringVar()
        self.mod_search_entry = ttk.Entry(search_frame, textvariable=self.mod_search_var, width=30)
        self.mod_search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_mods_in_manager)
        search_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 清除按钮
        clear_button = ttk.Button(search_frame, text="清除", command=self.clear_mod_search)
        clear_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 模组列表框架
        mod_list_frame = ttk.LabelFrame(mod_manager_main_frame, text="模组列表", padding="10")
        mod_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示模组列表
        columns = ('name', 'status', 'size')
        self.mods_tree = ttk.Treeview(mod_list_frame, columns=columns, show='headings', height=15, selectmode='extended')
        
        # 定义列标题
        self.mods_tree.heading('name', text='模组名称')
        self.mods_tree.heading('status', text='状态')
        self.mods_tree.heading('size', text='大小')
        
        # 设置列宽
        self.mods_tree.column('name', width=400)
        self.mods_tree.column('status', width=100)
        self.mods_tree.column('size', width=100)
        
        # 添加滚动条
        mods_scrollbar_y = ttk.Scrollbar(mod_list_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        mods_scrollbar_x = ttk.Scrollbar(mod_list_frame, orient=tk.HORIZONTAL, command=self.mods_tree.xview)
        self.mods_tree.configure(yscrollcommand=mods_scrollbar_y.set, xscrollcommand=mods_scrollbar_x.set)
        
        # 布局
        self.mods_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        mods_scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        mods_scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 按钮框架
        button_frame = ttk.Frame(mod_manager_main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 全选/取消全选按钮
        self.select_all_button = ttk.Button(button_frame, text="全选", command=self.toggle_select_all)
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 删除模组按钮
        delete_mod_button = ttk.Button(button_frame, text="删除模组", command=self.delete_selected_mod, state=tk.DISABLED)
        delete_mod_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 禁用/启用模组按钮
        self.toggle_mod_button = ttk.Button(button_frame, text="禁用模组", command=self.toggle_selected_mod, state=tk.DISABLED)
        self.toggle_mod_button.pack(side=tk.LEFT, padx=(0, 5))

        # 提示
        tips = tk.Label(button_frame, text="提示：按住Ctrl或Shift可多选模组！")
        tips.pack(side=tk.LEFT, padx=(0, 5))
        
        # 刷新按钮
        refresh_button = ttk.Button(button_frame, text="刷新", command=lambda: self.load_mods_list(mods_dir))
        refresh_button.pack(side=tk.RIGHT)
        
        # 配置网格权重
        mod_manager_main_frame.columnconfigure(0, weight=1)
        mod_manager_main_frame.rowconfigure(1, weight=1)
        mod_list_frame.columnconfigure(0, weight=1)
        mod_list_frame.rowconfigure(0, weight=1)
        
        # 绑定Treeview选择事件
        self.mods_tree.bind('<<TreeviewSelect>>', self.on_mod_in_manager_select)
        
        # 绑定搜索框回车事件
        self.mod_search_entry.bind('<Return>', lambda event: self.search_mods_in_manager())
        
        # 加载模组列表
        self.load_mods_list(mods_dir)
        
    def load_mods_list(self, mods_dir):
        """加载模组列表"""
        # 清空现有数据
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
            
        # 获取模组文件
        if os.path.exists(mods_dir):
            for file in os.listdir(mods_dir):
                file_path = os.path.join(mods_dir, file)
                if os.path.isfile(file_path) and (file.endswith('.jar') or file.endswith('.disabled')):
                    # 获取文件大小
                    size = os.path.getsize(file_path)
                    size_str = self.format_file_size(size)
                    
                    # 获取模组状态
                    status = "已禁用" if file.endswith('.disabled') else "已启用"
                    
                    # 添加到Treeview
                    self.mods_tree.insert('', tk.END, values=(file, status, size_str), tags=(file_path,))
                    
    def search_mods_in_manager(self):
        """在模组管理器中搜索模组"""
        search_term = self.mod_search_var.get().lower()
        if not search_term:
            return
            
        # 获取当前版本的模组目录
        version = self.launch_version_var.get()
        self.init_isolation_state(version)
        mods_dir = f"{self.isolation_dir}/mods"
        
        # 清空现有数据
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
            
        # 获取模组文件并过滤
        if os.path.exists(mods_dir):
            for file in os.listdir(mods_dir):
                file_path = os.path.join(mods_dir, file)
                if os.path.isfile(file_path) and (file.endswith('.jar') or file.endswith('.disabled')):
                    # 检查是否匹配搜索词
                    if search_term in file.lower():
                        # 获取文件大小
                        size = os.path.getsize(file_path)
                        size_str = self.format_file_size(size)
                        
                        # 获取模组状态
                        status = "已禁用" if file.endswith('.disabled') else "已启用"
                        
                        # 添加到Treeview
                        self.mods_tree.insert('', tk.END, values=(file, status, size_str), tags=(file_path,))
                        
    def toggle_select_all(self):
        """全选/取消全选模组"""
        current_text = self.select_all_button.cget('text')
        
        if current_text == "全选":
            # 选择所有项
            children = self.mods_tree.get_children()
            self.mods_tree.selection_set(children)
            self.select_all_button.config(text="取消全选")
            
            # 启用批量操作按钮
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button) and button.cget('text') in ['批量删除', '批量禁用']:
                                    button.config(state=tk.NORMAL)
        else:
            # 取消选择所有项
            self.mods_tree.selection_remove(self.mods_tree.selection())
            self.select_all_button.config(text="全选")
            
            # 禁用批量操作按钮
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button) and button.cget('text') in ['批量删除', '批量禁用', '批量启用']:
                                    button.config(state=tk.DISABLED)
            
            # 禁用单个操作按钮
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button) and button.cget('text') in ['删除模组', '禁用模组', '启用模组']:
                                    button.config(state=tk.DISABLED)
                    
    def batch_delete_mods(self):
        """批量删除模组"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的模组")
            return
            
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selection)} 个模组吗？此操作不可撤销。"):
            deleted_count = 0
            error_count = 0
            
            # 删除每个选中的模组
            for item_id in selection:
                item = self.mods_tree.item(item_id)
                values = item['values']
                mod_name = values[0] if len(values) > 0 else '未知模组'
                
                # 获取文件路径
                tags = item['tags']
                file_path = tags[0] if len(tags) > 0 else None
                
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        error_count += 1
                        self.mod_manager_window.after(0, lambda: messagebox.showerror("错误", f"删除模组 {mod_name} 失败: {str(e)}"))
                else:
                    error_count += 1
                    self.mod_manager_window.after(0, lambda: messagebox.showerror("错误", f"无法找到模组文件: {mod_name}"))
            
            # 显示结果
            if error_count == 0:
                self.log(f"成功删除 {deleted_count} 个模组", "INFO")
                messagebox.showinfo("成功", f"成功删除 {deleted_count} 个模组")
            else:
                self.log(f"删除完成: {deleted_count} 个成功, {error_count} 个失败", "WARN")
                messagebox.showinfo("完成", f"删除完成: {deleted_count} 个成功, {error_count} 个失败")
                
            # 重新加载模组列表
            version = self.launch_version_var.get()
            self.init_isolation_state(version)
            mods_dir = f"{self.isolation_dir}/mods"
            self.load_mods_list(mods_dir)
            
            # 重置全选按钮
            self.select_all_button.config(text="全选")
            
    def batch_toggle_mods(self):
        """批量启用/禁用模组"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要操作的模组")
            return
            
        # 检查选中的模组状态，确定是启用还是禁用
        enable_count = 0
        disable_count = 0
        
        for item_id in selection:
            item = self.mods_tree.item(item_id)
            values = item['values']
            status = values[1] if len(values) > 1 else '未知状态'
            
            if status == "已启用":
                disable_count += 1
            else:
                enable_count += 1
                
        # 确定操作类型（以多数为准）
        operation = "禁用" if disable_count >= enable_count else "启用"
        
        # 确认操作
        if messagebox.askyesno("确认操作", f"确定要{operation}选中的 {len(selection)} 个模组吗？"):
            success_count = 0
            error_count = 0
            
            # 执行操作
            for item_id in selection:
                item = self.mods_tree.item(item_id)
                values = item['values']
                mod_name = values[0] if len(values) > 0 else '未知模组'
                status = values[1] if len(values) > 1 else '未知状态'
                
                # 获取文件路径
                tags = item['tags']
                file_path = tags[0] if len(tags) > 0 else None
                
                if file_path and os.path.exists(file_path):
                    try:
                        # 获取文件目录和文件名
                        dir_name = os.path.dirname(file_path)
                        file_name = os.path.basename(file_path)
                        
                        if operation == "禁用" and status == "已启用":
                            # 禁用模组（添加.disabled后缀）
                            new_file_path = file_path + ".disabled"
                            os.rename(file_path, new_file_path)
                            success_count += 1
                        elif operation == "启用" and status == "已禁用":
                            # 启用模组（移除.disabled后缀）
                            if file_name.endswith('.disabled'):
                                new_file_path = os.path.join(dir_name, file_name[:-9])  # 移除.disabled后缀
                                os.rename(file_path, new_file_path)
                                success_count += 1
                        else:
                            # 状态已经正确，不需要操作
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        self.mod_manager_window.after(0, lambda: messagebox.showerror("错误", f"{operation}模组 {mod_name} 失败: {str(e)}"))
                else:
                    error_count += 1
                    self.mod_manager_window.after(0, lambda: messagebox.showerror("错误", f"无法找到模组文件: {mod_name}"))
            
            # 显示结果
            if error_count == 0:
                self.log(f"成功: {operation} {success_count} 个模组", "INFO")
                messagebox.showinfo("成功", f"成功{operation} {success_count} 个模组")
            else:
                self.log(f"{operation} 完成: {success_count} 个成功, {error_count} 个失败", "WARN")
                messagebox.showinfo("完成", f"{operation}完成: {success_count} 个成功, {error_count} 个失败")
                
            # 重新加载模组列表
            version = self.launch_version_var.get()
            self.init_isolation_state(version)
            mods_dir = f"{self.isolation_dir}/mods"
            self.load_mods_list(mods_dir)
            
            # 重置全选按钮
            self.select_all_button.config(text="全选")
                        
    def clear_mod_search(self):
        """清除模组搜索"""
        self.mod_search_var.set("")
        
        # 重新加载所有模组
        version = self.launch_version_var.get()
        self.init_isolation_state(version)
        mods_dir = f"{self.isolation_dir}/mods"
        self.load_mods_list(mods_dir)
        
    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def on_mod_in_manager_select(self, event):
        """当选择模组时"""
        selection = self.mods_tree.selection()
        if selection:
            # 启用单个操作按钮
            delete_button = None
            toggle_button = None
            
            # 查找按钮并启用它们
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button):
                                    if button.cget('text') == '删除模组':
                                        delete_button = button
                                    elif button.cget('text') == '禁用模组' or button.cget('text') == '启用模组':
                                        toggle_button = button
            
            if delete_button:
                delete_button.config(state=tk.NORMAL)
            if toggle_button:
                toggle_button.config(state=tk.NORMAL)
                
                # 更新按钮文本
                item = self.mods_tree.item(selection[0])
                values = item['values']
                if len(values) > 1:
                    status = values[1]
                    if status == "已启用":
                        toggle_button.config(text="禁用模组")
                    else:
                        toggle_button.config(text="启用模组")
            
            # 启用批量操作按钮
            batch_delete_button = None
            batch_toggle_button = None
            
            # 查找批量操作按钮
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button):
                                    if button.cget('text') == '批量删除':
                                        batch_delete_button = button
                                    elif button.cget('text') == '批量禁用' or button.cget('text') == '批量启用':
                                        batch_toggle_button = button
            
            if batch_delete_button:
                batch_delete_button.config(state=tk.NORMAL)
            if batch_toggle_button:
                batch_toggle_button.config(state=tk.NORMAL)
        else:
            # 禁用所有操作按钮
            for child in self.mod_manager_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for button in subchild.winfo_children():
                                if isinstance(button, ttk.Button):
                                    if button.cget('text') in ['删除模组', '禁用模组', '启用模组', '批量删除', '批量禁用', '批量启用']:
                                        button.config(state=tk.DISABLED)
        
    def delete_selected_mod(self):
        """删除选中的模组"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模组")
            return
            
        # 如果只选择了一个模组，使用原来的逻辑
        if len(selection) == 1:
            # 获取选中的模组信息
            item = self.mods_tree.item(selection[0])
            values = item['values']
            mod_name = values[0] if len(values) > 0 else '未知模组'
            
            # 确认删除
            if messagebox.askyesno("确认删除", f"确定要删除模组 {mod_name} 吗？此操作不可撤销。"):
                # 获取文件路径
                tags = item['tags']
                file_path = tags[0] if len(tags) > 0 else None
                
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.log(f"模组 {mod_name} 已删除", "INFO")
                        messagebox.showinfo("成功", f"模组 {mod_name} 已删除")
                        
                        # 重新加载模组列表
                        version = self.launch_version_var.get()
                        self.init_isolation_state(version)
                        mods_dir = f"{self.isolation_dir}/mods"
                        self.load_mods_list(mods_dir)
                    except Exception as e:
                        self.log(f"删除模组失败: {str(e)}", "ERROR")
                        messagebox.showerror("错误", f"删除模组失败: {str(e)}")
                else:
                    self.log(f"无法找到模组文件", "ERROR")
                    messagebox.showerror("错误", "无法找到模组文件")
        else:
            # 如果选择了多个模组，使用批量删除
            self.batch_delete_mods()
                
    def toggle_selected_mod(self):
        """禁用/启用选中的模组"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个模组")
            return
            
        # 如果只选择了一个模组，使用原来的逻辑
        if len(selection) == 1:
            # 获取选中的模组信息
            item = self.mods_tree.item(selection[0])
            values = item['values']
            mod_name = values[0] if len(values) > 0 else '未知模组'
            status = values[1] if len(values) > 1 else '未知状态'
            
            # 获取文件路径
            tags = item['tags']
            file_path = tags[0] if len(tags) > 0 else None
            
            if file_path and os.path.exists(file_path):
                try:
                    # 获取文件目录和文件名
                    dir_name = os.path.dirname(file_path)
                    file_name = os.path.basename(file_path)
                    
                    if status == "已启用":
                        # 禁用模组（添加.disabled后缀）
                        new_file_path = file_path + ".disabled"
                        os.rename(file_path, new_file_path)
                        self.log(f"模组 {mod_name} 已禁用", "INFO")
                        messagebox.showinfo("成功", f"模组 {mod_name} 已禁用")
                    else:
                        # 启用模组（移除.disabled后缀）
                        if file_name.endswith('.disabled'):
                            new_file_path = os.path.join(dir_name, file_name[:-9])  # 移除.disabled后缀
                            os.rename(file_path, new_file_path)
                            self.log(f"模组 {mod_name} 已启用", "INFO")
                            messagebox.showinfo("成功", f"模组 {mod_name} 已启用")
                        else:
                            messagebox.showwarning("警告", "模组已经是启用状态")
                            return
                    
                    # 重新加载模组列表
                    version = self.launch_version_var.get()
                    self.init_isolation_state(version)
                    mods_dir = f"{self.isolation_dir}/mods"
                    self.load_mods_list(mods_dir)
                except Exception as e:
                    self.log(f"切换模组状态失败: {str(e)}", "ERROR")
                    messagebox.showerror("错误", f"切换模组状态失败: {str(e)}")
            else:
                self.log("无法找到模组文件", "ERROR")
                messagebox.showerror("错误", "无法找到模组文件")
        else:
            # 如果选择了多个模组，使用批量操作
            self.batch_toggle_mods()
                
    def rename_version(self, version, specify_name):
        """重命名指定版本"""
        # 弹出输入框获取新版本名
        if not specify_name:
            new_name = tk.simpledialog.askstring("重命名版本", "请输入新的版本名称:", initialvalue=version)
        else:
            new_name = ''.join(specify_name)

        # 检查用户是否取消或输入空值
        if not new_name or new_name == version:
            return

        # 检查新名称是否合法
        import re
        if re.search(r'[//:*?"<>|]', new_name):
            messagebox.showwarning("警告", "重命名版本失败: 名称包含非法字符")
            return
            
        # 检查新名称是否已存在
        new_path = f"{self.minecraft_directory}/versions/{new_name}"
        if os.path.exists(new_path):
            messagebox.showwarning("警告", f"版本 {new_name} 已存在，请选择其他名称。")
            return
            
        try:
            # 重命名版本文件夹
            old_path = f"{self.minecraft_directory}/versions/{version}"
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                
                # 重命名版本文件夹内的.jar和.json文件
                old_jar = f'{new_path}/{version}.jar'
                new_jar = f'{new_path}/{new_name}.jar'
                old_json = f'{new_path}/{version}.json'
                new_json = f'{new_path}/{new_name}.json'
                
                if os.path.exists(old_jar):
                    os.rename(old_jar, new_jar)
                if os.path.exists(old_json):
                    os.rename(old_json, new_json)
                    
                # 更新.json文件中的版本ID
                try:
                    with open(new_json, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        
                    # 更新版本ID
                    if 'id' in json_data and json_data['id'] == version:
                        json_data['id'] = new_name
                            
                    # 更新继承自的版本ID（如果有）
                    if 'inheritsFrom' in json_data and json_data['inheritsFrom'] == version:
                        json_data['inheritsFrom'] = new_name
                        
                    # 保存更新后的.json文件
                    with open(new_json, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    # 如果更新.json文件失败，仅记录日志但不中断重命名过程
                    self.log(f"警告: 更新版本配置文件失败: {str(e)}", "ERROR")

                # 重新加载版本列表
                self.load_installed_versions()
                
                # 更新启动版本选择
                current_values = list(self.launch_version_combobox['values'])
                if version in current_values:
                    idx = current_values.index(version)
                    current_values[idx] = new_name
                    self.launch_version_combobox['values'] = current_values
                    
                    # 如果当前选中的是被重命名的版本，则更新选中值
                    if self.launch_version_var.get() == version:
                        self.launch_version_var.set(new_name)
                
                # 如果是从版本设置窗口重命名，关闭窗口
                if hasattr(self, "version_settings_window"):
                    self.version_settings_window.destroy()
                
                # 当安装整合包时不显示弹窗和日志
                if specify_name:
                    return
                self.log(f"版本 {version} 已重命名为 {new_name}", "INFO")
                messagebox.showinfo("成功", f"版本 {version} 已重命名为 {new_name}")
            else:
                messagebox.showwarning("警告", f"版本 {version} 不存在")
        except Exception as e:
            self.log(f"重命名版本失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"重命名版本失败: {str(e)}")
    
    def delete_version(self, version):
        """删除指定版本"""
        if messagebox.askyesno("确认删除", f"确定要删除版本 {version} 吗？此操作不可撤销。"):
            try:
                version_path = f"{self.minecraft_directory}/versions/{version}"
                if os.path.exists(version_path):
                    import shutil
                    shutil.rmtree(version_path)
                    self.log(f"版本 {version} 已删除", "INFO")
                    messagebox.showinfo("成功", f"版本 {version} 已删除")
                    # 重新加载版本列表
                    self.load_installed_versions()
                else:
                    messagebox.showwarning("警告", f"版本 {version} 不存在")
                self.version_settings_window.destroy()
            except Exception as e:
                self.log(f"删除版本失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"删除版本失败: {str(e)}")
                
    def init_isolation_state(self, version):
        """初始化版本隔离状态"""
        if os.path.exists(f'{self.minecraft_directory}/versions/{version}/config'):
            if hasattr(self, "isolation_var"):
                self.isolation_var.set(True)
            self.isolation_dir = f'{self.minecraft_directory}/versions/{version}'
        else:
            if hasattr(self, "isolation_var"):
                self.isolation_var.set(False)
            self.isolation_dir = ''.join(self.minecraft_directory)
        
    def toggle_version_isolation(self, version):
        """切换版本隔离状态"""
        
        if self.isolation_var.get():
            # 启用版本隔离
            try:
                self.isolation_dir = f'{self.minecraft_directory}/versions/{version}'
                
                # 创建基本的目录结构
                directories = ['saves', 'mods', 'config', 'screenshots', 'resourcepacks', 'shaderpacks']
                if messagebox.askyesno("提示", "是否复制版本的数据？"):
                    import shutil
                    for directory in directories:
                        if os.path.exists(f'{self.minecraft_directory}/{directory}'):
                            shutil.copytree(f'{self.minecraft_directory}/{directory}', f'{self.isolation_dir}/{directory}', dirs_exist_ok=True)

                for directory in directories:
                    os.makedirs(f"{self.isolation_dir}/{directory}", exist_ok=True)
                
                messagebox.showinfo("成功", f"版本 {version} 的隔离环境已创建")
                self.log(f"版本 {version} 的隔离环境已创建", "INFO")
            except Exception as e:
                self.log(f"创建隔离环境失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"创建隔离环境失败: {str(e)}")
                self.isolation_var.set(False)
        else:
            # 禁用版本隔离
            if os.path.exists(self.isolation_dir):
                if messagebox.askyesno("确认", f"确定要移除版本 {version} 的隔离环境吗？"):
                    try:
                        directories = ['saves', 'mods', 'config', 'screenshots', 'resourcepacks']
                        
                        import shutil
                        if messagebox.askyesno("提示", "是否复制版本的数据？"):
                            for directory in directories:
                                if os.path.exists(f'{self.isolation_dir}/{directory}'):
                                    shutil.copytree(f'{self.isolation_dir}/{directory}', f'{self.minecraft_directory}/{directory}', dirs_exist_ok=True)
                        
                        for directory in directories:
                            for directory in directories:
                                if os.path.exists(f'{self.isolation_dir}/{directory}'):
                                    shutil.rmtree(f'{self.isolation_dir}/{directory}')
                        
                        self.isolation_dir = ''.join(self.minecraft_directory)
                        messagebox.showinfo("成功", f"版本 {version} 的隔离环境已移除")
                        self.log(f"版本 {version} 的隔离环境已移除", "INFO")
                    except Exception as e:
                        self.log(f"移除隔离环境失败: {str(e)}", "ERROR")
                        messagebox.showerror("错误", f"移除隔离环境失败: {str(e)}")
                        self.isolation_var.set(True)
                else:
                    # 用户取消操作，恢复复选框状态
                    self.isolation_var.set(True)
                    return
        
    def launch_minecraft(self):
        """启动Minecraft"""
        version = self.launch_version_var.get()
        if not version:
            messagebox.showwarning("警告", "请先选择一个版本")
            return
            
        # 检查登录方式
        login_method = self.login_method_var.get()
        
        # 如果是LittleSkin登录，验证邮箱和密码
        if login_method == "LittleSkin":
            username = ""
            email = self.littleskin_email_var.get()
            password = self.littleskin_password_var.get()
            if not email or not password:
                messagebox.showwarning("警告", "请输入LittleSkin邮箱和密码")
                return
        else:
            # 获取用户名
            username = self.username_var.get()
            if not username:
                messagebox.showwarning("警告", "请输入用户名")
                return
        options = {
            "username": username,
            "uuid": "",
            "token": ""
        }
        
        # 如果设置了Java路径，则添加到选项中
        if not self.use_custom_java:
            if self.java_path:
                options["executablePath"] = self.java_path
            else:
                messagebox.showwarning("警告", "请输入Java路径！")
                return
        
        # 添加内存设置
        if hasattr(self, 'memory_var'):
            memory = self.memory_var.get()
            if memory and memory.isdigit():
                options["jvmArguments"] = [f"-Xmx{memory}m"]
        
        options["customResolution"] = True
        options["resolutionWidth"] = "854"
        options["resolutionHeight"] = "480"
            
        # 初始化版本隔离状态
        self.init_isolation_state(version)
        
        options["gameDirectory"] = self.isolation_dir
        
        self.log(f"登录方式: {login_method}", "INFO")
        self.log(f"用户名: {username}", "INFO")
            
        # 禁用启动按钮防止重复点击
        self.launch_button.config(state=tk.DISABLED)
        
        # 在新线程中启动Minecraft
        if login_method == "LittleSkin":
            launch_thread = threading.Thread(target=self._launch_minecraft_with_littleskin, args=(version, options))
        else:
            launch_thread = threading.Thread(target=self._launch_minecraft_thread, args=(version, options))
        launch_thread.daemon = True
        launch_thread.start()
        
    def _launch_minecraft_thread(self, version, options):
        """在后台线程中启动Minecraft（离线模式）"""
        try:
            self.log("正在启动Minecraft...", "INFO")
            version = self.launch_version_var.get()

            # 保存用户名
            self.save_settings()
            
            # 应用内存设置
            if hasattr(self, 'memory_var'):
                memory = self.memory_var.get()
                if memory and memory.isdigit():
                    options["jvmArguments"] = [f"-Xmx{memory}m"]
            
            # 设置中文
            if not os.path.exists(f'{self.isolation_dir}/options.txt'):
                with open(f'{self.isolation_dir}/options.txt', 'w') as options_file:
                    options_file.write('lang:zh_CN')
            
            # 如果设置了皮肤路径，则复制皮肤文件
            username = self.username_var.get()
            if self.skin_path and os.path.exists(self.skin_path):
                try:
                    import shutil
                    skins_dir = f'{self.isolation_dir}/CustomSkinLoader'
                    if os.path.exists(skins_dir):
                        if os.path.exists(f'{skins_dir}/LocalSkin/skins/{username}.png'):
                            os.remove(f'{skins_dir}/LocalSkin/skins/{username}.png')
                        shutil.copy2(self.skin_path, f'{skins_dir}/LocalSkin/skins/{username}.png')
                        self.log(f"皮肤已应用: {self.skin_path}", "INFO")
                    else:
                        self.log("应用皮肤失败: 未找到CustomSkinLoader", "WARN")
                except Exception as e:
                    self.log(f"应用皮肤失败: {str(e)}", "ERROR")
            
            # 获取启动命令
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version, 
                self.minecraft_directory, 
                options
            )
            for i, arg in enumerate(minecraft_command):
                if arg == "--versionType":
                    minecraft_command[i + 1] = "PMCL"
                    break
            
            if not self.use_java:
                minecraft_command[0] = 'javaw'.join(minecraft_command[0].rsplit('java', 1))
                
            self.log(str(minecraft_command), "INFO")
            self.log("Minecraft已启动", "INFO")

            # 重新启用启动按钮
            self.launch_button.config(state=tk.NORMAL)
            
            # 启动Minecraft
            result = subprocess.run(minecraft_command, cwd=self.minecraft_directory)
            if result.returncode:
                self.log(f"游戏以错误代码{result.returncode}退出", "WARN")
                messagebox.showerror("错误", f"游戏以错误代码{result.returncode}退出")
            else:
                self.log("游戏正常退出", "INFO")
        except Exception as e:
            self.log(f"启动失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动失败: {str(e)}")
        finally:
            # 重新启用启动按钮
            self.launch_button.config(state=tk.NORMAL)
            
    def _launch_minecraft_with_littleskin(self, version, options):
        """在后台线程中启动Minecraft（LittleSkin模式）"""
        try:
            self.log("正在通过LittleSkin启动Minecraft...", "INFO")
            
            # 保存LittleSkin邮箱（不保存密码）
            self.save_littleskin_credentials()
            
            # 获取LittleSkin凭证
            email = self.littleskin_email_var.get()
            password = self.littleskin_password_var.get()
            
            # 使用LittleSkin进行认证
            auth_data = self.authenticate_with_littleskin(email, password)
            if not auth_data:
                return
                
            # 更新启动选项
            options["username"] = auth_data["username"]
            options["uuid"] = auth_data["uuid"]
            options["token"] = auth_data["access_token"]
            
            # 添加内存设置
            if hasattr(self, 'memory_var'):
                memory = self.memory_var.get()
                if memory and memory.isdigit():
                    options["jvmArguments"] = [f"-Xmx{memory}m"]
            
            # 添加Yggdrasil服务器参数
            options["customResolution"] = True
            options["resolutionWidth"] = "854"
            options["resolutionHeight"] = "480"
            
            # 设置中文
            if not os.path.exists(f'{self.isolation_dir}/options.txt'):
                with open(f'{self.isolation_dir}/options.txt', 'w') as options_file:
                    options_file.write('lang:zh_CN')
            
            username = auth_data["username"]
            self.log("正在使用littleskin启动，不使用本地皮肤", "INFO")
            
            # 获取启动命令（添加Yggdrasil参数）
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version, 
                self.minecraft_directory, 
                options
            )
            
            # 添加authlib-injector参数以使用LittleSkin
            authlib_injector_path = f"{self.minecraft_directory}/authlib-injector.jar"
            if not os.path.exists(authlib_injector_path):
                self.log("正在下载authlib-injector.jar...", "INFO")
                # 下载authlib-injector.jar
                with open(authlib_injector_path, 'wb') as f:
                    f.write(self.get_from_server('https://pmcldownloadserver.dpdns.org/authlib-injector.jar'))
            if os.path.exists(authlib_injector_path):
                # 在命令中添加-javaagent参数
                java_agent_index = -1
                for i, arg in enumerate(minecraft_command):
                    if arg == "-cp" or arg == "-classpath":
                        java_agent_index = i
                    if arg == "--versionType":
                        minecraft_command[i + 1] = "PMCL"
                
                if java_agent_index != -1:
                    minecraft_command.insert(java_agent_index, f"-javaagent:{authlib_injector_path}=https://littleskin.cn/api/yggdrasil")
                    minecraft_command.insert(java_agent_index, "-Dauthlibinjector.side=client")
                else:
                    # 如果没有找到-cp参数，则在java命令后直接添加
                    if "java" in minecraft_command[0].lower():
                        minecraft_command.insert(1, f"-javaagent:{authlib_injector_path}=https://littleskin.cn/api/yggdrasil")
                        minecraft_command.insert(1, "-Dauthlibinjector.side=client")
            else:
                self.log("警告: 未找到authlib-injector.jar，将使用默认认证", "WARN")

            if not self.use_java:
                minecraft_command[0] = 'javaw'.join(minecraft_command[0].rsplit('java', 1))
                
            self.log(str(minecraft_command), "INFO")
            self.log("Minecraft已启动", "INFO")

            # 重新启用启动按钮
            self.launch_button.config(state=tk.NORMAL)

            # 启动Minecraft
            result = subprocess.run(minecraft_command, cwd=self.minecraft_directory)
            if result.returncode:
                self.log(f"游戏以错误代码{result.returncode}退出", "WARN")
                messagebox.showerror("错误", f"游戏以错误代码{result.returncode}退出")
            else:
                self.log("游戏正常退出")
        except Exception as e:
            self.log(f"启动失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动失败: {str(e)}")
        finally:
            # 重新启用启动按钮
            self.launch_button.config(state=tk.NORMAL)
            
    # 创建下载窗口
    def create_download_widgets(self):
        self.dwidgets = tk.Toplevel(self.root)
        self.dwidgets.title("下载版本")
        
        self.dwidgets.geometry(f"500x300+{int((self.root.winfo_screenwidth()-500)/2)}+{int((self.root.winfo_screenheight()-300)/2)}")
        
        self.dwidgets.grab_set()
        self.dwidgets.resizable(False, False)
        
        # 下载窗口主框架
        dmain_frame = ttk.Frame(self.dwidgets, padding="10")
        dmain_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 下载版本选择框架
        download_frame = ttk.LabelFrame(dmain_frame, text="下载版本", padding="10")
        download_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 下载版本选择
        ttk.Label(download_frame, text="选择要下载的版本:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.download_version_var = tk.StringVar()
        self.download_version_combobox = ttk.Combobox(download_frame, textvariable=self.download_version_var, state="readonly", width=40)
        self.download_version_combobox.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.download_version_combobox.bind("<<ComboboxSelected>>", self.load_minecraft_modloader_version)
        
        self.download_modloader_var = tk.StringVar()
        self.download_modloader_var.set('原版')
        self.download_modloader_combobox = ttk.Combobox(download_frame, values = ['原版','Forge','Fabric', 'Quilt'], textvariable=self.download_modloader_var, state="readonly", width=40)
        self.download_modloader_combobox.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.download_modloader_combobox.bind("<<ComboboxSelected>>", self.load_modloader_version)
        
        # 刷新版本列表按钮
        refresh_button = ttk.Button(download_frame, text="刷新版本列表", command=self.load_version_list)
        refresh_button.grid(row=3, column=0, pady=(0, 5))
        
        # 下载按钮
        self.download_button = ttk.Button(download_frame, text="下载", command=self.install_version)
        self.download_button.grid(row=3, column=1, pady=(0, 5))

        # Forge版本框架
        self.forge_version_frame = ttk.LabelFrame(dmain_frame, text="选择Forge版本", padding="10")
        self.forge_version_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Forge版本下拉框
        self.forge_version_var = tk.StringVar()
        self.forge_version_combobox = ttk.Combobox(self.forge_version_frame, textvariable=self.forge_version_var, state="readonly")
        self.forge_version_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Fabric版本框架
        self.fabric_version_frame = ttk.LabelFrame(dmain_frame, text="选择Fabric版本", padding="10")
        self.fabric_version_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Fabric版本下拉框
        self.fabric_version_var = tk.StringVar()
        self.fabric_version_combobox = ttk.Combobox(self.fabric_version_frame, textvariable=self.fabric_version_var, state="readonly")
        self.fabric_version_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Quilt版本框架
        self.quilt_version_frame = ttk.LabelFrame(dmain_frame, text="选择Quilt版本", padding="10")
        self.quilt_version_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Quilt版本下拉框
        self.quilt_version_var = tk.StringVar()
        self.quilt_version_combobox = ttk.Combobox(self.quilt_version_frame, textvariable=self.quilt_version_var, state="readonly")
        self.quilt_version_combobox.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 显示非正式版
        self.show_non_release_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(download_frame, text="显示非正式版", variable=self.show_non_release_var, 
                                           command=lambda: self.load_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 配置网格权重
        self.dwidgets.columnconfigure(0, weight=1)
        self.dwidgets.rowconfigure(0, weight=1)
        dmain_frame.columnconfigure(0, weight=1)
        dmain_frame.columnconfigure(1, weight=1)
        dmain_frame.rowconfigure(0, weight=1)
        dmain_frame.rowconfigure(1, weight=1)
        download_frame.columnconfigure(2, weight=1)
        self.forge_version_frame.columnconfigure(0, weight=1)
        self.fabric_version_frame.columnconfigure(0, weight=1)
        self.quilt_version_frame.columnconfigure(0, weight=1)

        # 加载版本列表
        self.load_version_list()
        self.load_modloader_version(None)

        # 绑定回车键下载
        self.dwidgets.bind("<Return>", lambda event: self.install_version())

    def load_version_list(self):
        """加载Minecraft版本列表"""
        self.log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])
                    
            # 更新下拉列表
            self.download_version_combobox['values'] = self.version_list
                    
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.download_version_var.set(self.version_list[0])

            # 加载模组加载器版本
            self.load_minecraft_modloader_version(None)
                        
            self.log("版本列表加载完成", "INFO")
        except Exception as e:
            self.log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")

    def load_minecraft_modloader_version(self, event):
        """加载MC版本的模组加载器"""
        # 获取信息
        version = self.download_version_var.get()
        modloader = self.download_modloader_var.get()
        version_list = []
        if modloader == "Forge":
            for forge_version in minecraft_launcher_lib.forge.list_forge_versions():
                if f' {version}-' in f' {forge_version}':
                    version_list.append(forge_version)

            self.forge_version_combobox['value'] = version_list
            if version_list:
                self.forge_version_var.set(version_list[0])
            else:
                self.forge_version_var.set('')

        elif modloader == "Fabric":
            if minecraft_launcher_lib.fabric.is_minecraft_version_supported(version):
                for fabric_version in minecraft_launcher_lib.fabric.get_all_loader_versions():
                    version_list.append(fabric_version.get('version', ''))

            self.fabric_version_combobox['value'] = version_list
            if version_list:
                self.fabric_version_var.set(version_list[0])
            else:
                self.fabric_version_var.set('')

        elif modloader == "Quilt":
            if minecraft_launcher_lib.fabric.is_minecraft_version_supported(version):
                for quilt_version in minecraft_launcher_lib.quilt.get_all_loader_versions():
                    version_list.append(quilt_version.get('version', ''))

            self.quilt_version_combobox['value'] = version_list
            if version_list:
                self.quilt_version_var.set(version_list[0])
            else:
                self.quilt_version_var.set('')

    def load_modloader_version(self, event):
        """加载模组加载器版本"""
        modloader = self.download_modloader_var.get()
        if modloader == "原版":
            self.forge_version_frame.grid_remove()
            self.fabric_version_frame.grid_remove()
            self.quilt_version_frame.grid_remove()

        elif modloader == "Forge":
            self.forge_version_frame.grid()
            self.fabric_version_frame.grid_remove()
            self.quilt_version_frame.grid_remove()

        elif modloader == "Fabric":
            self.forge_version_frame.grid_remove()
            self.fabric_version_frame.grid()
            self.quilt_version_frame.grid_remove()

        elif modloader == "Quilt":
            self.forge_version_frame.grid_remove()
            self.fabric_version_frame.grid_remove()
            self.quilt_version_frame.grid()

        # 加载MC版本
        self.load_minecraft_modloader_version(None)

    def install_version(self):
        """下载选中的Minecraft版本"""
        version = self.download_version_var.get()
        if not version:
            messagebox.showwarning("警告", "请先选择一个版本")
            return
            
        # 禁用按钮防止重复点击
        self.download_button.config(state=tk.DISABLED)
        self.launch_button.config(state=tk.DISABLED)

        # 在新线程中执行安装操作
        install_thread = threading.Thread(target=self._install_version_thread, args=(version,))
        install_thread.daemon = True
        install_thread.start()
            
    def _install_version_thread(self, version):
        """在后台线程中安装版本"""
        modloader = self.download_modloader_var.get()

        current_max = 0

        def set_status(status):
            self.log(status.replace("Download", "下载").replace("Running", "运行").replace("Install java runtime", "安装Java环境").replace("Installation complete", "安装完成"), "INFO")

        def set_progress(progress):
            if current_max:
                self.log(f"进度：{progress}/{current_max} {progress / current_max * 100:.1f}%", "INFO")

        def set_max(new_max):
            global current_max
            current_max = new_max

        callback = {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }

        if modloader == '原版':
            try:
                self.log(f"正在安装Minecraft {version}...", "INFO")

                # 安装版本
                minecraft_launcher_lib.install.install_minecraft_version(
                    version,
                    self.minecraft_directory,
                    callback=callback
                )
                self.log(f"Minecraft {version} 安装完成!", "INFO")
                messagebox.showinfo("成功", f"Minecraft {version} 安装完成!")
            except Exception as e:
                self.log(f"安装失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"安装失败: {str(e)}")

        elif modloader == 'Forge':
            try:
                self.log(f"正在安装Forge for Minecraft {version}...", "INFO")

                # 获取选择的Forge版本
                forge_version = self.forge_version_var.get()
                if not forge_version:
                    messagebox.showwarning("警告", "请选择Forge版本！")

                    # 重新启用按钮
                    self.download_button.config(state=tk.NORMAL)
                    self.launch_button.config(state=tk.NORMAL)
                    return

                # 安装Forge
                minecraft_launcher_lib.forge.install_forge_version(
                    forge_version,
                    self.minecraft_directory,
                    callback=callback
                )

                self.log(f"Forge {forge_version} 安装完成!", "INFO")
                messagebox.showinfo("成功", f"Forge {forge_version} 安装完成!")
            except FileNotFoundError:
                self.log("Forge安装失败，可能是没有配置Java环境", "ERROR")
                if messagebox.askyesno("提示", "Forge安装失败，可能是没有配置Java环境，是否配置？"):
                    self.add_java_path()
            except Exception as e:
                self.log(f"Forge安装失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"Forge安装失败: {str(e)}")

        elif modloader == 'Fabric':
            try:
                self.log(f"正在安装Fabric for Minecraft {version}...", "INFO")
                if not self.fabric_version_var.get():
                    messagebox.showwarning("警告", "请选择Fabric版本！")

                    # 重新启用按钮
                    self.download_button.config(state=tk.NORMAL)
                    self.launch_button.config(state=tk.NORMAL)
                    return

                # 安装Fabric
                minecraft_launcher_lib.fabric.install_fabric(
                    version,
                    self.minecraft_directory,
                    loader_version=self.fabric_version_var.get(),
                    callback=callback
                )
                self.log(f"Fabric for Minecraft {version} 安装完成!", "INFO")
                messagebox.showinfo("成功", f"Fabric for Minecraft {version} 安装完成!")
            except FileNotFoundError:
                self.log("Fabric安装失败，可能是没有配置Java环境", "ERROR")
                if messagebox.askyesno("提示", "Fabric安装失败，可能是没有配置Java环境，是否配置？"):
                    self.add_java_path()
            except Exception as e:
                self.log(f"Fabric安装失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"Fabric安装失败: {str(e)}")

        elif modloader == 'Quilt':
            try:
                self.log(f"正在安装Quilt for Minecraft {version}...", "INFO")
                if not self.quilt_version_var.get():
                    messagebox.showwarning("警告", "请选择Quilt版本！")

                    # 重新启用按钮
                    self.download_button.config(state=tk.NORMAL)
                    self.launch_button.config(state=tk.NORMAL)
                    return

                # 安装Quilt
                minecraft_launcher_lib.quilt.install_quilt(
                    version,
                    self.minecraft_directory,
                    loader_version=self.quilt_version_var.get(),
                    callback=callback
                )
                self.log(f"Quilt for Minecraft {version} 安装完成!", "INFO")
                messagebox.showinfo("成功", f"Quilt for Minecraft {version} 安装完成!")
            except FileNotFoundError:
                self.log("Quilt安装失败，可能是没有配置Java环境", "ERROR")
                if messagebox.askyesno("提示", "Quilt安装失败，可能是没有配置Java环境，是否配置？"):
                    self.add_java_path()
            except Exception as e:
                self.log(f"Quilt安装失败: {str(e)}", "ERROR")
                messagebox.showerror("错误", f"Quilt安装失败: {str(e)}")

        # 重新加载已安装版本列表
        self.load_installed_versions()

        # 重新启用按钮
        self.download_button.config(state=tk.NORMAL)
        self.launch_button.config(state=tk.NORMAL)

        # 关闭下载窗口
        self.dwidgets.destroy()

    def add_java_path(self):
        """将Java路径添加到PATH"""
        # 查找Java路径
        for root, dirs, files in os.walk(self.minecraft_directory):
            if 'java.exe' in files:
                java_path = root
                break

        # 添加到PATH
        import winreg
        import ctypes

        def set_environment_variable(name, value):
            try:
                # 打开用户环境变量注册表键
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                    0,  # 默认权限
                    winreg.KEY_WRITE
                )
                # 设置环境变量
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
                winreg.CloseKey(key)
                
                # 通知系统环境变量已更改（使用WM_SETTINGCHANGE消息）
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, 'Environment', 0, 1000, None)
            except PermissionError:
                self.log("权限不足，请右键程序以管理员身份运行！", "WARN")
                messagebox.showinfo("错误", "权限不足，请右键程序以管理员身份运行！")
                sys.exit(1)

        set_environment_variable('PATH', f'{os.environ.get("PATH")};{java_path}')

        self.log("环境配置完成", "INFO")
        messagebox.showinfo("成功", "环境配置完成，请重新安装版本，如果仍然出现此提示请注销后重新登录！")

    # 清理游戏垃圾
    def cleangame(self):
        with open('cleangame.bat', 'w') as cleangame_file:
            cleangame_file.write('''@echo off
%1(start /min cmd.exe /c %0 :& exit)
del /f /s /q "./*.log"
del /f /s /q "./*.log.gz"
rd /s /q "./minecraft/logs"
del /f /s /q "./cleangame.bat"''')
        os.startfile('cleangame.bat')

    def homepage(self):
        """作品（作者）主页"""
        import webbrowser

        # 创建窗口
        homepage_window = tk.Toplevel(self.root)
        homepage_window.title("打开作品（作者）主页")
        homepage_window.geometry(f'300x110+{int((self.root.winfo_screenwidth()-300)/2)}+{int((self.root.winfo_screenheight()-110)/2)}')
        
        homepage_window.grab_set()
        homepage_window.resizable(False, False)

        hmain_frame = ttk.Frame(homepage_window, padding="10")
        hmain_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(hmain_frame, text="选择平台:", width=30, anchor="center", justify="center").pack(fill=tk.BOTH, pady=(0, 5))

        homepage_select_var = tk.StringVar(value="官网")
        ttk.Combobox(hmain_frame, textvariable=homepage_select_var, values=("官网", "Bilibili", "Github", "Github（镜像站）", "Gitcode"), state="readonly", width=20).pack(fill=tk.BOTH, pady=(0, 10))

        def openurl():
            """打开网站"""
            if not homepage_select_var:
                messagebox.showwarning("警告", "请选择平台！")
            elif homepage_select_var.get() == "官网":
                webbrowser.open("https://pmcldownloadserver.dpdns.org")
            elif homepage_select_var.get() == "Bilibili":
                webbrowser.open("https://space.bilibili.com/1191376859")
            elif homepage_select_var.get() == "Github":
                webbrowser.open("https://github.com/Dilideguazi/Python_Minecraft_Launcher")
            elif homepage_select_var.get() == "Github（镜像站）":
                webbrowser.open("https://bgithub.xyz/Dilideguazi/Python_Minecraft_Launcher")
            elif homepage_select_var.get() == "Gitcode":
                webbrowser.open("https://gitcode.com/Dilideguazi/Python_Minecraft_Launcher")
            homepage_window.destroy()

        ttk.Button(hmain_frame, text="确定", command=openurl).pack(side=tk.RIGHT)
        ttk.Button(hmain_frame, text="取消", command=homepage_window.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        


    # 退出
    def _exit(self):
        try:
            if messagebox.askyesno("提示","你是否要退出启动器？"):
                print(f"[{time.asctime()}] 程序正常退出")
                with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
                    f.write(f"[{time.asctime()}] 程序正常退出\n")
                sys.exit(0)
        except:
            sys.exit(0)

    def create_menu(self):
        # 创建菜单
        menu = tk.Menu(self.root)

        # 下载菜单
        download_menu = tk.Menu(menu, tearoff=False)
        download_menu.add_command(label="下载版本", command=self.create_download_widgets)
        download_menu.add_separator()
        download_menu.add_command(label="下载Mod", command=self.create_mod_download_widgets)
        download_menu.add_command(label="下载资源包", command=self.create_resourcepack_download_widgets)
        download_menu.add_command(label="下载光影包", command=self.create_shader_download_widgets)
        download_menu.add_command(label="下载数据包", command=self.create_datapack_download_widgets)
        download_menu.add_command(label="下载整合包", command=self.create_modpack_download_widgets)
        
        # 工具菜单
        tools_menu = tk.Menu(menu, tearoff=False)
        tools_menu.add_command(label="清理游戏垃圾", command=self.cleangame)

        # 帮助菜单
        help_menu = tk.Menu(menu, tearoff = False)
        help_menu.add_command(label="作品（作者）主页", command=self.homepage)
        help_menu.add_command(label = "检查更新",command = lambda: self.check_update(True))
        help_menu.add_command(label="支持与反馈", command=lambda: messagebox.showinfo("支持与反馈","如有意见，请去Gitcode或Github仓库提Issue！"))
        help_menu.add_command(label="关于", command=lambda: messagebox.showinfo("关于","Python Minecraft Launcher (PMCL)\nVersion 1.1.1-hotfix.1\nBilibili @七星五彩 (Github Gitcode & YouTube Dilideguazi)版权所有"))

        # 主菜单
        menu.add_cascade(label="下载", menu=download_menu)
        menu.add_command(label="设置", command=self.create_settings_widgets)
        menu.add_cascade(label="工具", menu=tools_menu)
        menu.add_cascade(label="帮助", menu=help_menu)
        menu.add_command(label="退出", command=self._exit)

        # 配置菜单
        self.root.config(menu=menu)
            
    def load_settings(self):
        """从配置文件加载设置"""
        try:
            settings_file = f"{os.path.abspath('')}/pmcl_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    self.use_custom_java = settings.get("use_custom_java", True)
                    self.use_java = settings.get("use_java", False)
                    self.java_path = settings.get("java_path", None)
                    self.skin_path = settings.get("skin_path", None)
                    self.username_var.set(settings.get("offline_username", ""))
                    self.littleskin_email_var.set(settings.get("littleskin_email", ""))
                    self.memory = settings.get("memory", None)
        except Exception as e:
            self.log(f"加载设置失败: {str(e)}", "ERROR")
            
    def save_settings(self):
        """保存设置到配置文件"""
        try:
            settings_file = f"{os.path.abspath('')}/pmcl_settings.json"
            settings = {
                "use_custom_java": self.use_custom_java,
                "use_java": self.use_java,
                "java_path": self.java_path,
                "skin_path": self.skin_path,
                "offline_username": self.username_var.get(),
                "littleskin_email": self.littleskin_email_var.get(),
                "memory": self.memory
            }
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            self.log(f"保存设置失败: {str(e)}", "ERROR")
            
    # 创建设置窗口
    def create_settings_widgets(self):
        """创建设置窗口"""
        self.settings_window = tk.Toplevel(self.root)
        
        self.settings_window.title("设置")
        
        self.settings_window.grab_set()
        self.settings_window.resizable(False, False)
        
        # 设置窗口主框架
        smain_frame = ttk.Frame(self.settings_window, padding="10")
        smain_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(smain_frame, text="启动器设置", font=("微软雅黑", 18))
        title_label.pack(pady=(0, 10))
        
        # Java设置框架
        java_frame = ttk.LabelFrame(smain_frame, text="Java设置", padding="10")
        java_frame.pack(fill=tk.X, pady=(0, 10))

        self.use_custom_java_var = tk.BooleanVar(value=self.use_custom_java)
        ttk.Checkbutton(java_frame, text="自动选择Java", variable=self.use_custom_java_var, command=self.toggle_use_custom_java_state).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.custom_java_frame = ttk.Frame(java_frame, padding="10")
        self.custom_java_frame.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(self.custom_java_frame, text="Java路径:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.java_path_var = tk.StringVar(value=self.java_path if self.java_path else "")
        self.java_path_entry = ttk.Entry(self.custom_java_frame, textvariable=self.java_path_var, width=30)
        self.java_path_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.java_browse_button = ttk.Button(self.custom_java_frame, text="浏览", command=self.browse_java_path)
        self.java_browse_button.grid(row=1, column=1, padx=(5, 0), pady=(0, 5))

        self.use_java_var = tk.BooleanVar(value=self.use_java)
        self.use_java_checkbox = ttk.Checkbutton(java_frame, text="使用java.exe而不是javaw.exe", variable=self.use_java_var)
        self.use_java_checkbox.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        java_frame.columnconfigure(0, weight=1)
        
        # 内存设置框架
        memory_frame = ttk.LabelFrame(smain_frame, text="内存设置", padding="10")
        memory_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(memory_frame, text="最大内存 (可选，以MB为单位):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.memory_var = tk.StringVar(value=self.memory if self.memory else "")
        self.memory_entry = ttk.Entry(memory_frame, textvariable=self.memory_var, width=30)
        self.memory_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(memory_frame, text="建议: 2048(2GB), 4096(4GB), 8192(8GB)").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        memory_frame.columnconfigure(0, weight=1)
        
        # 皮肤设置框架
        skin_frame = ttk.LabelFrame(smain_frame, text="皮肤设置", padding="10")
        skin_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(skin_frame, text="皮肤文件 (可选，需配合CustomSkinLoader使用):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.skin_path_var = tk.StringVar(value=self.skin_path if self.skin_path else "")
        self.skin_path_entry = ttk.Entry(skin_frame, textvariable=self.skin_path_var, width=30)
        self.skin_path_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.skin_browse_button = ttk.Button(skin_frame, text="浏览", command=self.browse_skin_path)
        self.skin_browse_button.grid(row=1, column=1, padx=(5, 0), pady=(0, 5))
        
        skin_frame.columnconfigure(0, weight=1)
        
        # 按钮框架
        button_frame = ttk.Frame(smain_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 保存按钮
        save_button = ttk.Button(button_frame, text="保存", command=self.save_settings_from_window)
        save_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=self.settings_window.destroy)
        cancel_button.pack(side=tk.RIGHT)

        # 加载设置
        self.load_settings()

        # 根据是否使用自定义Java调整窗口大小
        self.settings_window.geometry(f"500x{450 if self.use_custom_java_var.get() else 540}+{int((self.root.winfo_screenwidth()-500)/2)}+{int((self.root.winfo_screenheight()-(450 if self.use_custom_java_var.get() else 540))/2)}")

        if self.use_custom_java_var.get():
            self.use_java_var.set(self.use_java)
            self.custom_java_frame.grid_remove()
        else:
            self.use_java_checkbox.config(state=tk.DISABLED)
            self.use_java_var.set(True)
        
    def save_settings_from_window(self):
        """从设置窗口保存设置"""
        # 获取Java设置
        use_custom_java = self.use_custom_java_var.get()
        self.use_custom_java = use_custom_java
        
        use_java = self.use_java_var.get()
        self.use_java = use_java
        
        java_path = self.java_path_var.get()
        if not self.use_custom_java:
            if not self.java_path:
                messagebox.showwarning("警告", "请输入Java路径！")
                return
            
        # 获取内存设置
        memory = self.memory_var.get()
        if memory:
            self.memory = memory
        else:
            self.memory = None
            
        # 获取皮肤路径
        skin_path = self.skin_path_var.get()
        if skin_path:
            self.skin_path = skin_path
        else:
            self.skin_path = None
            
        # 保存设置
        self.save_settings()
        
        # 关闭窗口
        self.settings_window.destroy()
        
        self.log("设置已保存", "INFO")
        messagebox.showinfo("成功", "设置已保存")

    def toggle_use_custom_java_state(self):
        """切换使用自定义Java状态"""
        if self.use_custom_java_var.get():
            self.use_java_checkbox.config(state=tk.NORMAL)
            self.use_java_var.set(self.use_java)
            self.custom_java_frame.grid_remove()
            self.settings_window.geometry(f"500x450+{int((self.root.winfo_screenwidth()-500)/2)}+{int((self.root.winfo_screenheight()-450)/2)}")
        else:
            self.use_java_checkbox.config(state=tk.DISABLED)
            self.use_java_var.set(True)
            self.custom_java_frame.grid()
            self.settings_window.geometry(f"500x540+{int((self.root.winfo_screenwidth()-500)/2)}+{int((self.root.winfo_screenheight()-540)/2)}")
            
    # 创建数据包下载窗口
    def create_datapack_download_widgets(self):
        """创建数据包下载窗口"""
        self.datapack_window = tk.Toplevel(self.root)
        self.datapack_window.title("数据包下载")
        self.datapack_window.geometry(f"800x600+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-600)/2)}")
        
        self.datapack_window.resizable(False, False)
        
        # 数据包下载窗口主框架
        datapack_main_frame = ttk.Frame(self.datapack_window, padding="10")
        datapack_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 数据包搜索框架
        search_frame = ttk.LabelFrame(datapack_main_frame, text="搜索数据包", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索关键词:（暂不支持中文搜索）").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.datapack_search_var = tk.StringVar()
        self.datapack_search_entry = ttk.Entry(search_frame, textvariable=self.datapack_search_var, width=40)
        self.datapack_search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_datapacks)
        search_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Minecraft版本选择
        ttk.Label(search_frame, text="Minecraft版本:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.datapack_mc_version_var = tk.StringVar()
        self.datapack_mc_version_combobox = ttk.Combobox(search_frame, textvariable=self.datapack_mc_version_var, state="readonly", width=20)
        self.datapack_mc_version_combobox.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 显示非正式版
        self.show_non_release_datapack_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(search_frame, text="显示非正式版", variable=self.show_non_release_datapack_var, 
                                           command=lambda: self.load_datapack_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(datapack_main_frame, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview来显示搜索结果
        columns = ('name', 'version', 'downloads')
        self.datapacks_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题
        self.datapacks_tree.heading('name', text='数据包名称')
        self.datapacks_tree.heading('version', text='支持的最新版本')
        self.datapacks_tree.heading('downloads', text='下载量')
        
        # 设置列宽
        self.datapacks_tree.column('name', width=300)
        self.datapacks_tree.column('version', width=50)
        self.datapacks_tree.column('downloads', width=100)
        
        # 添加滚动条
        datapacks_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.datapacks_tree.yview)
        self.datapacks_tree.configure(yscrollcommand=datapacks_scrollbar.set)
        
        # 布局
        self.datapacks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        datapacks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载按钮
        self.download_datapack_button = ttk.Button(datapack_main_frame, text="下载选中的数据包", command=self.download_selected_datapack, state=tk.DISABLED)
        self.download_datapack_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        datapack_log_frame = ttk.LabelFrame(datapack_main_frame, text="日志", padding="10")
        datapack_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.datapack_log_text = scrolledtext.ScrolledText(datapack_log_frame, height=6, state=tk.DISABLED)
        self.datapack_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.datapack_window.columnconfigure(0, weight=1)
        self.datapack_window.rowconfigure(0, weight=1)
        datapack_main_frame.columnconfigure(0, weight=1)
        datapack_main_frame.rowconfigure(1, weight=1)
        datapack_main_frame.rowconfigure(3, weight=1)
        search_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        datapack_log_frame.columnconfigure(0, weight=1)
        datapack_log_frame.rowconfigure(0, weight=1)
        
        # 加载Minecraft版本
        self.load_datapack_version_list()
        
        # 绑定Treeview选择事件
        self.datapacks_tree.bind('<<TreeviewSelect>>', self.on_datapack_select)

        # 绑定回车键下载
        self.datapack_window.bind("<Return>", lambda event: self.search_datapacks())

    def load_datapack_version_list(self):
        """加载Minecraft版本列表"""
        self.datapack_log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_datapack_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])

            self.version_list.insert(0, "全部")
                    
            # 更新下拉列表
            self.datapack_mc_version_combobox['value'] = self.version_list

            try:
                self.datapack_minecraft_version_combobox['value'] = self.version_list
                if self.version_list:
                    self.datapack_minecraft_version_var.set(self.version_list[0])
            except:
                pass
            
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.datapack_mc_version_var.set(self.version_list[0])
                    
            self.datapack_log("版本列表加载完成", "INFO")
        except Exception as e:
            self.datapack_log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")
            
    def datapack_log(self, message, level):
        """在数据包日志区域显示消息"""
        print(f"[{time.asctime()}] [datapack/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [datapack/{level}] {message}\n")
        self.datapack_log_text.config(state=tk.NORMAL)
        self.datapack_log_text.insert(tk.END, message + "\n")
        self.datapack_log_text.config(state=tk.DISABLED)
        self.datapack_log_text.see(tk.END)
        
    def search_datapacks(self):
        """搜索数据包"""
        # 禁用搜索按钮防止重复点击
        search_button = None
        for child in self.datapack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        
        if search_button:
            search_button.config(state=tk.DISABLED)
        
        # 在新线程中执行搜索操作
        search_thread = threading.Thread(target=self._search_datapacks_thread)
        search_thread.daemon = True
        search_thread.start()
        
    def _search_datapacks_thread(self):
        """在后台线程中搜索数据包"""
        try:
            # 获取搜索参数
            query = self.datapack_search_var.get()
            mc_version = self.datapack_mc_version_var.get()
            
            self.datapack_log(f"正在搜索数据包: {query}", "INFO")
            
            # 构建查询参数
            params = {}
            if query:
                params['query'] = query
                
            # 构建facets参数
            facets = []
            if mc_version and mc_version != '全部':
                facets.append([f'versions:{mc_version}'])
            
            # 添加项目类型过滤（数据包）
            facets.append(['project_type:datapack'])
                
            if facets:
                params['facets'] = json.dumps(facets)
                
            # 添加排序
            params['index'] = 'relevance'
            params['limit'] = 20
            
            # 构建URL
            base_url = 'https://api.modrinth.com/v2/search'
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            # 发送请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # 在主线程中更新UI
            self.datapack_window.after(0, self._update_datapacks_tree, data)
            
        except Exception as e:
            self.datapack_log(f"搜索失败: {str(e)}", "ERROR")
            # 重新启用搜索按钮
            search_button = None
            for child in self.datapack_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                            search_button = subchild
                            break
            if search_button:
                search_button.config(state=tk.NORMAL)
                
    def _update_datapacks_tree(self, data):
        """更新数据包列表"""
        # 清空现有数据
        for item in self.datapacks_tree.get_children():
            self.datapacks_tree.delete(item)
            
        # 添加新数据
        for hit in data.get('hits', []):
            # 获取最新版本
            versions = hit.get('versions', [])
            latest_version = versions[-1] if versions else '未知'
            
            # 添加到Treeview
            self.datapacks_tree.insert('', tk.END, values=(
                hit.get('title', '未知'),
                latest_version,
                hit.get('downloads', 0)
            ), tags=(hit.get('project_id', ''), hit.get('slug', '')))
            
        self.datapack_log(f"搜索完成，找到 {data.get('total_hits', 0)} 个结果", "INFO")
        
        # 重新启用搜索按钮
        search_button = None
        for child in self.datapack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        if search_button:
            search_button.config(state=tk.NORMAL)
            
    def on_datapack_select(self, event):
        """当选择数据包时"""
        selection = self.datapacks_tree.selection()
        if selection:
            self.download_datapack_button.config(state=tk.NORMAL)
        else:
            self.download_datapack_button.config(state=tk.DISABLED)
            
    def download_selected_datapack(self):
        """下载选中的数据包"""
        selection = self.datapacks_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个数据包")
            return
            
        # 获取选中的数据包信息
        item = self.datapacks_tree.item(selection[0])
        values = item['values']
        datapack_name = values[0] if len(values) > 0 else '未知数据包'

        # 获取项目id
        tags = item['tags']
        project_id = tags[0] if len(tags) > 0 else None
        
        # 禁用下载按钮防止重复点击
        self.download_datapack_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载操作
        download_thread = threading.Thread(target=self._download_datapack_thread, args=(project_id,))
        download_thread.daemon = True
        download_thread.start()
        
    def select_datapack_version(self, versions_data, project_name):
        """选择数据包版本"""
        self.versions_data = versions_data

        # 创建版本选择窗口
        version_window = tk.Toplevel(self.datapack_window)
        version_window.title(f"选择 {project_name} 的版本")
        version_window.geometry(f"800x550+{int((self.datapack_window.winfo_screenwidth()-800)/2)}+{int((self.datapack_window.winfo_screenheight()-550)/2)}")
        
        version_window.grab_set()  # 模态窗口
        version_window.resizable(False, False)
        
        # 版本选择窗口主框架
        version_main_frame = ttk.Frame(version_window, padding="10")
        version_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(version_main_frame, text=f"选择 {project_name} 的版本", font=("微软雅黑", 16))
        title_label.pack(pady=(0, 10))

        # 顶部框架
        top_frame = ttk.Frame(version_main_frame, padding="0")
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 选择想要安装数据包的已安装版本
        self.install_datapack_version_var = tk.StringVar()
        self.install_datapack_version_combobox = ttk.Combobox(top_frame, textvariable=self.install_datapack_version_var, state="readonly", width=20)
        self.install_datapack_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.install_datapack_version_combobox['values'] = self.installed_versions
        self.install_datapack_version_var.set(self.installed_versions[0])
        self.install_datapack_version_combobox.bind("<<ComboboxSelected>>", self.load_world_list)

        # 选择想要安装数据包的MC版本
        self.datapack_minecraft_version_var = tk.StringVar()
        self.datapack_minecraft_version_combobox = ttk.Combobox(top_frame, textvariable=self.datapack_minecraft_version_var, state="readonly", width=20)
        self.datapack_minecraft_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.datapack_minecraft_version_combobox['values'] = self.installed_versions
        self.datapack_minecraft_version_var.set(self.installed_versions[0])
        self.datapack_minecraft_version_combobox.bind("<<ComboboxSelected>>", self.load_datapack_list)

        self.load_datapack_version_list()
        
        # 选择想要安装数据包的世界    
        self.install_datapack_world_var = tk.StringVar()
        self.install_datapack_world_combobox = ttk.Combobox(version_main_frame, textvariable=self.install_datapack_world_var, state="readonly", width=40)
        self.install_datapack_world_combobox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 加载版本和世界列表
        self.load_installed_versions()
        self.load_world_list()
        
        # 版本列表框架
        version_list_frame = ttk.Frame(version_main_frame)
        version_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示版本列表
        version_columns = ('version', 'datapack_filename', 'mc_version', 'type', 'date')
        self.version_tree = ttk.Treeview(version_list_frame, columns=version_columns, show='headings', height=17)
        
        # 定义列标题
        self.version_tree.heading('version', text='版本')
        self.version_tree.heading('datapack_filename', text='文件名')
        self.version_tree.heading('mc_version', text='MC版本')
        self.version_tree.heading('type', text='类型')
        self.version_tree.heading('date', text='发布日期')
        
        # 设置列宽
        self.version_tree.column('version', width=70)
        self.version_tree.column('datapack_filename', width=200)
        self.version_tree.column('mc_version', width=360)
        self.version_tree.column('type', width=50)
        self.version_tree.column('date', width=120)
        
        # 添加滚动条
        version_scrollbar = ttk.Scrollbar(version_list_frame, orient=tk.VERTICAL, command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=version_scrollbar.set)
        
        # 布局
        self.version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充版本数据
        for version in versions_data:
            if self.datapack_minecraft_version_var.get() in version.get('game_versions', []) or self.datapack_minecraft_version_var.get() == "全部":
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
        # 选择的版本变量
        selected_version = [None]  # 使用列表以便在内部函数中修改

        def on_version_select(event):
            """当选择版本时"""
            selection = self.version_tree.selection()
            if selection:
                item = self.version_tree.item(selection[0])
                tags = item['tags']
                if tags:
                    selected_version[0] = tags[0]
        
        def confirm_selection():
            """确认选择"""
            if selected_version[0] is None:
                messagebox.showwarning("警告", "请先选择一个版本")
                return
            version_window.destroy()   
        
        # 绑定选择事件
        self.version_tree.bind('<<TreeviewSelect>>', on_version_select)
        
        # 按钮框架
        button_frame = ttk.Frame(version_main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认按钮
        confirm_button = ttk.Button(button_frame, text="确认", command=confirm_selection)
        confirm_button.pack(side=tk.RIGHT)

        def cancel():
            """取消"""
            selected_version[0] = 'not_selected'
            version_window.destroy()


        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))

        # 重新启用下载按钮
        self.download_datapack_button.config(state=tk.NORMAL)
        
        # 等待窗口关闭
        version_window.wait_window()
        
        # 返回选择的版本ID
        return selected_version[0]
    
    def load_datapack_list(self, event):
        """加载数据包列表"""
        self.version_tree.delete(*self.version_tree.get_children())
        for version in self.versions_data:
            if self.datapack_minecraft_version_var.get() in version.get('game_versions', []) or self.datapack_minecraft_version_var.get() == "全部":
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
    def load_world_list(self, event=None):
        """加载世界列表"""
        try:
            self.init_isolation_state(self.install_datapack_version_var.get())
            # 获取存档目录
            saves_dir = f"{self.isolation_dir}/saves"
            if not os.path.exists(saves_dir):
                os.makedirs(saves_dir)
                
            # 获取世界列表
            worlds = []
            for item in os.listdir(saves_dir):
                item_path = os.path.join(saves_dir, item)
                if os.path.isdir(item_path):
                    # 检查是否是有效的Minecraft世界
                    if os.path.exists(os.path.join(item_path, "level.dat")):
                        worlds.append(item)
            
            # 更新下拉列表
            self.install_datapack_world_combobox['values'] = worlds
            
            # 设置默认选中世界
            if worlds:
                self.install_datapack_world_var.set(worlds[0])
        except Exception as e:
            self.datapack_log(f"加载世界列表失败: {str(e)}", "ERROR")

    def _download_datapack_thread(self, project_id):
        """在后台线程中下载数据包"""
        try:
            if not project_id:
                self.datapack_log("无法获取项目ID", "WARN")
                return
                
            self.datapack_log(f"正在获取数据包信息: {project_id}", "INFO")
            
            # 获取项目详细信息
            project_url = f'https://api.modrinth.com/v2/project/{project_id}'
            req = urllib.request.Request(project_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            project_data = json.loads(response.read().decode())
            
            # 获取项目版本信息
            versions_url = f'https://api.modrinth.com/v2/project/{project_id}/version'
            req = urllib.request.Request(versions_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            versions_data = json.loads(response.read().decode())
            
            # 选择版本
            if not versions_data:
                self.datapack_log("未找到可用版本", "WARN")
                return
            
            # 在主线程中显示版本选择窗口
            selected_version_id = [None]
            def show_version_selector():
                selected_version_id[0] = self.select_datapack_version(versions_data, project_data.get('title', '未知数据包'))
            
            show_version_selector()
            
            # 等待用户选择版本
            while selected_version_id[0] is None:
                import time
                time.sleep(0.1)
            
            if selected_version_id[0] == 'not_selected':
                self.datapack_log("用户取消了版本选择", "WARN")
                return
                
            # 获取选中版本的详细信息
            selected_version = None
            for version in versions_data:
                if version.get('id') == selected_version_id[0]:
                    selected_version = version
                    break
            
            if not selected_version:
                self.datapack_log("无法找到选中的版本", "WARN")
                return
                
            files = selected_version.get('files', [])
            
            if not files:
                self.datapack_log("该版本没有可下载的文件", "WARN")
                return
                
            # 获取第一个文件（主文件）
            file_info = files[0]
            file_url = file_info.get('url')
            file_name = file_info.get('filename')
            
            if not file_url or not file_name:
                self.datapack_log("文件信息不完整", "WARN")
                return
                
            # 确定保存路径
            world_name = self.install_datapack_world_var.get()
            if not world_name:
                self.datapack_log("未选择世界", "WARN")
                return
                
            datapacks_dir = f"{self.isolation_dir}/saves/{world_name}/datapacks"
            if not os.path.exists(datapacks_dir):
                os.makedirs(datapacks_dir)
                
            save_path = f"{datapacks_dir}/{file_name}"
            
            self.datapack_log(f"正在下载: {file_name}", "INFO")
            
            # 下载文件
            def progress_callback(block_num, block_size, total_size):
                percent = min(100, int(block_num * block_size * 100 / total_size))
                self.datapack_window.after(0, lambda: self.datapack_log(f"下载进度: {percent}%", "INFO"))
                
            urllib.request.urlretrieve(file_url, save_path, reporthook=progress_callback)
            
            self.datapack_log(f"数据包下载完成: {save_path}", "INFO")
            
            self.datapack_window.after(0, lambda: messagebox.showinfo("成功", f"数据包下载完成!\n保存至: {save_path}"))
            
        except Exception as e:
            self.datapack_log(f"下载失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {str(e)}")
        finally:
            # 重新启用下载按钮
            self.datapack_window.after(0, lambda: self.download_datapack_button.config(state=tk.NORMAL))

    # 创建资源包下载窗口
    def create_resourcepack_download_widgets(self):
        """创建资源包下载窗口"""
        self.resourcepack_window = tk.Toplevel(self.root)
        self.resourcepack_window.title("资源包下载")
        self.resourcepack_window.geometry(f"800x600+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-600)/2)}")
        
        self.resourcepack_window.resizable(False, False)
        
        # 资源包下载窗口主框架
        resourcepack_main_frame = ttk.Frame(self.resourcepack_window, padding="10")
        resourcepack_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 资源包搜索框架
        search_frame = ttk.LabelFrame(resourcepack_main_frame, text="搜索资源包", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索关键词:（暂不支持中文搜索）").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.resourcepack_search_var = tk.StringVar()
        self.resourcepack_search_entry = ttk.Entry(search_frame, textvariable=self.resourcepack_search_var, width=40)
        self.resourcepack_search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_resourcepacks)
        search_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Minecraft版本选择
        ttk.Label(search_frame, text="Minecraft版本:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.resourcepack_mc_version_var = tk.StringVar()
        self.resourcepack_mc_version_combobox = ttk.Combobox(search_frame, textvariable=self.resourcepack_mc_version_var, state="readonly", width=20)
        self.resourcepack_mc_version_combobox.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 显示非正式版
        self.show_non_release_resourcepack_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(search_frame, text="显示非正式版", variable=self.show_non_release_resourcepack_var, 
                                           command=lambda: self.load_resourcepack_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(resourcepack_main_frame, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview来显示搜索结果
        columns = ('name', 'version', 'downloads')
        self.resourcepacks_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题
        self.resourcepacks_tree.heading('name', text='资源包名称')
        self.resourcepacks_tree.heading('version', text='支持的最新版本')
        self.resourcepacks_tree.heading('downloads', text='下载量')
        
        # 设置列宽
        self.resourcepacks_tree.column('name', width=300)
        self.resourcepacks_tree.column('version', width=50)
        self.resourcepacks_tree.column('downloads', width=100)
        
        # 添加滚动条
        resourcepacks_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.resourcepacks_tree.yview)
        self.resourcepacks_tree.configure(yscrollcommand=resourcepacks_scrollbar.set)
        
        # 布局
        self.resourcepacks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        resourcepacks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载按钮
        self.download_resourcepack_button = ttk.Button(resourcepack_main_frame, text="下载选中的资源包", command=self.download_selected_resourcepack, state=tk.DISABLED)
        self.download_resourcepack_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        resourcepack_log_frame = ttk.LabelFrame(resourcepack_main_frame, text="日志", padding="10")
        resourcepack_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.resourcepack_log_text = scrolledtext.ScrolledText(resourcepack_log_frame, height=6, state=tk.DISABLED)
        self.resourcepack_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.resourcepack_window.columnconfigure(0, weight=1)
        self.resourcepack_window.rowconfigure(0, weight=1)
        resourcepack_main_frame.columnconfigure(0, weight=1)
        resourcepack_main_frame.rowconfigure(1, weight=1)
        resourcepack_main_frame.rowconfigure(3, weight=1)
        search_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        resourcepack_log_frame.columnconfigure(0, weight=1)
        resourcepack_log_frame.rowconfigure(0, weight=1)
        
        # 加载Minecraft版本
        self.load_resourcepack_version_list()
        
        # 绑定Treeview选择事件
        self.resourcepacks_tree.bind('<<TreeviewSelect>>', self.on_resourcepack_select)

        # 绑定回车键下载
        self.resourcepack_window.bind("<Return>", lambda event: self.search_resourcepacks())

    def load_resourcepack_version_list(self):
        """加载Minecraft版本列表"""
        self.resourcepack_log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_resourcepack_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])

            self.version_list.insert(0, "全部")
                    
            # 更新下拉列表
            self.resourcepack_mc_version_combobox['value'] = self.version_list

            try:
                self.resourcepack_minecraft_version_combobox['value'] = self.version_list
                if self.version_list:
                    self.resourcepack_minecraft_version_var.set(self.version_list[0])
            except:
                pass
            
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.resourcepack_mc_version_var.set(self.version_list[0])
                    
            self.resourcepack_log("版本列表加载完成", "INFO")
        except Exception as e:
            self.resourcepack_log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")
            
    def resourcepack_log(self, message, level):
        """在资源包日志区域显示消息"""
        print(f"[{time.asctime()}] [resourcepack/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [resourcepack/{level}] {message}\n")
        self.resourcepack_log_text.config(state=tk.NORMAL)
        self.resourcepack_log_text.insert(tk.END, message + "\n")
        self.resourcepack_log_text.config(state=tk.DISABLED)
        self.resourcepack_log_text.see(tk.END)
        
    def search_resourcepacks(self):
        """搜索资源包"""
        # 禁用搜索按钮防止重复点击
        search_button = None
        for child in self.resourcepack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        
        if search_button:
            search_button.config(state=tk.DISABLED)
        
        # 在新线程中执行搜索操作
        search_thread = threading.Thread(target=self._search_resourcepacks_thread)
        search_thread.daemon = True
        search_thread.start()
        
    def _search_resourcepacks_thread(self):
        """在后台线程中搜索资源包"""
        try:
            # 获取搜索参数
            query = self.resourcepack_search_var.get()
            mc_version = self.resourcepack_mc_version_var.get()
            
            self.resourcepack_log(f"正在搜索资源包: {query}", "INFO")
            
            # 构建查询参数
            params = {}
            if query:
                params['query'] = query
                
            # 构建facets参数
            facets = []
            if mc_version and mc_version != '全部':
                facets.append([f'versions:{mc_version}'])
            
            # 添加项目类型过滤（资源包）
            facets.append(['project_type:resourcepack'])
                
            if facets:
                params['facets'] = json.dumps(facets)
                
            # 添加排序
            params['index'] = 'relevance'
            params['limit'] = 20
            
            # 构建URL
            base_url = 'https://api.modrinth.com/v2/search'
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            # 发送请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # 在主线程中更新UI
            self.resourcepack_window.after(0, self._update_resourcepacks_tree, data)
            
        except Exception as e:
            self.resourcepack_log(f"搜索失败: {str(e)}", "ERROR")
            # 重新启用搜索按钮
            search_button = None
            for child in self.resourcepack_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                            search_button = subchild
                            break
            if search_button:
                search_button.config(state=tk.NORMAL)
                
    def _update_resourcepacks_tree(self, data):
        """更新资源包列表"""
        # 清空现有数据
        for item in self.resourcepacks_tree.get_children():
            self.resourcepacks_tree.delete(item)
            
        # 添加新数据
        for hit in data.get('hits', []):
            # 获取最新版本
            versions = hit.get('versions', [])
            latest_version = versions[-1] if versions else '未知'
            
            # 添加到Treeview
            self.resourcepacks_tree.insert('', tk.END, values=(
                hit.get('title', '未知'),
                latest_version,
                hit.get('downloads', 0)
            ), tags=(hit.get('project_id', ''), hit.get('slug', '')))
            
        self.resourcepack_log(f"搜索完成，找到 {data.get('total_hits', 0)} 个结果", "INFO")
        
        # 重新启用搜索按钮
        search_button = None
        for child in self.resourcepack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        if search_button:
            search_button.config(state=tk.NORMAL)
            
    def on_resourcepack_select(self, event):
        """当选择资源包时"""
        selection = self.resourcepacks_tree.selection()
        if selection:
            self.download_resourcepack_button.config(state=tk.NORMAL)
        else:
            self.download_resourcepack_button.config(state=tk.DISABLED)
            
    def download_selected_resourcepack(self):
        """下载选中的资源包"""
        selection = self.resourcepacks_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个资源包")
            return
            
        # 获取选中的资源包信息
        item = self.resourcepacks_tree.item(selection[0])
        values = item['values']
        resourcepack_name = values[0] if len(values) > 0 else '未知资源包'

        # 获取项目id
        tags = item['tags']
        project_id = tags[0] if len(tags) > 0 else None
        
        # 禁用下载按钮防止重复点击
        self.download_resourcepack_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载操作
        download_thread = threading.Thread(target=self._download_resourcepack_thread, args=(project_id,))
        download_thread.daemon = True
        download_thread.start()
        
    def select_resourcepack_version(self, versions_data, project_name):
        """选择资源包版本"""
        self.versions_data = versions_data

        # 创建版本选择窗口
        version_window = tk.Toplevel(self.resourcepack_window)
        version_window.title(f"选择 {project_name} 的版本")
        version_window.geometry(f"800x500+{int((self.resourcepack_window.winfo_screenwidth()-800)/2)}+{int((self.resourcepack_window.winfo_screenheight()-500)/2)}")
        version_window.grab_set()  # 模态窗口
        version_window.resizable(False, False)
        
        # 版本选择窗口主框架
        version_main_frame = ttk.Frame(version_window, padding="10")
        version_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(version_main_frame, text=f"选择 {project_name} 的版本", font=("微软雅黑", 16))
        title_label.pack(pady=(0, 10))

        # 顶部框架
        top_frame = ttk.Frame(version_main_frame, padding="0")
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 选择想要安装资源包的MC版本
        self.install_resourcepack_version_var = tk.StringVar()
        self.install_resourcepack_version_combobox = ttk.Combobox(top_frame, textvariable=self.install_resourcepack_version_var, state="readonly", width=20)
        self.install_resourcepack_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.install_resourcepack_version_combobox['values'] = self.installed_versions
        self.install_resourcepack_version_var.set(self.installed_versions[0])

        # 选择资源包的MC版本
        self.resourcepack_minecraft_version_var = tk.StringVar()
        self.resourcepack_minecraft_version_combobox = ttk.Combobox(top_frame, textvariable=self.resourcepack_minecraft_version_var, state="readonly", width=20)
        self.resourcepack_minecraft_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.resourcepack_minecraft_version_combobox.bind("<<ComboboxSelected>>", self.load_resourcepack_version)

        self.load_resourcepack_version_list()

        # 版本列表框架
        version_list_frame = ttk.Frame(version_main_frame)
        version_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示版本列表
        version_columns = ('version', 'resourcepack_filename', 'mc_version', 'type', 'date')
        self.version_tree = ttk.Treeview(version_list_frame, columns=version_columns, show='headings', height=17)
        
        # 定义列标题
        self.version_tree.heading('version', text='版本')
        self.version_tree.heading('resourcepack_filename', text='文件名')
        self.version_tree.heading('mc_version', text='MC版本')
        self.version_tree.heading('type', text='类型')
        self.version_tree.heading('date', text='发布日期')
        
        # 设置列宽
        self.version_tree.column('version', width=70)
        self.version_tree.column('resourcepack_filename', width=200)
        self.version_tree.column('mc_version', width=360)
        self.version_tree.column('type', width=50)
        self.version_tree.column('date', width=120)
        
        # 添加滚动条
        version_scrollbar = ttk.Scrollbar(version_list_frame, orient=tk.VERTICAL, command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=version_scrollbar.set)
        
        # 布局
        self.version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充版本数据
        for version in versions_data:
            if self.resourcepack_minecraft_version_var.get() == "全部" or self.resourcepack_minecraft_version_var.get() in version.get('game_versions', []):
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
        # 选择的版本变量
        selected_version = [None]  # 使用列表以便在内部函数中修改

        def on_version_select(event):
            """当选择版本时"""
            selection = self.version_tree.selection()
            if selection:
                item = self.version_tree.item(selection[0])
                tags = item['tags']
                if tags:
                    selected_version[0] = tags[0]
        
        def confirm_selection():
            """确认选择"""
            if selected_version[0] is None:
                messagebox.showwarning("警告", "请先选择一个版本")
                return
            version_window.destroy()
        
        # 绑定选择事件
        self.version_tree.bind('<<TreeviewSelect>>', on_version_select)
        
        # 按钮框架
        button_frame = ttk.Frame(version_main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认按钮
        confirm_button = ttk.Button(button_frame, text="确认", command=confirm_selection)
        confirm_button.pack(side=tk.RIGHT)

        def cancel():
            """取消"""
            selected_version[0] = 'not_installed'
            version_window.destroy()


        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))

        # 重新启用下载按钮
        self.download_resourcepack_button.config(state=tk.NORMAL)
        
        # 等待窗口关闭
        version_window.wait_window()
        
        # 返回选择的版本ID
        return selected_version[0]
    
    def load_resourcepack_version(self, event):
        """加载资源包版本"""
        self.version_tree.delete(*self.version_tree.get_children())

        # 填充版本数据
        for version in self.versions_data:
            if self.resourcepack_minecraft_version_var.get() == "全部" or self.resourcepack_minecraft_version_var.get() in version.get('game_versions', []):
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
    def _download_resourcepack_thread(self, project_id):
        """在后台线程中下载资源包"""
        try:
            if not project_id:
                self.resourcepack_log("无法获取项目ID", "WARN")
                return
                
            self.resourcepack_log(f"正在获取资源包信息: {project_id}", "INFO")
            
            # 获取项目详细信息
            project_url = f'https://api.modrinth.com/v2/project/{project_id}'
            req = urllib.request.Request(project_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            project_data = json.loads(response.read().decode())
            
            # 获取项目版本信息
            versions_url = f'https://api.modrinth.com/v2/project/{project_id}/version'
            req = urllib.request.Request(versions_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            versions_data = json.loads(response.read().decode())
            
            # 选择版本
            if not versions_data:
                self.resourcepack_log("未找到可用版本", "WARN")
                return
            
            # 在主线程中显示版本选择窗口
            selected_version_id = [None]
            def show_version_selector():
                selected_version_id[0] = self.select_resourcepack_version(versions_data, project_data.get('title', '未知资源包'))
            
            show_version_selector()
            
            # 等待用户选择版本
            while selected_version_id[0] is None:
                import time
                time.sleep(0.1)
            
            if selected_version_id[0] == 'not_selected':
                self.resourcepack_log("用户取消了版本选择", "WARN")
                return
                
            # 获取选中版本的详细信息
            selected_version = None
            for version in versions_data:
                if version.get('id') == selected_version_id[0]:
                    selected_version = version
                    break
            
            if not selected_version:
                self.resourcepack_log("无法找到选中的版本", "WARN")
                return
                
            files = selected_version.get('files', [])
            
            if not files:
                self.resourcepack_log("该版本没有可下载的文件", "WARN")
                return
                
            # 获取第一个文件（主文件）
            file_info = files[0]
            file_url = file_info.get('url')
            file_name = file_info.get('filename')
            
            if not file_url or not file_name:
                self.resourcepack_log("文件信息不完整", "WARN")
                return
                
            # 确定保存路径
            self.init_isolation_state(self.install_resourcepack_version_var.get())
            resourcepacks_dir = f"{self.isolation_dir}/resourcepacks"
            if not os.path.exists(resourcepacks_dir):
                os.makedirs(resourcepacks_dir)
                
            save_path = f"{resourcepacks_dir}/{file_name}"
            
            self.resourcepack_log(f"正在下载: {file_name}", "INFO")
            
            # 下载文件
            def progress_callback(block_num, block_size, total_size):
                percent = min(100, int(block_num * block_size * 100 / total_size))
                self.resourcepack_window.after(0, lambda: self.resourcepack_log(f"下载进度: {percent}%", "INFO"))
                
            urllib.request.urlretrieve(file_url, save_path, reporthook=progress_callback)
            
            self.resourcepack_log(f"资源包下载完成: {save_path}", "INFO")
            
            self.resourcepack_window.after(0, lambda: messagebox.showinfo("成功", f"资源包下载完成!\n保存至: {save_path}"))
            
        except Exception as e:
            self.resourcepack_log(f"下载失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {str(e)}")
        finally:
            # 重新启用下载按钮
            self.resourcepack_window.after(0, lambda: self.download_resourcepack_button.config(state=tk.NORMAL))

    # 创建Mod下载窗口
    def create_mod_download_widgets(self):
        """创建Mod下载窗口"""
        self.mod_window = tk.Toplevel(self.root)
        self.mod_window.title("Mod下载")
        self.mod_window.geometry(f"800x600+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-600)/2)}")
        
        self.mod_window.resizable(False, False)
        
        # Mod下载窗口主框架
        mod_main_frame = ttk.Frame(self.mod_window, padding="10")
        mod_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Mod搜索框架
        search_frame = ttk.LabelFrame(mod_main_frame, text="搜索Mod", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索关键词:（暂不支持中文搜索）").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.mod_search_var = tk.StringVar()
        self.mod_search_entry = ttk.Entry(search_frame, textvariable=self.mod_search_var, width=40)
        self.mod_search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_mods)
        search_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Minecraft版本选择
        ttk.Label(search_frame, text="Minecraft版本:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.mod_mc_version_var = tk.StringVar()
        self.mod_mc_version_combobox = ttk.Combobox(search_frame, textvariable=self.mod_mc_version_var, state="readonly", width=20)
        self.mod_mc_version_combobox.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Mod加载器选择
        ttk.Label(search_frame, text="Mod加载器:").grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        self.mod_loader_var = tk.StringVar()
        self.mod_loader_var.set('全部')
        self.mod_loader_combobox = ttk.Combobox(search_frame, values=['全部', 'Forge', 'Fabric', 'Quilt'], textvariable=self.mod_loader_var, state="readonly", width=20)
        self.mod_loader_combobox.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # 显示非正式版
        self.show_non_release_mod_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(search_frame, text="显示非正式版", variable=self.show_non_release_mod_var, 
                                           command=lambda: self.load_mod_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(mod_main_frame, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview来显示搜索结果
        columns = ('name', 'version', 'downloads')
        self.mods_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题
        self.mods_tree.heading('name', text='Mod名称')
        self.mods_tree.heading('version', text='支持的最新版本')
        self.mods_tree.heading('downloads', text='下载量')
        
        # 设置列宽
        self.mods_tree.column('name', width=300)
        self.mods_tree.column('version', width=50)
        self.mods_tree.column('downloads', width=100)
        
        # 添加滚动条
        mods_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=mods_scrollbar.set)
        
        # 布局
        self.mods_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        mods_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载按钮
        self.download_mod_button = ttk.Button(mod_main_frame, text="下载选中的Mod", command=self.download_selected_mod, state=tk.DISABLED)
        self.download_mod_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        mod_log_frame = ttk.LabelFrame(mod_main_frame, text="日志", padding="10")
        mod_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.mod_log_text = scrolledtext.ScrolledText(mod_log_frame, height=6, state=tk.DISABLED)
        self.mod_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.mod_window.columnconfigure(0, weight=1)
        self.mod_window.rowconfigure(0, weight=1)
        mod_main_frame.columnconfigure(0, weight=1)
        mod_main_frame.rowconfigure(1, weight=1)
        mod_main_frame.rowconfigure(3, weight=1)
        search_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        mod_log_frame.columnconfigure(0, weight=1)
        mod_log_frame.rowconfigure(0, weight=1)
        
        # 加载Minecraft版本
        self.load_mod_version_list()
        
        # 绑定Treeview选择事件
        self.mods_tree.bind('<<TreeviewSelect>>', self.on_mod_select)

        # 绑定回车键下载
        self.mod_window.bind("<Return>", lambda event: self.search_mods())

    def load_mod_version_list(self):
        """加载Minecraft版本列表"""
        self.mod_log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_mod_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])

            self.version_list.insert(0, "全部")
                    
            # 更新下拉列表
            self.mod_mc_version_combobox['value'] = self.version_list

            try:
                self.mod_minecraft_version_combobox['value'] = self.version_list
                if self.version_list:
                    self.mod_minecraft_version_var.set(self.version_list[0])
            except:
                pass
            
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.mod_mc_version_var.set(self.version_list[0])
                    
            self.mod_log("版本列表加载完成", "INFO")
        except Exception as e:
            self.mod_log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")
            
    def mod_log(self, message, level):
        """在Mod日志区域显示消息"""
        print(f"[{time.asctime()}] [mod/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [mod/{level}] {message}\n")
        
        self.mod_log_text.config(state=tk.NORMAL)
        self.mod_log_text.insert(tk.END, message + "\n")
        self.mod_log_text.config(state=tk.DISABLED)
        self.mod_log_text.see(tk.END)
        
    def search_mods(self):
        """搜索Mods"""
        # 禁用搜索按钮防止重复点击
        search_button = None
        for child in self.mod_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        
        if search_button:
            search_button.config(state=tk.DISABLED)
        
        # 在新线程中执行搜索操作
        search_thread = threading.Thread(target=self._search_mods_thread)
        search_thread.daemon = True
        search_thread.start()
        
    def _search_mods_thread(self):
        """在后台线程中搜索Mods"""
        try:
            # 获取搜索参数
            query = self.mod_search_var.get()
            mc_version = self.mod_mc_version_var.get()
            loader = self.mod_loader_var.get()
            
            self.mod_log(f"正在搜索Mods: {query}", "INFO")
            
            # 构建查询参数
            params = {}
            if query:
                params['query'] = query
                
            # 构建facets参数
            facets = []
            if mc_version and mc_version != '全部':
                facets.append([f'versions:{mc_version}'])
            if loader and loader != '全部':
                facets.append([f'categories:{loader.lower()}'])
                
            if facets:
                params['facets'] = json.dumps(facets)
                
            # 添加项目类型过滤
            params['index'] = 'relevance'
            params['limit'] = 20
            
            # 构建URL
            base_url = 'https://api.modrinth.com/v2/search'
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            # 发送请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # 在主线程中更新UI
            self.mod_window.after(0, self._update_mods_tree, data)
            
        except Exception as e:
            self.mod_log(f"搜索失败: {str(e)}", "ERROR")
            # 重新启用搜索按钮
            search_button = None
            for child in self.mod_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                            search_button = subchild
                            break
            if search_button:
                search_button.config(state=tk.NORMAL)
                
    def _update_mods_tree(self, data):
        """更新Mods列表"""
        # 清空现有数据
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
            
        # 添加新数据
        for hit in data.get('hits', []):
            # 获取最新版本
            versions = hit.get('versions', [])
            latest_version = versions[-1] if versions else '未知'
            
            # 添加到Treeview
            self.mods_tree.insert('', tk.END, values=(
                hit.get('title', '未知'),
                latest_version,
                hit.get('downloads', 0)
            ), tags=(hit.get('project_id', ''), hit.get('slug', '')))
            
        self.mod_log(f"搜索完成，找到 {data.get('total_hits', 0)} 个结果", "INFO")
        
        # 重新启用搜索按钮
        search_button = None
        for child in self.mod_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        if search_button:
            search_button.config(state=tk.NORMAL)
            
    def on_mod_select(self, event):
        """当选择Mod时"""
        selection = self.mods_tree.selection()
        if selection:
            self.download_mod_button.config(state=tk.NORMAL)
        else:
            self.download_mod_button.config(state=tk.DISABLED)
            
    def download_selected_mod(self):
        """下载选中的Mod"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个Mod")
            return
            
        # 获取选中的Mod信息
        item = self.mods_tree.item(selection[0])
        values = item['values']
        mod_name = values[0] if len(values) > 0 else '未知Mod'

        # 获取项目id
        tags = item['tags']
        project_id = tags[0] if len(tags) > 0 else None
        
        # 禁用下载按钮防止重复点击
        self.download_mod_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载操作
        download_thread = threading.Thread(target=self._download_mod_thread, args=(project_id,))
        download_thread.daemon = True
        download_thread.start()
        
    def select_mod_version(self, versions_data, project_name):
        """选择Mod版本"""
        self.versions_data = versions_data

        # 创建版本选择窗口
        version_window = tk.Toplevel(self.mod_window)
        version_window.title(f"选择 {project_name} 的版本")
        version_window.geometry(f"800x500+{int((self.mod_window.winfo_screenwidth()-800)/2)}+{int((self.mod_window.winfo_screenheight()-500)/2)}")
        
        version_window.grab_set()  # 模态窗口
        version_window.resizable(False, False)
        
        # 版本选择窗口主框架
        version_main_frame = ttk.Frame(version_window, padding="10")
        version_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(version_main_frame, text=f"选择 {project_name} 的版本", font=("微软雅黑", 16))
        title_label.pack(pady=(0, 10))

        # 顶部框架
        top_frame = ttk.Frame(version_main_frame, padding="0")
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 选择想要安装Mod的版本
        self.install_mod_version_var = tk.StringVar()
        self.install_mod_version_combobox = ttk.Combobox(top_frame, textvariable=self.install_mod_version_var, state="readonly", width=20)
        self.install_mod_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.install_mod_version_combobox['values'] = self.installed_versions
        self.install_mod_version_var.set(self.installed_versions[0])

        # 选择Mod的MC版本
        self.mod_minecraft_version_var = tk.StringVar()
        self.mod_minecraft_version_combobox = ttk.Combobox(top_frame, textvariable=self.mod_minecraft_version_var, state="readonly", width=20)
        self.mod_minecraft_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.mod_minecraft_version_combobox.bind("<<ComboboxSelected>>", self.load_mod_list)

        self.load_mod_version_list()

        # 选择Mod的模组加载器版本
        self.mod_modloader_var = tk.StringVar()
        self.mod_modloader_combobox = ttk.Combobox(top_frame, textvariable=self.mod_modloader_var, state="readonly", width=20)
        self.mod_modloader_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.mod_modloader_combobox['values'] = ("全部", "Forge", "Fabric", "Quilt")
        self.mod_modloader_var.set("全部")
        self.mod_modloader_combobox.bind("<<ComboboxSelected>>", self.load_mod_list)

        # 版本列表框架
        version_list_frame = ttk.Frame(version_main_frame)
        version_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示版本列表
        version_columns = ('version', 'mod_filename', 'mod_loader', 'mc_version', 'type', 'date')
        self.version_tree = ttk.Treeview(version_list_frame, columns=version_columns, show='headings', height=17)
        
        # 定义列标题
        self.version_tree.heading('version', text='版本')
        self.version_tree.heading('mod_filename', text='文件名')
        self.version_tree.heading('mod_loader', text='模组加载器')
        self.version_tree.heading('mc_version', text='MC版本')
        self.version_tree.heading('type', text='类型')
        self.version_tree.heading('date', text='发布日期')
        
        # 设置列宽
        self.version_tree.column('version', width=170)
        self.version_tree.column('mod_filename', width=250)
        self.version_tree.column('mod_loader', width=70)
        self.version_tree.column('mc_version', width=150)
        self.version_tree.column('type', width=50)
        self.version_tree.column('date', width=120)
        
        # 添加滚动条
        version_scrollbar = ttk.Scrollbar(version_list_frame, orient=tk.VERTICAL, command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=version_scrollbar.set)
        
        # 布局
        self.version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充版本数据
        for version in versions_data:
            if self.mod_minecraft_version_var.get() in version.get('game_versions', []) or self.mod_minecraft_version_var.get() == "全部":
                if self.mod_modloader_var.get().lower() in version.get('loaders', []) or self.mod_modloader_var.get() == "全部":
                    self.version_tree.insert('', tk.END, values=(
                        version.get('version_number', '未知'),
                        version.get('files', [])[0].get('filename','未知'),
                        version.get('loaders', []),
                        ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                        version.get('version_type', '未知'),
                        version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                    ), tags=(version.get('id'),))
        
        # 选择的版本变量
        selected_version = [None]  # 使用列表以便在内部函数中修改

        def on_version_select(event):
            """当选择版本时"""
            selection = self.version_tree.selection()
            if selection:
                item = self.version_tree.item(selection[0])
                tags = item['tags']
                if tags:
                    selected_version[0] = tags[0]
        
        def confirm_selection():
            """确认选择"""
            if selected_version[0] is None:
                messagebox.showwarning("警告", "请先选择一个版本")
                return
            version_window.destroy()
        
        # 绑定选择事件
        self.version_tree.bind('<<TreeviewSelect>>', on_version_select)
        
        # 按钮框架
        button_frame = ttk.Frame(version_main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认按钮
        confirm_button = ttk.Button(button_frame, text="确认", command=confirm_selection)
        confirm_button.pack(side=tk.RIGHT)

        def cancel():
            """取消"""
            selected_version[0] = 'not_selected'
            version_window.destroy()


        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))

        # 重新启用下载按钮
        self.download_mod_button.config(state=tk.NORMAL)
        
        # 等待窗口关闭
        version_window.wait_window()
        
        # 返回选择的版本ID
        return selected_version[0]
    
    def load_mod_list(self, event):
        """加载mod版本"""
        self.version_tree.delete(*self.version_tree.get_children())
        for version in self.versions_data:
            if self.mod_minecraft_version_var.get() in version.get('game_versions', []) or self.mod_minecraft_version_var.get() == "全部":
                if self.mod_modloader_var.get().lower() in version.get('loaders', []) or self.mod_modloader_var.get() == "全部":
                    self.version_tree.insert('', tk.END, values=(
                        version.get('version_number', '未知'),
                        version.get('files', [])[0].get('filename','未知'),
                        version.get('loaders', []),
                        ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                        version.get('version_type', '未知'),
                        version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                    ), tags=(version.get('id'),))
        
    def _download_mod_thread(self, project_id):
        """在后台线程中下载Mod"""
        try:
            if not project_id:
                self.mod_log("无法获取项目ID", "WARN")
                return
                
            self.mod_log(f"正在获取Mod信息: {project_id}", "INFO")
            
            # 获取项目详细信息
            project_url = f'https://api.modrinth.com/v2/project/{project_id}'
            req = urllib.request.Request(project_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            project_data = json.loads(response.read().decode())
            
            # 获取项目版本信息
            versions_url = f'https://api.modrinth.com/v2/project/{project_id}/version'
            req = urllib.request.Request(versions_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            versions_data = json.loads(response.read().decode())
            
            # 选择版本
            if not versions_data:
                self.mod_log("未找到可用版本", "WARN")
                return
            
            # 在主线程中显示版本选择窗口
            selected_version_id = [None]
            def show_version_selector():
                selected_version_id[0] = self.select_mod_version(versions_data, project_data.get('title', '未知Mod'))
            
            show_version_selector()
            
            # 等待用户选择版本
            while selected_version_id[0] is None:
                import time
                time.sleep(0.1)
            
            if selected_version_id[0] == 'not_selected':
                self.mod_log("用户取消了版本选择", "WARN")
                return
                
            # 获取选中版本的详细信息
            selected_version = None
            for version in versions_data:
                if version.get('id') == selected_version_id[0]:
                    selected_version = version
                    break
            
            if not selected_version:
                self.mod_log("无法找到选中的版本", "WARN")
                return
                
            files = selected_version.get('files', [])
            
            if not files:
                self.mod_log("该版本没有可下载的文件", "WARN")
                return
                
            # 获取第一个文件（主文件）
            file_info = files[0]
            file_url = file_info.get('url')
            file_name = file_info.get('filename')
            
            if not file_url or not file_name:
                self.mod_log("文件信息不完整", "WARN")
                return
                
            # 确定保存路径
            self.init_isolation_state(self.install_mod_version_var.get())
            mods_dir = f"{self.isolation_dir}/mods"
            if not os.path.exists(mods_dir):
                os.makedirs(mods_dir)
                
            save_path = f"{mods_dir}/{file_name}"
            
            self.mod_log(f"正在下载: {file_name}", "INFO")
            
            # 下载文件
            def progress_callback(block_num, block_size, total_size):
                percent = min(100, int(block_num * block_size * 100 / total_size))
                self.mod_window.after(0, lambda: self.mod_log(f"下载进度: {percent}%", "INFO"))
                
            urllib.request.urlretrieve(file_url, save_path, reporthook=progress_callback)
            
            self.mod_log(f"Mod下载完成: {save_path}", "INFO")
            
            # 处理依赖
            dependencies = selected_version.get('dependencies', [])
            self.required_dep_counter = 0
            for dep in dependencies:
                if dep.get('dependency_type') == 'required':
                    self.required_dep_counter += 1
            if dependencies:
                self.mod_log(f"发现 {len(dependencies)} 个依赖项，{self.required_dep_counter}个重要，正在处理...", "INFO")
                self._download_dependencies(dependencies)
            
            self.mod_window.after(0, lambda: messagebox.showinfo("成功", f"Mod下载完成!\n保存至: {save_path}"))
            
        except Exception as e:
            self.mod_log(f"下载失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {str(e)}")
        finally:
            # 重新启用下载按钮
            self.mod_window.after(0, lambda: self.download_mod_button.config(state=tk.NORMAL))

    def _download_dependencies(self, dependencies):
        """打开依赖项下载页面并让用户下载依赖项"""
        try:
            
            if messagebox.askyesno("提示",f"发现{len(dependencies)}个依赖项，{self.required_dep_counter}个重要。是否下载非必要依赖项？"):
                download_non_required_dep = True
            else:
                download_non_required_dep = False
                
            for dep in dependencies:
                if not download_non_required_dep:
                    if dep.get('dependency_type') != 'required':
                        continue  # 只下载必需的依赖项
                    
                project_id = dep.get('project_id')
                if not project_id:
                    continue

                # 在新线程中执行下载操作
                download_thread = threading.Thread(target=self._download_mod_thread, args=(project_id,))
                download_thread.daemon = True
                download_thread.start()
                download_thread.join()

        except Exception as e:
            self.mod_log(f"下载依赖项失败: {str(e)}", "ERROR")
            
    # 创建光影包下载窗口
    def create_shader_download_widgets(self):
        """创建光影包下载窗口"""
        self.shader_window = tk.Toplevel(self.root)
        self.shader_window.title("光影包下载")
        self.shader_window.geometry(f"800x600+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-600)/2)}")
        
        self.shader_window.resizable(False, False)
        
        # 光影包下载窗口主框架
        shader_main_frame = ttk.Frame(self.shader_window, padding="10")
        shader_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 光影包搜索框架
        search_frame = ttk.LabelFrame(shader_main_frame, text="搜索光影包", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索关键词:（暂不支持中文搜索）").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.shader_search_var = tk.StringVar()
        self.shader_search_entry = ttk.Entry(search_frame, textvariable=self.shader_search_var, width=40)
        self.shader_search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_shaders)
        search_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Minecraft版本选择
        ttk.Label(search_frame, text="Minecraft版本:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.shader_mc_version_var = tk.StringVar()
        self.shader_mc_version_combobox = ttk.Combobox(search_frame, textvariable=self.shader_mc_version_var, state="readonly", width=20)
        self.shader_mc_version_combobox.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 显示非正式版
        self.show_non_release_shader_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(search_frame, text="显示非正式版", variable=self.show_non_release_shader_var, 
                                           command=lambda: self.load_shader_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(shader_main_frame, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview来显示搜索结果
        columns = ('name', 'version', 'downloads')
        self.shaders_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题
        self.shaders_tree.heading('name', text='光影包名称')
        self.shaders_tree.heading('version', text='支持的最新版本')
        self.shaders_tree.heading('downloads', text='下载量')
        
        # 设置列宽
        self.shaders_tree.column('name', width=300)
        self.shaders_tree.column('version', width=50)
        self.shaders_tree.column('downloads', width=100)
        
        # 添加滚动条
        shaders_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.shaders_tree.yview)
        self.shaders_tree.configure(yscrollcommand=shaders_scrollbar.set)
        
        # 布局
        self.shaders_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        shaders_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载按钮
        self.download_shader_button = ttk.Button(shader_main_frame, text="下载选中的光影包", command=self.download_selected_shader, state=tk.DISABLED)
        self.download_shader_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        shader_log_frame = ttk.LabelFrame(shader_main_frame, text="日志", padding="10")
        shader_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.shader_log_text = scrolledtext.ScrolledText(shader_log_frame, height=6, state=tk.DISABLED)
        self.shader_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.shader_window.columnconfigure(0, weight=1)
        self.shader_window.rowconfigure(0, weight=1)
        shader_main_frame.columnconfigure(0, weight=1)
        shader_main_frame.rowconfigure(1, weight=1)
        shader_main_frame.rowconfigure(3, weight=1)
        search_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        shader_log_frame.columnconfigure(0, weight=1)
        shader_log_frame.rowconfigure(0, weight=1)
        
        # 加载Minecraft版本
        self.load_shader_version_list()
        
        # 绑定Treeview选择事件
        self.shaders_tree.bind('<<TreeviewSelect>>', self.on_shader_select)

        # 绑定回车键下载
        self.shader_window.bind("<Return>", lambda event: self.search_shaders())

    def load_shader_version_list(self):
        """加载Minecraft版本列表"""
        self.shader_log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_shader_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])

            self.version_list.insert(0, "全部")
                    
            # 更新下拉列表
            self.shader_mc_version_combobox['value'] = self.version_list

            try:
                self.shader_minecraft_version_combobox['value'] = self.version_list
                if self.version_list:
                    self.shader_minecraft_version_var.set(self.version_list[0])
            except:
                pass
            
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.shader_mc_version_var.set(self.version_list[0])
                    
            self.shader_log("版本列表加载完成", "INFO")
        except Exception as e:
            self.shader_log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")
            
    def shader_log(self, message, level):
        """在光影包日志区域显示消息"""
        print(f"[{time.asctime()}] [shaderpack/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [shaderpack/{level}] {message}\n")
        
        self.shader_log_text.config(state=tk.NORMAL)
        self.shader_log_text.insert(tk.END, message + "\n")
        self.shader_log_text.config(state=tk.DISABLED)
        self.shader_log_text.see(tk.END)
        
    def search_shaders(self):
        """搜索光影包"""
        # 禁用搜索按钮防止重复点击
        search_button = None
        for child in self.shader_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        
        if search_button:
            search_button.config(state=tk.DISABLED)
        
        # 在新线程中执行搜索操作
        search_thread = threading.Thread(target=self._search_shaders_thread)
        search_thread.daemon = True
        search_thread.start()
        
    def _search_shaders_thread(self):
        """在后台线程中搜索光影包"""
        try:
            # 获取搜索参数
            query = self.shader_search_var.get()
            mc_version = self.shader_mc_version_var.get()
            
            self.shader_log(f"正在搜索光影包: {query}", "INFO")
            
            # 构建查询参数
            params = {}
            if query:
                params['query'] = query
                
            # 构建facets参数
            facets = []
            if mc_version and mc_version != '全部':
                facets.append([f'versions:{mc_version}'])
            
            # 添加项目类型过滤（光影包）
            facets.append(['project_type:shader'])
                
            if facets:
                params['facets'] = json.dumps(facets)
                
            # 添加排序
            params['index'] = 'relevance'
            params['limit'] = 20
            
            # 构建URL
            base_url = 'https://api.modrinth.com/v2/search'
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            # 发送请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # 在主线程中更新UI
            self.shader_window.after(0, self._update_shaders_tree, data)
            
        except Exception as e:
            self.shader_log(f"搜索失败: {str(e)}", "ERROR")
            # 重新启用搜索按钮
            search_button = None
            for child in self.shader_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                            search_button = subchild
                            break
            if search_button:
                search_button.config(state=tk.NORMAL)
                
    def _update_shaders_tree(self, data):
        """更新光影包列表"""
        # 清空现有数据
        for item in self.shaders_tree.get_children():
            self.shaders_tree.delete(item)
            
        # 添加新数据
        for hit in data.get('hits', []):
            # 获取最新版本
            versions = hit.get('versions', [])
            latest_version = versions[-1] if versions else '未知'
            
            # 添加到Treeview
            self.shaders_tree.insert('', tk.END, values=(
                hit.get('title', '未知'),
                latest_version,
                hit.get('downloads', 0)
            ), tags=(hit.get('project_id', ''), hit.get('slug', '')))
            
        self.shader_log(f"搜索完成，找到 {data.get('total_hits', 0)} 个结果", "INFO")
        
        # 重新启用搜索按钮
        search_button = None
        for child in self.shader_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        if search_button:
            search_button.config(state=tk.NORMAL)
            
    def on_shader_select(self, event):
        """当选择光影包时"""
        selection = self.shaders_tree.selection()
        if selection:
            self.download_shader_button.config(state=tk.NORMAL)
        else:
            self.download_shader_button.config(state=tk.DISABLED)
            
    def download_selected_shader(self):
        """下载选中的光影包"""
        selection = self.shaders_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个光影包")
            return
            
        # 获取选中的光影包信息
        item = self.shaders_tree.item(selection[0])
        values = item['values']
        shader_name = values[0] if len(values) > 0 else '未知光影包'

        # 获取项目id
        tags = item['tags']
        project_id = tags[0] if len(tags) > 0 else None
        
        # 禁用下载按钮防止重复点击
        self.download_shader_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载操作
        download_thread = threading.Thread(target=self._download_shader_thread, args=(project_id,))
        download_thread.daemon = True
        download_thread.start()
        
    def select_shader_version(self, versions_data, project_name):
        """选择光影包版本"""
        self.versions_data = versions_data

        # 创建版本选择窗口
        version_window = tk.Toplevel(self.shader_window)
        version_window.title(f"选择 {project_name} 的版本")
        version_window.geometry(f"800x500+{int((self.shader_window.winfo_screenwidth()-800)/2)}+{int((self.shader_window.winfo_screenheight()-500)/2)}")
        
        version_window.grab_set()  # 模态窗口
        version_window.resizable(False, False)
        
        # 版本选择窗口主框架
        version_main_frame = ttk.Frame(version_window, padding="10")
        version_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(version_main_frame, text=f"选择 {project_name} 的版本", font=("微软雅黑", 16))
        title_label.pack(pady=(0, 10))

        # 顶部框架
        top_frame = ttk.Frame(version_main_frame, padding="0")
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 选择想要安装光影包的MC版本
        self.install_shader_version_var = tk.StringVar()
        self.install_shader_version_combobox = ttk.Combobox(top_frame, textvariable=self.install_shader_version_var, state="readonly", width=20)
        self.install_shader_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.install_shader_version_combobox['values'] = self.installed_versions
        self.install_shader_version_var.set(self.installed_versions[0])

        # 选择光影包的MC版本
        self.shader_minecraft_version_var = tk.StringVar()
        self.shader_minecraft_version_combobox = ttk.Combobox(top_frame, textvariable=self.shader_minecraft_version_var, state="readonly", width=20)
        self.shader_minecraft_version_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 10))
        self.shader_minecraft_version_combobox.bind("<<ComboboxSelected>>", self.load_shader_version)

        self.load_shader_version_list()

        # 版本列表框架
        version_list_frame = ttk.Frame(version_main_frame)
        version_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示版本列表
        version_columns = ('version', 'shader_filename', 'mc_version', 'type', 'date')
        self.version_tree = ttk.Treeview(version_list_frame, columns=version_columns, show='headings', height=17)
        
        # 定义列标题
        self.version_tree.heading('version', text='版本')
        self.version_tree.heading('shader_filename', text='文件名')
        self.version_tree.heading('mc_version', text='MC版本')
        self.version_tree.heading('type', text='类型')
        self.version_tree.heading('date', text='发布日期')
        
        # 设置列宽
        self.version_tree.column('version', width=70)
        self.version_tree.column('shader_filename', width=200)
        self.version_tree.column('mc_version', width=360)
        self.version_tree.column('type', width=50)
        self.version_tree.column('date', width=120)
        
        # 添加滚动条
        version_scrollbar = ttk.Scrollbar(version_list_frame, orient=tk.VERTICAL, command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=version_scrollbar.set)
        
        # 布局
        self.version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充版本数据
        for version in versions_data:
            if self.shader_minecraft_version_var.get() == "全部" or self.shader_minecraft_version_var.get() in version.get('game_versions', []):
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
        # 选择的版本变量
        selected_version = [None]  # 使用列表以便在内部函数中修改

        def on_version_select(event):
            """当选择版本时"""
            selection = self.version_tree.selection()
            if selection:
                item = self.version_tree.item(selection[0])
                tags = item['tags']
                if tags:
                    selected_version[0] = tags[0]
        
        def confirm_selection():
            """确认选择"""
            if selected_version[0] is None:
                messagebox.showwarning("警告", "请先选择一个版本")
                return
            version_window.destroy()
        
        # 绑定选择事件
        self.version_tree.bind('<<TreeviewSelect>>', on_version_select)
        
        # 按钮框架
        button_frame = ttk.Frame(version_main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认按钮
        confirm_button = ttk.Button(button_frame, text="确认", command=confirm_selection)
        confirm_button.pack(side=tk.RIGHT)

        def cancel():
            """取消"""
            selected_version[0] = 'not_selected'
            version_window.destroy()


        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))

        # 重新启用下载按钮
        self.download_shader_button.config(state=tk.NORMAL)
        
        # 等待窗口关闭
        version_window.wait_window()
        
        # 返回选择的版本ID
        return selected_version[0]
    
    def load_shader_version(self, event):
        """加载光影包版本"""
        self.version_tree.delete(*self.version_tree.get_children())

        # 填充版本数据
        for version in self.versions_data:
            if self.shader_minecraft_version_var.get() == "全部" or self.shader_minecraft_version_var.get() in version.get('game_versions', []):
                self.version_tree.insert('', tk.END, values=(
                    version.get('version_number', '未知'),
                    version.get('files', [])[0].get('filename', '未知'),
                    ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                    version.get('version_type', '未知'),
                    version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
                ), tags=(version.get('id'),))
        
    def _download_shader_thread(self, project_id):
        """在后台线程中下载光影包"""
        try:
            if not project_id:
                self.shader_log("无法获取项目ID", "WARN")
                return
                
            self.shader_log(f"正在获取光影包信息: {project_id}", "INFO")
            
            # 获取项目详细信息
            project_url = f'https://api.modrinth.com/v2/project/{project_id}'
            req = urllib.request.Request(project_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            project_data = json.loads(response.read().decode())
            
            # 获取项目版本信息
            versions_url = f'https://api.modrinth.com/v2/project/{project_id}/version'
            req = urllib.request.Request(versions_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            versions_data = json.loads(response.read().decode())
            
            # 选择版本
            if not versions_data:
                self.shader_log("未找到可用版本", "WARN")
                return
            
            # 在主线程中显示版本选择窗口
            selected_version_id = [None]
            def show_version_selector():
                selected_version_id[0] = self.select_shader_version(versions_data, project_data.get('title', '未知光影包'))
            
            show_version_selector()
            
            # 等待用户选择版本
            while selected_version_id[0] is None:
                import time
                time.sleep(0.1)
            
            if selected_version_id[0] == 'not_selected':
                self.shader_log("用户取消了版本选择", "WARN")
                return
                
            # 获取选中版本的详细信息
            selected_version = None
            for version in versions_data:
                if version.get('id') == selected_version_id[0]:
                    selected_version = version
                    break
            
            if not selected_version:
                self.shader_log("无法找到选中的版本", "WARN")
                return
                
            files = selected_version.get('files', [])
            
            if not files:
                self.shader_log("该版本没有可下载的文件", "WARN")
                return
                
            # 获取第一个文件（主文件）
            file_info = files[0]
            file_url = file_info.get('url')
            file_name = file_info.get('filename')
            
            if not file_url or not file_name:
                self.shader_log("文件信息不完整", "WARN")
                return
                
            # 确定保存路径
            self.init_isolation_state(self.install_shader_version_var.get())
            shaderpacks_dir = f"{self.isolation_dir}/shaderpacks"
            if not os.path.exists(shaderpacks_dir):
                os.makedirs(shaderpacks_dir)
                
            save_path = f"{shaderpacks_dir}/{file_name}"
            
            self.shader_log(f"正在下载: {file_name}", "INFO")
            
            # 下载文件
            def progress_callback(block_num, block_size, total_size):
                percent = min(100, int(block_num * block_size * 100 / total_size))
                self.shader_window.after(0, lambda: self.shader_log(f"下载进度: {percent}%", "INFO"))
                
            urllib.request.urlretrieve(file_url, save_path, reporthook=progress_callback)
            
            self.shader_log(f"光影包下载完成: {save_path}", "INFO")
            
            self.shader_window.after(0, lambda: messagebox.showinfo("成功", f"光影包下载完成!\n保存至: {save_path}"))
            
        except Exception as e:
            self.shader_log(f"下载失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {str(e)}")
        finally:
            # 重新启用下载按钮
            self.shader_window.after(0, lambda: self.download_shader_button.config(state=tk.NORMAL))

    # 创建整合包下载窗口
    def create_modpack_download_widgets(self):
        """创建整合包下载窗口"""
        self.modpack_window = tk.Toplevel(self.root)
        self.modpack_window.title("整合包下载")
        self.modpack_window.geometry(f"800x600+{int((self.root.winfo_screenwidth()-800)/2)}+{int((self.root.winfo_screenheight()-600)/2)}")
        
        self.modpack_window.resizable(False, False)

        # 创建选项卡
        notebook = ttk.Notebook(self.modpack_window)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 整合包下载窗口主框架
        modpack_main_frame = ttk.Frame(notebook, padding="10")
        modpack_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        notebook.add(modpack_main_frame, text="下载整合包")
        
        # 整合包搜索框架
        search_frame = ttk.LabelFrame(modpack_main_frame, text="搜索整合包", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索关键词:（暂不支持中文搜索）").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.modpack_search_var = tk.StringVar()
        self.modpack_search_entry = ttk.Entry(search_frame, textvariable=self.modpack_search_var, width=40)
        self.modpack_search_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_modpacks)
        search_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 10))
        
        # Minecraft版本选择
        ttk.Label(search_frame, text="Minecraft版本:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.modpack_mc_version_var = tk.StringVar()
        self.modpack_mc_version_combobox = ttk.Combobox(search_frame, textvariable=self.modpack_mc_version_var, state="readonly", width=20)
        self.modpack_mc_version_combobox.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 显示非正式版
        self.show_non_release_modpack_var = tk.BooleanVar()
        show_non_release_checkbox = ttk.Checkbutton(search_frame, text="显示非正式版", variable=self.show_non_release_modpack_var, 
                                           command=lambda: self.load_modpack_version_list())
        show_non_release_checkbox.grid(row=3, column=2, pady=(0, 5))
        
        # 搜索结果框架
        results_frame = ttk.LabelFrame(modpack_main_frame, text="搜索结果", padding="10")
        results_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建Treeview来显示搜索结果
        columns = ('name', 'version', 'downloads')
        self.modpacks_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        # 定义列标题
        self.modpacks_tree.heading('name', text='整合包名称')
        self.modpacks_tree.heading('version', text='支持的最新版本')
        self.modpacks_tree.heading('downloads', text='下载量')
        
        # 设置列宽
        self.modpacks_tree.column('name', width=300)
        self.modpacks_tree.column('version', width=50)
        self.modpacks_tree.column('downloads', width=100)
        
        # 添加滚动条
        modpacks_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.modpacks_tree.yview)
        self.modpacks_tree.configure(yscrollcommand=modpacks_scrollbar.set)
        
        # 布局
        self.modpacks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        modpacks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 下载按钮
        self.download_modpack_button = ttk.Button(modpack_main_frame, text="下载选中的整合包", command=self.download_selected_modpack, state=tk.DISABLED)
        self.download_modpack_button.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 日志显示区域
        modpack_log_frame = ttk.LabelFrame(modpack_main_frame, text="日志", padding="10")
        modpack_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.modpack_log_text = scrolledtext.ScrolledText(modpack_log_frame, height=6, state=tk.DISABLED)
        self.modpack_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.modpack_window.columnconfigure(0, weight=1)
        self.modpack_window.rowconfigure(0, weight=1)
        modpack_main_frame.columnconfigure(0, weight=1)
        modpack_main_frame.rowconfigure(1, weight=1)
        modpack_main_frame.rowconfigure(3, weight=1)
        search_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        modpack_log_frame.columnconfigure(0, weight=1)
        modpack_log_frame.rowconfigure(0, weight=1)

        # 安装本地整合包
        modpack_install_frame = ttk.Frame(notebook, padding="10")
        modpack_install_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        notebook.add(modpack_install_frame, text="安装本地整合包")

        ttk.Label(modpack_install_frame, text="安装本地整合包", font=("微软雅黑", 18)).grid(row=0, column=0, columnspan=2)

        modpack_choose_frame = ttk.LabelFrame(modpack_install_frame, text="本地整合包文件", padding="10")
        modpack_choose_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(modpack_choose_frame, text="选择本地Modrinth(.mrpack)格式整合包文件:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.modpack_var = tk.StringVar()
        self.modpack_entry = ttk.Entry(modpack_choose_frame, textvariable=self.modpack_var, width=30)
        self.modpack_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.modpack_button = ttk.Button(modpack_choose_frame, text="浏览", command=self.browse_offline_modpack_path)
        self.modpack_button.grid(row=1, column=2, padx=(5, 0), pady=(0, 5))

        self.modpack_install_button = ttk.Button(modpack_install_frame, text="安装整合包", command=lambda: self.install_modpack(self.modpack_var.get()))
        self.modpack_install_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # 日志显示区域
        modpack_install_log_frame = ttk.LabelFrame(modpack_install_frame, text="日志", padding="10")
        modpack_install_log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.modpack_install_log_text = scrolledtext.ScrolledText(modpack_install_log_frame, height=10, state=tk.DISABLED)
        self.modpack_install_log_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        modpack_install_frame.columnconfigure(0, weight=2)
        modpack_install_frame.columnconfigure(1, weight=2)
        modpack_choose_frame.columnconfigure(0, weight=1)
        modpack_choose_frame.columnconfigure(1, weight=1)
        modpack_install_log_frame.columnconfigure(0, weight=1)
        
        # 加载Minecraft版本
        self.load_modpack_version_list()
        
        # 绑定Treeview选择事件
        self.modpacks_tree.bind('<<TreeviewSelect>>', self.on_modpack_select)

        # 绑定回车键下载
        self.modpack_window.bind("<Return>", lambda event: self.search_modpacks())

    def browse_offline_modpack_path(self):
        """浏览本地整合包路径"""
        offline_modpack = filedialog.askopenfilename(
            title="选择Modrinth整合包文件",
            filetypes=[("Modrinth Modpack", "*.mrpack"), ("All Files", "*.*")]
        )
        if offline_modpack:
            self.modpack_var.set(offline_modpack)

    def load_modpack_version_list(self):
        """加载Minecraft版本列表"""
        self.modpack_log("正在获取版本列表...", "INFO")
        try:
            # 获取所有可用版本
            versions = minecraft_launcher_lib.utils.get_version_list()
            if self.show_non_release_modpack_var.get():
                self.version_list = [version['id'] for version in versions]
            else:
                self.version_list = []
                for version in versions:
                    if version['type'] == 'release':
                        self.version_list.append(version['id'])

            self.version_list.insert(0, "全部")
                    
            # 更新下拉列表
            self.modpack_mc_version_combobox['value'] = self.version_list
            
            # 设置默认选中版本为最新版本
            if self.version_list:
                self.modpack_mc_version_var.set(self.version_list[0])
                    
            self.modpack_log("版本列表加载完成", "INFO")
        except Exception as e:
            self.modpack_log(f"加载版本列表失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"加载版本列表失败: {str(e)}")
            
    def modpack_log(self, message, level):
        """在整合包日志区域显示消息"""
        print(f"[{time.asctime()}] [modpack/{level}] {message}")
        with open(f"logs/log_{self.start_time}.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] [modpack/{level}] {message}\n")
        
        self.modpack_log_text.config(state=tk.NORMAL)
        self.modpack_log_text.insert(tk.END, message + "\n")
        self.modpack_log_text.config(state=tk.DISABLED)
        self.modpack_log_text.see(tk.END)
        self.modpack_install_log_text.config(state=tk.NORMAL)
        self.modpack_install_log_text.insert(tk.END, message + "\n")
        self.modpack_install_log_text.config(state=tk.DISABLED)
        self.modpack_install_log_text.see(tk.END)
        
    def search_modpacks(self):
        """搜索整合包"""
        # 禁用搜索按钮防止重复点击
        search_button = None
        for child in self.modpack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        
        if search_button:
            search_button.config(state=tk.DISABLED)
        
        # 在新线程中执行搜索操作
        search_thread = threading.Thread(target=self._search_modpacks_thread)
        search_thread.daemon = True
        search_thread.start()
        
    def _search_modpacks_thread(self):
        """在后台线程中搜索整合包"""
        try:
            # 获取搜索参数
            query = self.modpack_search_var.get()
            mc_version = self.modpack_mc_version_var.get()
            
            self.modpack_log(f"正在搜索整合包: {query}", "INFO")
            
            # 构建查询参数
            params = {}
            if query:
                params['query'] = query
                
            # 构建facets参数
            facets = []
            if mc_version and mc_version != '全部':
                facets.append([f'versions:{mc_version}'])
            
            # 添加项目类型过滤（整合包）
            facets.append(['project_type:modpack'])
                
            if facets:
                params['facets'] = json.dumps(facets)
                
            # 添加排序
            params['index'] = 'relevance'
            params['limit'] = 20
            
            # 构建URL
            base_url = 'https://api.modrinth.com/v2/search'
            url = base_url + '?' + urllib.parse.urlencode(params)
            
            # 发送请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # 在主线程中更新UI
            self.modpack_window.after(0, self._update_modpacks_tree, data)
            
        except Exception as e:
            self.modpack_log(f"搜索失败: {str(e)}", "ERROR")
            # 重新启用搜索按钮
            search_button = None
            for child in self.modpack_window.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                            search_button = subchild
                            break
            if search_button:
                search_button.config(state=tk.NORMAL)
                
    def _update_modpacks_tree(self, data):
        """更新整合包列表"""
        # 清空现有数据
        for item in self.modpacks_tree.get_children():
            self.modpacks_tree.delete(item)
            
        # 添加新数据
        for hit in data.get('hits', []):
            # 获取最新版本
            versions = hit.get('versions', [])
            latest_version = versions[-1] if versions else '未知'
            
            # 添加到Treeview
            self.modpacks_tree.insert('', tk.END, values=(
                hit.get('title', '未知'),
                latest_version,
                hit.get('downloads', 0)
            ), tags=(hit.get('project_id', ''), hit.get('slug', '')))
            
        self.modpack_log(f"搜索完成，找到 {data.get('total_hits', 0)} 个结果", "INFO")
        
        # 重新启用搜索按钮
        search_button = None
        for child in self.modpack_window.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Button) and subchild.cget('text') == '搜索':
                        search_button = subchild
                        break
        if search_button:
            search_button.config(state=tk.NORMAL)
            
    def on_modpack_select(self, event):
        """当选择整合包时"""
        selection = self.modpacks_tree.selection()
        if selection:
            self.download_modpack_button.config(state=tk.NORMAL)
        else:
            self.download_modpack_button.config(state=tk.DISABLED)
            
    def download_selected_modpack(self):
        """下载选中的整合包"""
        selection = self.modpacks_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个整合包")
            return
            
        # 获取选中的整合包信息
        item = self.modpacks_tree.item(selection[0])
        values = item['values']
        modpack_name = values[0] if len(values) > 0 else '未知整合包'

        # 获取项目id
        tags = item['tags']
        project_id = tags[0] if len(tags) > 0 else None
        
        # 禁用下载按钮防止重复点击
        self.download_modpack_button.config(state=tk.DISABLED)

        # 询问版本名称
        self.version_name = ''
        while not self.version_name:
            self.version_name = tk.simpledialog.askstring("命名版本", "请为安装的整合包命名", initialvalue=modpack_name)
        import re
        if re.search(r'[//:*?"<>|]', self.version_name):
            messagebox.showwarning("警告", "非法的版本名称")
            self.download_modpack_button.config(state=tk.NORMAL)
            return
        
        # 在新线程中执行下载操作
        download_thread = threading.Thread(target=self._download_modpack_thread, args=(project_id,))
        download_thread.daemon = True
        download_thread.start()
        
    def select_modpack_version(self, versions_data, project_name):
        """选择整合包版本"""
        # 创建版本选择窗口
        version_window = tk.Toplevel(self.modpack_window)
        version_window.title(f"选择 {project_name} 的版本")
        version_window.geometry(f"800x500+{int((self.modpack_window.winfo_screenwidth()-800)/2)}+{int((self.modpack_window.winfo_screenheight()-500)/2)}")
        
        version_window.grab_set()  # 模态窗口
        version_window.resizable(False, False)
        
        # 版本选择窗口主框架
        version_main_frame = ttk.Frame(version_window, padding="10")
        version_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(version_main_frame, text=f"选择 {project_name} 的版本", font=("微软雅黑", 16))
        title_label.pack(pady=(0, 10))

        # 版本列表框架
        version_list_frame = ttk.Frame(version_main_frame)
        version_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示版本列表
        version_columns = ('version', 'modpack_filename', 'mc_version', 'type', 'date')
        version_tree = ttk.Treeview(version_list_frame, columns=version_columns, show='headings', height=17)
        
        # 定义列标题
        version_tree.heading('version', text='版本')
        version_tree.heading('modpack_filename', text='文件名')
        version_tree.heading('mc_version', text='MC版本')
        version_tree.heading('type', text='类型')
        version_tree.heading('date', text='发布日期')
        
        # 设置列宽
        version_tree.column('version', width=70)
        version_tree.column('modpack_filename', width=200)
        version_tree.column('mc_version', width=360)
        version_tree.column('type', width=50)
        version_tree.column('date', width=120)
        
        # 添加滚动条
        version_scrollbar = ttk.Scrollbar(version_list_frame, orient=tk.VERTICAL, command=version_tree.yview)
        version_tree.configure(yscrollcommand=version_scrollbar.set)
        
        # 布局
        version_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充版本数据
        for version in versions_data:
            version_tree.insert('', tk.END, values=(
                version.get('version_number', '未知'),
                version.get('files', [])[0].get('filename', '未知'),
                ', '.join(version.get('game_versions', [])) if version.get('game_versions') else '未知',
                version.get('version_type', '未知'),
                version.get('date_published', '未知')[:10] if version.get('date_published') else '未知'
            ), tags=(version.get('id'),))
        
        # 选择的版本变量
        selected_version = [None]  # 使用列表以便在内部函数中修改

        def on_version_select(event):
            """当选择版本时"""
            selection = version_tree.selection()
            if selection:
                item = version_tree.item(selection[0])
                tags = item['tags']
                if tags:
                    selected_version[0] = tags[0]
        
        def confirm_selection(): 
            """确认选择"""
            if selected_version[0] is None:
                messagebox.showwarning("警告", "请先选择一个版本")
                return
            version_window.destroy()
        
        # 绑定选择事件
        version_tree.bind('<<TreeviewSelect>>', on_version_select)
        
        # 按钮框架
        button_frame = ttk.Frame(version_main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认按钮
        confirm_button = ttk.Button(button_frame, text="确认", command=confirm_selection)
        confirm_button.pack(side=tk.RIGHT)

        def cancel():
            """取消"""
            selected_version[0] = 'not_selected'
            version_window.destroy()

        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 5))

        # 重新启用下载按钮
        self.download_modpack_button.config(state=tk.NORMAL)
        
        # 等待窗口关闭
        version_window.wait_window()
        
        # 返回选择的版本ID
        return selected_version[0]
        
    def _download_modpack_thread(self, project_id):
        """在后台线程中下载整合包"""
        try:
            if not project_id:
                self.modpack_log("无法获取项目ID", "WARN")
                return
                
            self.modpack_log(f"正在获取整合包信息: {project_id}", "INFO")
            
            import zipfile
            import tempfile
            import shutil
            
            # 获取项目详细信息
            project_url = f'https://api.modrinth.com/v2/project/{project_id}'
            req = urllib.request.Request(project_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            project_data = json.loads(response.read().decode())
            
            # 获取项目版本信息
            versions_url = f'https://api.modrinth.com/v2/project/{project_id}/version'
            req = urllib.request.Request(versions_url)
            req.add_header('User-Agent', 'PMCL/1.1.1 (Python Minecraft Launcher)')
            response = urllib.request.urlopen(req)
            versions_data = json.loads(response.read().decode())
            
            # 选择版本
            if not versions_data:
                self.modpack_log("未找到可用版本", "WARN")
                return
            
            # 在主线程中显示版本选择窗口
            selected_version_id = [None]
            def show_version_selector():
                selected_version_id[0] = self.select_modpack_version(versions_data, project_data.get('title', '未知整合包'))
            
            show_version_selector()
            
            # 等待用户选择版本
            while selected_version_id[0] is None:
                import time
                time.sleep(0.1)
            
            if selected_version_id[0] == 'not_selected':
                self.modpack_log("用户取消了版本选择", "WARN")
                return
                
            # 获取选中版本的详细信息
            selected_version = None
            for version in versions_data:
                if version.get('id') == selected_version_id[0]:
                    selected_version = version
                    break
            
            if not selected_version:
                self.modpack_log("无法找到选中的版本", "WARN")
                return
                
            files = selected_version.get('files', [])
            
            if not files:
                self.modpack_log("该版本没有可下载的文件", "WARN")
                return
                
            # 获取第一个文件（主文件）
            file_info = files[0]
            file_url = file_info.get('url')
            file_name = file_info.get('filename')
            
            if not file_url or not file_name:
                self.modpack_log("文件信息不完整", "WARN")
                return
                
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            modpack_zip_path = os.path.join(temp_dir, file_name)
            
            self.modpack_log(f"正在下载整合包: {file_name}", "INFO")
            
            # 下载整合包文件
            def progress_callback(block_num, block_size, total_size):
                percent = min(100, int(block_num * block_size * 100 / total_size))
                self.modpack_window.after(0, lambda: self.modpack_log(f"下载进度: {percent}%", "INFO"))
                
            urllib.request.urlretrieve(file_url, modpack_zip_path, reporthook=progress_callback)
            
            self.modpack_log("整合包下载完成，正在解压...", "INFO")
            
            # 解压整合包
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(modpack_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.modpack_log("整合包解压完成，正在处理...", "INFO")
            
            # 读取modrinth.index.json文件
            index_file = os.path.join(extract_dir, 'modrinth.index.json')
            if not os.path.exists(index_file):
                self.modpack_log("错误: 未找到modrinth.index.json文件", "WARN")
                shutil.rmtree(temp_dir)
                return
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 获取游戏版本和加载器信息
            game_version = index_data.get('dependencies', {}).get('minecraft', '未知')
            modloader = None
            if 'forge' in index_data.get('dependencies', {}):
                modloader = 'forge'
            elif 'fabric-loader' in index_data.get('dependencies', {}):
                modloader = 'fabric'
            elif 'quilt-loader' in index_data.get('dependencies', {}):
                modloader = 'quilt'
            
            self.modpack_log(f"整合包信息: Minecraft {game_version}, 加载器: {modloader if modloader else '原版'}", "INFO")
            
            # 检查是否需要安装游戏版本
            current_max = 0

            def set_status(status):
                self.modpack_log(status.replace("Download", "下载").replace("Running", "运行").replace("Install java runtime", "安装Java环境").replace("Installation complete", "安装完成"), "INFO")

            def set_progress(progress):
                if current_max:
                    self.modpack_log(f"进度：{progress}/{current_max} {progress / current_max * 100:.1f}%", "INFO")
            
            def set_max(new_max):
                global current_max
                current_max = new_max

            callback = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": set_max
            }
            
            if not modloader:
                if not os.path.exists(f"{self.minecraft_directory}/versions/{game_version}"):
                    self.modpack_log(f"需要安装Minecraft {game_version}...", "INFO")
                    try:
                        minecraft_launcher_lib.install.install_minecraft_version(game_version, self.minecraft_directory, callback=callback)
                        self.modpack_log(f"Minecraft {game_version} 安装完成", "INFO")
                    except Exception as e:
                        self.modpack_log(f"安装Minecraft版本失败: {str(e)}", "ERROR")
            
            # 检查是否需要安装模组加载器
            if modloader == 'forge':
                forge_version = index_data.get('dependencies', {}).get('forge')
                if forge_version:
                    for version in minecraft_launcher_lib.forge.list_forge_versions():
                        if game_version in version and forge_version in version:
                            forge_id = version
                            break
                    
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{forge_id}"):
                        self.modpack_log(f"需要安装Forge {forge_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.forge.install_forge_version(forge_id, self.minecraft_directory, callback=callback)
                            self.modpack_log(f"Forge {forge_version} 安装完成", "INFO")
                            self.load_installed_versions()
                            for version in self.launch_version_combobox['values']:
                                if (game_version in version) and ('forge' in version):
                                    installed_version = ''.join(version)
                        except Exception as e:
                            self.modpack_log(f"安装Forge失败: {str(e)}", "ERROR")
            elif modloader == 'fabric':
                fabric_loader_version = index_data.get('dependencies', {}).get('fabric-loader')
                if fabric_loader_version:
                    fabric_id = f"fabric-loader-{fabric_loader_version}-{game_version}"
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{fabric_id}"):
                        self.modpack_log(f"需要安装Fabric Loader {fabric_loader_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.fabric.install_fabric(game_version, self.minecraft_directory, loader_version=fabric_loader_version, callback=callback)
                            self.modpack_log(f"Fabric Loader {fabric_loader_version} 安装完成", "INFO")
                        except Exception as e:
                            self.modpack_log(f"安装Fabric失败: {str(e)}", "ERROR")
            
            elif modloader == 'quilt':
                quilt_loader_version = index_data.get('dependencies', {}).get('Quilt-loader')
                if quilt_loader_version:
                    quilt_id = f"quilt-loader-{quilt_loader_version}-{game_version}"
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{quilt_id}"):
                        self.modpack_log(f"需要安装Quilt Loader {quilt_loader_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.quilt.install_quilt(game_version, self.minecraft_directory, loader_version=quilt_loader_version, callback=callback)
                            self.modpack_log(f"Quilt Loader {quilt_loader_version} 安装完成", "INFO")
                        except Exception as e:
                            self.modpack_log(f"安装Quilt失败: {str(e)}", "ERROR")

            if messagebox.askyesno("提示", "是否为安装的整合包启用版本隔离？"):
                if not modloader:
                    isolation_dir = os.path.join(self.minecraft_directory, 'versions', game_version)
                else:
                    isolation_dir = os.path.join(self.minecraft_directory, 'versions', (installed_version if modloader == 'forge' else (fabric_id if modloader == 'fabric' else quilt_id)))
                os.makedirs(os.path.join(isolation_dir, 'config'), exist_ok=True)
            else:
                if not modloader:
                    isolation_dir = ''.join(self.minecraft_directory)
                else:
                    isolation_dir = ''.join(self.minecraft_directory)
            
            # 下载依赖文件（模组、资源包等）
            self.modpack_log("正在下载整合包依赖文件...", "INFO")
            
            for file_info in index_data.get('files', []):
                file_path = file_info.get('path', '')
                downloads = file_info.get('downloads', [])
                
                if downloads:
                    download_url = downloads[0]
                    
                    # 确定保存路径
                    save_path = os.path.join(isolation_dir, file_path)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # 下载文件
                    try:
                        urllib.request.urlretrieve(download_url, save_path)
                        self.modpack_log(f"已下载: {file_path}", "INFO")
                    except Exception as e:
                        self.modpack_log(f"下载 {file_path} 失败: {str(e)}", "ERROR")
            
            # 复制overrides文件夹（如果有）
            overrides_dir = os.path.join(extract_dir, 'overrides')
            if os.path.exists(overrides_dir):
                self.modpack_log("正在复制overrides文件...", "INFO")
                for root, dirs, files in os.walk(overrides_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, overrides_dir)
                        dst_path = os.path.join(isolation_dir, rel_path)
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)

            if not modloader:
                self.rename_version(game_version, self.version_name)
            else:
                self.rename_version(installed_version if modloader == 'forge' else (fabric_id if modloader == 'fabric' else quilt_id), self.version_name)
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            
            self.modpack_log("整合包安装完成!", "INFO")
            self.modpack_window.after(0, lambda: messagebox.showinfo("成功", "整合包安装完成!"))

            # 重新加载已安装版本列表
            self.load_installed_versions()
            
        except Exception as e:
            self.modpack_log(f"整合包安装失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"整合包安装失败: {str(e)}")
        finally:
            # 重新启用下载按钮
            self.modpack_window.after(0, lambda: self.download_modpack_button.config(state=tk.NORMAL))

    def install_modpack(self, modpack_path):
        """安装本地整合包"""
        if os.path.splitext(modpack_path)[-1].lower() != '.mrpack':
            messagebox.showwarning("警告", "请选择一个有效的Modrinth整合包(.mrpack)文件")
            return
        self.version_name = ''
        while not self.version_name:
            self.version_name = tk.simpledialog.askstring("命名版本", "请为安装的整合包命名", initialvalue=os.path.splitext(os.path.basename(modpack_path))[0])
        import re
        if re.search(r'[//:*?"<>|]', self.version_name):
            messagebox.showwarning("警告", "非法的版本名称")
            return
        install_modpack_thread = threading.Thread(target=self._install_modpack_thread, args=(modpack_path,))
        install_modpack_thread.daemon = True
        install_modpack_thread.start()

    def _install_modpack_thread(self, modpack_path):
        """在后台线程中安装本地整合包"""
        try:
            if not modpack_path:
                self.modpack_log("请指定整合包文件！", "WARN")
                messagebox.showwarning("警告", "请指定整合包文件！")
                return
            
            import tempfile
            import zipfile
            import shutil

            # 禁用按钮防止重复安装
            self.modpack_install_button.config(state=tk.DISABLED)

            # 解压整合包
            extract_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(modpack_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.modpack_log("整合包解压完成，正在处理...", "INFO")
            
            # 读取modrinth.index.json文件
            index_file = os.path.join(extract_dir, 'modrinth.index.json')
            if not os.path.exists(index_file):
                self.modpack_log("错误: 未找到modrinth.index.json文件", "WARN")
                shutil.rmtree(extract_dir)
                return
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 获取游戏版本和加载器信息
            game_version = index_data.get('dependencies', {}).get('minecraft', '未知')
            modloader = None
            if 'forge' in index_data.get('dependencies', {}):
                modloader = 'forge'
            elif 'fabric-loader' in index_data.get('dependencies', {}):
                modloader = 'fabric'
            elif 'quilt-loader' in index_data.get('dependencies', {}):
                modloader = 'quilt'
            
            self.modpack_log(f"整合包信息: Minecraft {game_version}, 加载器: {modloader if modloader else '原版'}", "INFO")
            
            # 检查是否需要安装游戏版本
            current_max = 0

            def set_status(status):
                self.modpack_log(status.replace("Download", "下载").replace("Running", "运行").replace("Install java runtime", "安装Java环境").replace("Installation complete", "安装完成"), "INFO")

            def set_progress(progress):
                if current_max:
                    self.modpack_log(f"进度：{progress}/{current_max} {progress / current_max * 100:.1f}%", "INFO")
            
            def set_max(new_max):
                global current_max
                current_max = new_max

            callback = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": set_max
            }

            if not modloader:
                if not os.path.exists(f"{self.minecraft_directory}/versions/{game_version}"):
                    self.modpack_log(f"需要安装Minecraft {game_version}...", "INFO")
                    try:
                        minecraft_launcher_lib.install.install_minecraft_version(game_version, self.minecraft_directory, callback=callback)
                        self.modpack_log(f"Minecraft {game_version} 安装完成", "INFO")
                    except Exception as e:
                        self.modpack_log(f"安装Minecraft版本失败: {str(e)}", "ERROR")
            
            # 检查是否需要安装模组加载器
            if modloader == 'forge':
                forge_version = index_data.get('dependencies', {}).get('forge')
                if forge_version:
                    for version in minecraft_launcher_lib.forge.list_forge_versions():
                        if game_version in version and forge_version in version:
                            forge_id = version
                            break
                    
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{forge_id}"):
                        self.modpack_log(f"需要安装Forge {forge_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.forge.install_forge_version(forge_id, self.minecraft_directory, callback=callback)
                            self.modpack_log(f"Forge {forge_version} 安装完成", "INFO")
                            self.load_installed_versions()
                            for version in self.launch_version_combobox['values']:
                                if (game_version in version) and ('forge' in version):
                                    installed_version = ''.join(version)
                        except Exception as e:
                            self.modpack_log(f"安装Forge失败: {str(e)}", "ERROR")
            elif modloader == 'fabric':
                fabric_loader_version = index_data.get('dependencies', {}).get('fabric-loader')
                if fabric_loader_version:
                    fabric_id = f"fabric-loader-{fabric_loader_version}-{game_version}"
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{fabric_id}"):
                        self.modpack_log(f"需要安装Fabric Loader {fabric_loader_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.fabric.install_fabric(game_version, self.minecraft_directory, loader_version=fabric_loader_version, callback=callback)
                            self.modpack_log(f"Fabric Loader {fabric_loader_version} 安装完成", "INFO")
                        except Exception as e:
                            self.modpack_log(f"安装Fabric失败: {str(e)}", "ERROR")
            
            elif modloader == 'quilt':
                quilt_loader_version = index_data.get('dependencies', {}).get('quilt-loader')
                if quilt_loader_version:
                    quilt_id = f"quilt-loader-{quilt_loader_version}-{game_version}"
                    if not os.path.exists(f"{self.minecraft_directory}/versions/{quilt_id}"):
                        self.modpack_log(f"需要安装Quilt Loader {quilt_loader_version}...", "INFO")
                        try:
                            minecraft_launcher_lib.quilt.install_quilt(game_version, self.minecraft_directory, loader_version=quilt_loader_version, callback=callback)
                            self.modpack_log(f"Quilt Loader {quilt_loader_version} 安装完成", "INFO")
                        except Exception as e:
                            self.modpack_log(f"安装Quilt失败: {str(e)}", "ERROR")
            
            # 下载依赖文件（模组、资源包等）
            self.modpack_log("正在下载整合包依赖文件...", "INFO")

            if self.modpack_window.after(0, messagebox.askyesno("提示", "是否为安装的整合包启用版本隔离？")):
                if not modloader:
                    isolation_dir = os.path.join(self.minecraft_directory, 'versions', game_version)
                else:
                    isolation_dir = os.path.join(self.minecraft_directory, 'versions', installed_version if modloader == 'forge' else (fabric_id if modloader == 'fabric' else quilt_id))
                os.makedirs(os.path.join(isolation_dir, 'config'), exist_ok=True)
            else:
                if not modloader:
                    isolation_dir = ''.join(self.minecraft_directory)
                else:
                    isolation_dir = ''.join(self.minecraft_directory)

            for file_info in index_data.get('files', []):
                file_path = file_info.get('path', '')
                downloads = file_info.get('downloads', [])
                
                if downloads:
                    download_url = downloads[0]
                    
                    # 确定保存路径                    
                    save_path = os.path.join(isolation_dir, file_path)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # 下载文件
                    try:
                        urllib.request.urlretrieve(download_url, save_path)                        
                        self.modpack_log(f"已下载: {file_path}", "INFO")
                    except Exception as e:
                        self.modpack_log(f"下载 {file_path} 失败: {str(e)}", "ERROR")
            
            # 复制overrides文件夹（如果有）
            overrides_dir = os.path.join(extract_dir, 'overrides')
            if os.path.exists(overrides_dir):
                self.modpack_log("正在复制overrides文件...", "INFO")
                for root, dirs, files in os.walk(overrides_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, overrides_dir)
                        dst_path = os.path.join(isolation_dir, rel_path)
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
            
            if not modloader:
                self.rename_version(game_version, self.version_name)
            else:
                self.rename_version(installed_version if modloader == 'forge' else (fabric_id if modloader == 'fabric' else quilt_id), self.version_name)

            # 清理临时文件
            shutil.rmtree(extract_dir)
            
            self.modpack_log("整合包安装完成!", "INFO")
            self.modpack_window.after(0, lambda: messagebox.showinfo("成功", "整合包安装完成!"))

            # 重新加载已安装版本列表
            self.load_installed_versions()
            
        except Exception as e:
            self.modpack_log(f"整合包安装失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"整合包安装失败: {str(e)}")
        finally:
            # 重新启用安装按钮
            self.modpack_install_button.config(state=tk.NORMAL)

    def install_update(self):
        """安装更新"""
        try:
            # 创建更新批处理文件
            with open('update.bat', 'w') as update:
                update.write('''
@echo off
setlocal
                            
echo 正在更新启动器

:loop
tasklist /fi "imagename eq PMCL.exe" /fo csv 2>nul | find /i "PMCL.exe" >nul
if not errorlevel 1 (
    echo 等待启动器关闭. . .
    timeout /t 1 /nobreak >nul
    goto loop
)

del /q PMCL*.exe
move /y update.exe PMCL.exe >nul

start PMCL.exe

del /q update.bat >nul
''')
            
            # 在主线程中退出程序并启动更新批处理
            self.root.after(100, self._execute_update)
        except Exception as e:
            messagebox.showerror("错误", f"安装更新失败：{e}")
            
    def _execute_update(self):
        """在主线程中执行更新"""
        try:
            # 启动更新批处理
            os.startfile('update.bat')
            
            # 退出当前程序
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("错误", f"执行更新失败：{e}")

def main():
    root = tk.Tk()
    app = MinecraftLauncherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
