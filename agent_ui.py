import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from GUIAgent import DoubaoUITarsGUI
import os

class GoalExecutorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("目标执行器")
        self.root.geometry("800x600")
        
        self.agent = None
        self.is_running = False
        self.current_file = None
        self.goals = []
        self.current_goal_index = 0
        
        self.setup_gui()
        self.initialize_agent()
    
    def setup_gui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # API密钥输入
        ttk.Label(main_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="9dc1016e-8562-42e4-addb-4bdf30d8152c")
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, width=50)
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="目标文件", padding="5")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="选择TXT文件", command=self.select_file).grid(row=0, column=0, padx=5)
        self.file_path_var = tk.StringVar(value="未选择文件")
        ttk.Label(file_frame, textvariable=self.file_path_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="开始执行", command=self.start_execution)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="暂停", command=self.pause_execution, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 进度显示
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT)
        self.progress_var = tk.StringVar(value="0/0")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    def initialize_agent(self):
        """初始化代理"""
        try:
            api_key = self.api_key_var.get().strip()
            if api_key:
                self.agent = DoubaoUITarsGUI(api_key=api_key)
                self.log("代理初始化成功")
            else:
                self.log("请输入有效的API密钥")
        except Exception as e:
            self.log(f"代理初始化失败: {e}")
    
    def select_file(self):
        """选择TXT文件"""
        filename = filedialog.askopenfilename(
            title="选择目标文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            self.current_file = filename
            self.file_path_var.set(os.path.basename(filename))
            self.load_goals(filename)
    
    def load_goals(self, filename):
        """从文件加载目标"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                self.goals = [line.strip() for line in file if line.strip()]
            
            self.log(f"已加载 {len(self.goals)} 个目标")
            self.progress_bar['maximum'] = len(self.goals)
            self.update_progress(0)
            
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {e}")
            self.log(f"读取文件失败: {e}")
    
    def start_execution(self):
        """开始执行目标"""
        if not self.current_file:
            messagebox.showwarning("警告", "请先选择目标文件")
            return
        
        if not self.goals:
            messagebox.showwarning("警告", "文件中没有有效的目标")
            return
        
        if not self.agent:
            self.initialize_agent()
            if not self.agent:
                return
        
        self.is_running = True
        self.current_goal_index = 0
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        
        # 在新线程中执行
        thread = threading.Thread(target=self.execute_goals)
        thread.daemon = True
        thread.start()
    
    def pause_execution(self):
        """暂停执行"""
        self.is_running = False
        self.pause_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.log("执行已暂停")
    
    def stop_execution(self):
        """停止执行"""
        self.is_running = False
        self.current_goal_index = 0
        self.progress_bar['value'] = 0
        self.progress_var.set("0/0")
        
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log("执行已停止")
    
    def execute_goals(self):
        """执行目标序列"""
        total_goals = len(self.goals)
        
        for i in range(self.current_goal_index, total_goals):
            if not self.is_running:
                break
            
            goal = self.goals[i]
            self.current_goal_index = i
            
            # 更新UI（必须在主线程中执行）
            self.root.after(0, self.update_progress, i + 1)
            self.root.after(0, self.log, f"执行目标 {i+1}/{total_goals}: {goal}")
            
            try:
                response, success, total_token = self.agent.run_autonomous_goal(goal)
                self.root.after(0,self.log, f"AI思考: {response.get('thought', '无')}")
                self.root.after(0,self.log, f"AI建议: {response.get('action', '无')}")
                
                if success:
                    log_message = f"✓ 目标 {i+1} 执行成功 (步骤数: {self.agent.current_step})"
                    self.root.after(0,self.log, f"总token数: {total_token}")
                else:
                    log_message = f"✗ 目标 {i+1} 执行失败"
                
                self.root.after(0, self.log, log_message)
                
            except Exception as e:
                error_message = f"✗ 目标 {i+1} 执行异常: {e}"
                self.root.after(0, self.log, error_message)
            
            # 短暂延迟，避免执行过快
            time.sleep(1)
        
        # 执行完成
        self.root.after(0, self.execution_completed)
    
    def update_progress(self, current):
        """更新进度显示"""
        total = len(self.goals)
        self.progress_var.set(f"{current}/{total}")
        self.progress_bar['value'] = current
    
    def execution_completed(self):
        """执行完成后的处理"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        
        completed = self.current_goal_index + 1
        total = len(self.goals)
        
        if completed == total:
            self.log("所有目标执行完成！")
            messagebox.showinfo("完成", "所有目标已执行完成！")
        else:
            self.log(f"执行中断，已完成 {completed}/{total} 个目标")
    
    def log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.status_var.set(message)

def main():
    root = tk.Tk()
    app = GoalExecutorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()