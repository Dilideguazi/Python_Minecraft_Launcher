import sys
import os
import shutil
import threading
import psutil
import subprocess
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

try:

    def resource_path(relative_path):
        """获取资源的绝对路径"""
        try:
            base_path = sys._MEIPASS
        except:
            base_path = os.path.abspath('')
        return os.path.join(base_path, relative_path)

    start_time = int(time.time())

    # 显示图片
    root = tk.Tk()
    root.overrideredirect(True)
    root.config(cursor='watch')
    root.grab_set()

    # 加载图片
    image = Image.open(resource_path('updater.png'))
    photo = ImageTk.PhotoImage(image)

    # 创建标签显示图片
    label = tk.Label(root, image=photo)
    label.pack()
        
    # 获取屏幕尺寸
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
        
    # 获取图片尺寸
    img_width = image.width
    img_height = image.height
        
    # 计算居中位置
    x = (screen_width - img_width) // 2
    y = (screen_height - img_height) // 2
        
    # 设置窗口位置和大小
    root.geometry(f"{img_width}x{img_height}+{x}+{y}")

    # 设置定时关闭
    root.after(10000, root.destroy)

    def update():
        """执行更新"""
        try:
            # 遍历进程名称和pid
            while True:
                if not any('PMCL' in process.info['name'] for process in psutil.process_iter(('name',))):
                    break
                for process in psutil.process_iter(('name', 'pid')):
                    if 'PMCL' in process.info['name']:
                        if int(time.time()) - start_time > 5:
                            subprocess.run(('taskkill', '/f', '/pid', str(process.info['pid'])))
                            break
                time.sleep(0.1)

            exe_name = None
            # 操作文件
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if 'PMCL' in file and 'exe' in file:
                        exe_name = file
            if exe_name:
                if os.path.exists(exe_name):
                    os.remove(exe_name)
            else:
                exe_name = 'PMCL.exe'
            shutil.move('update.exe', exe_name)
            os.startfile(exe_name)
        except Exception as e:
            messagebox.showerror("错误", f"执行更新失败: {e}")

    update_thread = threading.Thread(target=update)
    update_thread.daemon = True
    update_thread.start()

    root.mainloop()

except Exception as e:
    messagebox.showerror("错误", f"执行更新失败: {e}")
