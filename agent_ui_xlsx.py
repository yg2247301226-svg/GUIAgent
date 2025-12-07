import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import json
import time
from rag_enhanced_agent import RAGEnhancedGUIAgent
import threading
from markdown_rag import MarkdownKnowledgeRetriever, OpenAIMarkdownVectorDB

class TestCaseManager:
    def __init__(self, root):
        self.root = root
        # 设置主题风格
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义颜色
        bg_color = "#f0f0f0"
        frame_color = "#e0e0e0"
        select_color = "#3498db"
        
        # 配置样式
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, bordercolor=frame_color)
        style.configure("TLabelframe.Label", background=bg_color, font=("Microsoft YaHei", 10, "bold"))
        style.configure("TButton", font=("Microsoft YaHei", 9), padding=6)
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"))
        style.configure("TNotebook", background=bg_color)
        style.configure("TNotebook.Tab", padding=[12, 8], font=("Microsoft YaHei", 9))
        
        self.root.title("智能GUI测试管理系统")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 存储测试用例数据
        self.test_cases = []
        self.api_key = ""
        self.total_tokens = 0
        self.agent = None
        
        # API Key 配置文件
        self.config_file = "app_config.json"
        self.config = {
            "api_key": ""
        }
        
        # 测试执行记录
        self.execution_history_file = "execution_history.json"
        self.session_history = {
            "total_sessions": 0,
            "total_executions": 0,
            "session_date": "",
            "executions_in_session": 0,
            "total_success": 0,
            "total_failed": 0
        }
        
        # 加载配置和历史记录
        self.load_config()
        self.load_execution_history()
        
        self.create_widgets()
        
        # 延迟刷新MD文件列表，确保界面完全加载后再执行
        self.root.after(100, self.refresh_md_file_list)
        
    def create_widgets(self):
        # 创建顶部标题栏
        title_frame = ttk.Frame(self.root)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=20, pady=(10, 5))
        
        title_label = ttk.Label(title_frame, text="智能GUI测试管理系统", 
                                font=("Microsoft YaHei", 16, "bold"))
        title_label.pack()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧：测试用例列表
        left_frame = ttk.LabelFrame(main_frame, text="测试用例列表", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # 添加搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)
        
        search_label = ttk.Label(search_frame, text="快速搜索:")
        search_label.grid(row=0, column=0, sticky=tk.W)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.filter_test_cases)
        
        # 创建树状视图显示测试用例
        columns = ("编号", "用例名称", "完成状态", "Token使用数")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.tree.heading("编号", text="编号")
        self.tree.heading("用例名称", text="用例名称")
        self.tree.heading("完成状态", text="完成状态")
        self.tree.heading("Token使用数", text="Token使用数")
        
        # 设置列宽
        self.tree.column("编号", width=80)
        self.tree.column("用例名称", width=300)
        self.tree.column("完成状态", width=100)
        self.tree.column("Token使用数", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 添加底部状态栏
        status_frame = ttk.Frame(left_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        # 添加测试用例计数
        self.case_count_label = ttk.Label(status_frame, text="总计: 0 个测试用例")
        self.case_count_label.pack(side=tk.RIGHT)
        
        # 右侧：控制面板
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # 创建Notebook组件来组织右侧面板
        self.right_notebook = ttk.Notebook(right_frame)
        self.right_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        right_frame.rowconfigure(0, weight=1)
        
        # 选项卡1：测试用例控制
        control_frame = ttk.Frame(self.right_notebook, padding="15")
        self.right_notebook.add(control_frame, text="测试用例控制")
        control_frame.columnconfigure(0, weight=1)
        
        # 创建滚动区域
        canvas = tk.Canvas(control_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API Key 设置区域
        api_frame = ttk.LabelFrame(scrollable_frame, text="🔑 API Key 设置", padding="15")
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        api_input_frame = ttk.Frame(api_frame)
        api_input_frame.pack(fill=tk.X)
        
        self.api_entry = ttk.Entry(api_input_frame, width=40, show="*", font=("Microsoft YaHei", 10))
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(api_input_frame, text="保存", command=self.save_api_key, 
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        
        # 文件操作区域
        file_frame = ttk.LabelFrame(scrollable_frame, text="📁 文件操作", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.file_var = tk.StringVar()
        file_path_frame = ttk.Frame(file_frame)
        file_path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(file_path_frame, textvariable=self.file_var, state="readonly", 
                 font=("Microsoft YaHei", 9)).pack(fill=tk.X)
        
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X)
        
        ttk.Button(file_button_frame, text="选择Excel文件", 
                  command=self.select_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_button_frame, text="导入测试用例", 
                  command=self.import_test_cases).pack(side=tk.LEFT, padx=5)
        
        # Token 统计区域
        token_frame = ttk.LabelFrame(scrollable_frame, text="📊 Token 统计", padding="15")
        token_frame.pack(fill=tk.X, pady=(0, 15))
        
        token_info_frame = ttk.Frame(token_frame)
        token_info_frame.pack(fill=tk.X)
        
        self.token_label = ttk.Label(token_info_frame, text="总Token数: 0", 
                                    font=("Microsoft YaHei", 11, "bold"))
        self.token_label.pack(side=tk.LEFT)
        
        # 执行历史统计区域
        history_frame = ttk.LabelFrame(scrollable_frame, text="📈 执行历史统计", padding="15")
        history_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建统计网格
        stats_frame = ttk.Frame(history_frame)
        stats_frame.pack(fill=tk.X)
        
        # 第一行统计
        row1_frame = ttk.Frame(stats_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 8))
        
        session_frame = ttk.Frame(row1_frame)
        session_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(session_frame, text="总会话数:", 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor=tk.W)
        self.session_label = ttk.Label(session_frame, text="0", 
                                     font=("Microsoft YaHei", 10))
        self.session_label.pack(anchor=tk.W)
        
        execution_frame = ttk.Frame(row1_frame)
        execution_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(execution_frame, text="总执行数:", 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor=tk.W)
        self.execution_label = ttk.Label(execution_frame, text="0", 
                                       font=("Microsoft YaHei", 10))
        self.execution_label.pack(anchor=tk.W)
        
        # 第二行统计
        row2_frame = ttk.Frame(stats_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 8))
        
        success_frame = ttk.Frame(row2_frame)
        success_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(success_frame, text="成功率:", 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor=tk.W)
        self.success_rate_label = ttk.Label(success_frame, text="0.0%", 
                                          font=("Microsoft YaHei", 10))
        self.success_rate_label.pack(anchor=tk.W)
        
        date_frame = ttk.Frame(row2_frame)
        date_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(date_frame, text="上次会话:", 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor=tk.W)
        self.last_session_label = ttk.Label(date_frame, text="无", 
                                          font=("Microsoft YaHei", 10))
        self.last_session_label.pack(anchor=tk.W)
        
        # 更新统计显示
        self.update_history_display()
        
        # 操作按钮区域
        button_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ 操作控制", padding="15")
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 主要操作按钮
        main_button_frame = ttk.Frame(button_frame)
        main_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(main_button_frame, text="▶️ 执行选中用例", 
                  command=self.execute_selected_case, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(main_button_frame, text="⏩ 执行全部用例", 
                  command=self.execute_all_cases, width=20).pack(side=tk.LEFT)
        
        # 辅助操作按钮
        aux_button_frame = ttk.Frame(button_frame)
        aux_button_frame.pack(fill=tk.X)
        
        ttk.Button(aux_button_frame, text="📋 查看历史记录", 
                  command=self.show_execution_history, width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(aux_button_frame, text="🧹 清理低质量数据", 
                  command=self.clean_low_usage_data, width=20).pack(side=tk.LEFT)
        
        # 打包滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 选项卡2：MD知识库管理
        md_frame = ttk.Frame(self.right_notebook, padding="15")
        self.right_notebook.add(md_frame, text="📚 知识库管理")
        md_frame.columnconfigure(0, weight=1)
        md_frame.rowconfigure(1, weight=1)
        
        # MD文件列表
        md_list_frame = ttk.LabelFrame(md_frame, text="📄 知识库中的MD文件", padding="15")
        md_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        md_list_frame.columnconfigure(0, weight=1)
        md_list_frame.rowconfigure(0, weight=1)
        
        # 创建树状视图显示MD文件
        md_columns = ("文件名", "来源路径", "内容块数")
        self.md_tree = ttk.Treeview(md_list_frame, columns=md_columns, show="headings", height=12)
        
        # 设置列标题
        self.md_tree.heading("文件名", text="文件名")
        self.md_tree.heading("来源路径", text="来源路径")
        self.md_tree.heading("内容块数", text="内容块数")
        
        # 设置列宽
        self.md_tree.column("文件名", width=250)
        self.md_tree.column("来源路径", width=280)
        self.md_tree.column("内容块数", width=100)
        
        # 添加滚动条
        md_scrollbar = ttk.Scrollbar(md_list_frame, orient=tk.VERTICAL, command=self.md_tree.yview)
        self.md_tree.configure(yscrollcommand=md_scrollbar.set)
        
        self.md_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        md_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # MD文件统计信息
        md_stats_frame = ttk.Frame(md_frame)
        md_stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.md_count_label = ttk.Label(md_stats_frame, text="总文件数: 0", 
                                      font=("Microsoft YaHei", 10, "bold"))
        self.md_count_label.pack(side=tk.LEFT)
        
        self.md_chunks_label = ttk.Label(md_stats_frame, text="总内容块: 0", 
                                       font=("Microsoft YaHei", 10, "bold"))
        self.md_chunks_label.pack(side=tk.RIGHT)
        
        # MD文件操作按钮区域
        md_button_frame = ttk.LabelFrame(md_frame, text="🛠️ 文件操作", padding="15")
        md_button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # 第一行按钮
        md_button_row1 = ttk.Frame(md_button_frame)
        md_button_row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(md_button_row1, text="🔄 刷新文件列表", 
                  command=self.refresh_md_file_list, width=18).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(md_button_row1, text="🗑️ 删除选中文件", 
                  command=self.delete_selected_md_file, width=18).pack(side=tk.LEFT)
        
        # 第二行按钮
        md_button_row2 = ttk.Frame(md_button_frame)
        md_button_row2.pack(fill=tk.X)
        
        ttk.Button(md_button_row2, text="📤 上传MD文件", 
                  command=self.upload_md_to_knowledge, width=18).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(md_button_row2, text="📊 查看知识库统计", 
                  command=self.show_knowledge_stats, width=18).pack(side=tk.LEFT)
        
        # 选项卡3：执行信息
        info_frame = ttk.Frame(self.right_notebook, padding="15")
        self.right_notebook.add(info_frame, text="📄 执行信息")
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)
        
        # 信息控制区
        info_control_frame = ttk.Frame(info_frame)
        info_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(info_control_frame, text="🗑️ 清空日志", 
                  command=self.clear_info_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(info_control_frame, text="📥 导出日志", 
                  command=self.export_info_log).pack(side=tk.LEFT)
        
        # 日志显示区
        log_frame = ttk.LabelFrame(info_frame, text="📜 执行日志", padding="10")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 创建自定义文本框样式
        self.info_text = tk.Text(log_frame, wrap=tk.WORD, font=("Microsoft YaHei", 9),
                               bg="#2e3440", fg="#d8dee9", insertbackground="#d8dee9",
                               selectbackground="#434c5e", selectforeground="#d8dee9")
        scrollbar_info = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar_info.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_info.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
    def save_api_key(self):
        api_key_input = self.api_entry.get().strip()
        if api_key_input:
            self.api_key = api_key_input
            
            # 保存到配置文件
            self.save_config()
            
            try:
                self.agent = RAGEnhancedGUIAgent(api_key=self.api_key)
                messagebox.showinfo("成功", "API Key 已保存并成功初始化代理")
                self.log_info(f"🔑 API Key 已保存并初始化代理")
                
                # 刷新MD文件列表
                self.refresh_md_file_list()
            except Exception as e:
                messagebox.showerror("错误", f"初始化代理失败: {e}")
                self.log_info(f"❌ 初始化代理失败: {e}")
        else:
            messagebox.showwarning("警告", "请输入有效的 API Key")
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
    
    def import_test_cases(self):
        filename = self.file_var.get()
        if not filename:
            messagebox.showwarning("警告", "请先选择Excel文件")
            return
        
        try:
            # 读取Excel文件
            df = pd.read_excel(filename, sheet_name='Sheet1')
            
            # 清空现有数据
            self.test_cases = []
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 处理数据并显示
            for index, row in df.iterrows():
                case_id = str(row.get('编号', ''))
                case_name = str(row.get('用例名称', ''))
                
                if case_id and case_name:
                    case_data = {
                        '编号': case_id,
                        '用例名称': case_name,
                        '前置条件': str(row.get('前置条件', '')),
                        '操作步骤': str(row.get('操作步骤', '')),
                        '预期结果': str(row.get('预期结果', '')),
                        '完成状态': '未完成',
                        'Token使用数': 0
                    }
                    self.test_cases.append(case_data)
                    
                    # 添加到树状视图
                    self.tree.insert("", "end", values=(
                        case_data['编号'],
                        case_data['用例名称'],
                        case_data['完成状态'],
                        case_data['Token使用数']
                    ))
            
            # 更新测试用例计数
            self.case_count_label.config(text=f"总计: {len(self.test_cases)} 个测试用例")
            self.log_info(f"成功导入 {len(self.test_cases)} 个测试用例")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入文件失败: {e}")
            self.log_info(f"读取文件失败: {e}")
    
    def filter_test_cases(self, event=None):
        """根据搜索框内容过滤测试用例"""
        search_term = self.search_var.get().lower()
        
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 重新添加匹配的测试用例
        filtered_count = 0
        for case in self.test_cases:
            # 检查是否匹配搜索条件
            if (search_term == "" or 
                search_term in case['编号'].lower() or 
                search_term in case['用例名称'].lower() or
                search_term in case['完成状态'].lower()):
                
                self.tree.insert("", "end", values=(
                    case['编号'],
                    case['用例名称'],
                    case['完成状态'],
                    case['Token使用数']
                ))
                filtered_count += 1
        
        # 更新状态
        self.status_label.config(text=f"已过滤: 显示 {filtered_count} / {len(self.test_cases)} 个测试用例")
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    self.api_key = self.config.get('api_key', '')
                    print(f"✅ 已加载配置文件")
                    
                    # 如果有API Key，尝试初始化代理
                    if self.api_key:
                        try:
                            self.agent = RAGEnhancedGUIAgent(api_key=self.api_key)
                            self.api_entry.delete(0, tk.END)
                            self.api_entry.insert(0, self.api_key)
                            print(f"✅ 已使用保存的API Key初始化代理")
                        except Exception as e:
                            print(f"❌ 使用保存的API Key初始化代理失败: {e}")
            else:
                print(f"⚠️ 未找到配置文件，将创建新文件")
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            self.config = {"api_key": ""}
    
    def save_config(self):
        """保存配置文件"""
        try:
            self.config['api_key'] = self.api_key
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"💾 配置文件已保存")
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
    
    def log_info(self, message):
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)
        self.root.update()
    
    def load_execution_history(self):
        """加载执行历史记录"""
        try:
            if os.path.exists(self.execution_history_file):
                with open(self.execution_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.session_history = data
                    print(f"✅ 已加载执行历史记录")
            else:
                print(f"⚠️ 未找到历史记录文件，将创建新文件")
        except Exception as e:
            print(f"❌ 加载历史记录失败: {e}")
    
    def save_execution_history(self):
        """保存执行历史记录"""
        try:
            with open(self.execution_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_history, f, ensure_ascii=False, indent=2)
            print(f"💾 执行历史记录已保存")
        except Exception as e:
            print(f"❌ 保存历史记录失败: {e}")
    
    def update_history_display(self):
        """更新历史统计显示"""
        self.session_label.config(text=f"总会话数: {self.session_history['total_sessions']}")
        self.execution_label.config(text=f"总执行数: {self.session_history['total_executions']}")
        
        # 计算成功率
        total = self.session_history['total_executions']
        success = self.session_history['total_success']
        success_rate = (success / total * 100) if total > 0 else 0.0
        self.success_rate_label.config(text=f"成功率: {success_rate:.1f}%")
        
        # 显示上次会话日期
        last_date = self.session_history['session_date']
        if last_date:
            # 将时间戳转换为可读格式
            if isinstance(last_date, (int, float)):
                last_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_date))
            self.last_session_label.config(text=f"上次会话日期: {last_date}")
        else:
            self.last_session_label.config(text="上次会话日期: 无")
    
    def start_new_session(self):
        """开始新的会话"""
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
        
        # 检查是否是新的日期会话
        last_session_date = self.session_history.get('session_date', 0)
        if isinstance(last_session_date, str):
            # 如果是字符串，尝试转换为时间戳
            try:
                last_session_date = time.mktime(time.strptime(last_session_date, '%Y-%m-%d %H:%M:%S'))
            except:
                last_session_date = 0
        
        # 检查是否是新的一天或首次运行
        if not last_session_date or time.strftime('%Y-%m-%d', time.localtime(current_time)) != time.strftime('%Y-%m-%d', time.localtime(last_session_date)):
            # 新的一天，增加会话计数
            self.session_history['total_sessions'] += 1
            self.session_history['session_date'] = current_date
            self.session_history['executions_in_session'] = 0
            self.log_info(f"📅 开始新的会话 (#{self.session_history['total_sessions']})")
        elif self.session_history['executions_in_session'] == 0:
            # 同一天但首次运行
            self.session_history['session_date'] = current_date
            self.log_info(f"📅 继续今日会话 (#{self.session_history['total_sessions']})")
        
        # 保存更新
        self.save_execution_history()
        self.update_history_display()
    
    def record_execution(self, success):
        """记录测试用例执行"""
        # 更新统计
        self.session_history['total_executions'] += 1
        self.session_history['executions_in_session'] += 1
        
        if success:
            self.session_history['total_success'] += 1
        else:
            self.session_history['total_failed'] += 1
        
        # 保存更新
        self.save_execution_history()
        self.update_history_display()
    
    def show_execution_history(self):
        """显示执行历史记录"""
        history_window = tk.Toplevel(self.root)
        history_window.title("测试用例执行历史")
        history_window.geometry("600x400")
        
        # 创建文本框显示历史
        text_frame = ttk.Frame(history_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        history_text = tk.Text(text_frame, wrap=tk.WORD)
        history_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=history_text.yview)
        history_text.configure(yscrollcommand=history_scrollbar.set)
        
        history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 格式化历史记录
        history_content = "测试用例执行历史记录\n"
        history_content += "=" * 40 + "\n\n"
        
        history_content += f"总会话数: {self.session_history['total_sessions']}\n"
        history_content += f"总执行数: {self.session_history['total_executions']}\n"
        history_content += f"总成功数: {self.session_history['total_success']}\n"
        history_content += f"总失败数: {self.session_history['total_failed']}\n"
        
        # 计算成功率
        total = self.session_history['total_executions']
        success = self.session_history['total_success']
        success_rate = (success / total * 100) if total > 0 else 0.0
        history_content += f"总体成功率: {success_rate:.1f}%\n"
        
        # 显示会话日期
        session_date = self.session_history.get('session_date', '')
        if session_date:
            history_content += f"最近会话日期: {session_date}\n"
        
        history_content += f"本次会话执行数: {self.session_history['executions_in_session']}\n"
        
        # 插入到文本框
        history_text.insert(tk.END, history_content)
        history_text.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_button = ttk.Button(history_window, text="关闭", command=history_window.destroy)
        close_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 清理按钮
        def cleanup_history():
            if messagebox.askyesno("确认", "确定要重置所有执行历史记录吗？此操作不可撤销。"):
                self.session_history = {
                    "total_sessions": 0,
                    "total_executions": 0,
                    "session_date": "",
                    "executions_in_session": 0,
                    "total_success": 0,
                    "total_failed": 0
                }
                self.save_execution_history()
                self.update_history_display()
                history_window.destroy()
                messagebox.showinfo("成功", "执行历史记录已重置")
        
        cleanup_button = ttk.Button(history_window, text="重置历史记录", command=cleanup_history)
        cleanup_button.pack(side=tk.LEFT, padx=10, pady=10)
    
    def execute_selected_case(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要执行的测试用例")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先设置 API Key")
            return
        
        # 开始新会话（如果需要）
        self.start_new_session()
        
        # 在新线程中执行
        thread = threading.Thread(target=self._execute_case_thread, args=(selection,))
        thread.daemon = True
        thread.start()
    
    def execute_all_cases(self):
        if not self.test_cases:
            messagebox.showwarning("警告", "没有可执行的测试用例")
            return
        
        if not self.api_key:
            messagebox.showwarning("警告", "请先设置 API Key")
            return
        
        # 开始新会话（如果需要）
        self.start_new_session()
        
        # 在新线程中执行
        thread = threading.Thread(target=self._execute_all_cases_thread)
        thread.daemon = True
        thread.start()
    
    def _execute_case_thread(self, selection):
        for item in selection:
            case_values = self.tree.item(item)['values']
            case_id = case_values[0]
            
            # 找到对应的测试用例数据
            case_data = None
            for case in self.test_cases:
                if int(case['编号']) == case_id:
                    case_data = case
                    break
            
            if case_data:
                self._execute_single_case(case_data, item)
    
    def _execute_all_cases_thread(self):
        for item in self.tree.get_children():
            case_values = self.tree.item(item)['values']
            case_id = case_values[0]
            
            # 找到对应的测试用例数据
            case_data = None
            for case in self.test_cases:
                if int(case['编号']) == case_id:
                    case_data = case
                    break
            if case_data:
                self._execute_single_case(case_data, item)

    def convert_test_case(self,original):
        # 键名映射关系
        key_mapping = {
            '用例名称': 'task',
            '前置条件': 'prerequisites', 
            '操作步骤': 'steps',
            '预期结果': 'expected_result'
        }
        
        # 创建新字典
        new_dict = {}
        
        for old_key, new_key in key_mapping.items():
            if old_key in original:
                # 处理操作步骤和预期结果中的换行符
                value = original[old_key]
                if old_key in ['操作步骤', '预期结果']:
                    # 将换行符替换为空格，并去除多余空格
                    value = ' '.join(value.split())
                new_dict[new_key] = value
        
        return new_dict
    
    def _execute_single_case(self, case_data, tree_item):
        try:
            self.log_info(f"开始执行测试用例 {case_data['编号']}: {case_data['用例名称']}")
            
            # # 构建目标描述字符串（而不是字典对象）
            # goal_description = f"{case_data['用例名称']}"
            
            # # 如果有前置条件，添加到目标描述中
            # if case_data.get('前置条件'):
            #     goal_description += f"，前置条件：{case_data['前置条件']}"
            
            # # 如果有操作步骤，添加到目标描述中
            # if case_data.get('操作步骤'):
            #     goal_description += f"，操作步骤：{case_data['操作步骤']}"
            
            # # 如果有预期结果，添加到目标描述中
            # if case_data.get('预期结果'):
            #     goal_description += f"，预期结果：{case_data['预期结果']}"
            goal_description = self.convert_test_case(case_data)
            
            # 执行测试用例
            response, success, total_token = self.agent.run_rag_enhanced_goal(goal_description)
            
            # 更新界面
            self.root.after(0, self._update_case_result, tree_item, success, total_token)
            
            # 记录执行结果到历史记录
            self.record_execution(success)
            
            # 记录执行信息
            if success:
                self.log_info(f"测试用例 {case_data['编号']} 执行成功！")
                if response:
                    self.log_info(f"AI思考: {response.get('thought', '无')}")
            else:
                self.log_info(f"测试用例 {case_data['编号']} 执行失败")
            
            self.log_info(f"Token使用数: {total_token}")
            self.log_info("-" * 50)
            
        except Exception as e:
            self.log_info(f"执行测试用例 {case_data['编号']} 时发生错误: {e}")
            # 即使出错也要记录
            self.record_execution(False)
    
    def _update_case_result(self, tree_item, success, token_used):
        # 更新树状视图
        current_values = self.tree.item(tree_item)['values']
        new_values = (
            current_values[0],  # 编号
            current_values[1],  # 用例名称
            "完成" if success else "失败",  # 完成状态
            token_used  # Token使用数
        )
        self.tree.item(tree_item, values=new_values)
        
        # 更新总Token数
        self.total_tokens += token_used
        self.token_label.config(text=f"总Token数: {self.total_tokens}")
    
    def clean_low_usage_data(self):
        """清理使用率低的数据"""
        if not self.agent:
            messagebox.showwarning("警告", "请先初始化代理")
            return
        
        # 创建配置对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("清理低使用率数据")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # 设置为模态对话框
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 使用率阈值
        ttk.Label(dialog, text="使用率阈值 (0.0-1.0):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        usage_threshold_var = tk.DoubleVar(value=0.2)
        usage_scale = ttk.Scale(dialog, from_=0.0, to=1.0, variable=usage_threshold_var, orient=tk.HORIZONTAL)
        usage_scale.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        usage_label = ttk.Label(dialog, text="0.2")
        usage_label.grid(row=0, column=2, padx=5, pady=10)
        
        # 更新标签显示
        def update_usage_label(value):
            usage_label.config(text=f"{float(value):.2f}")
        
        usage_scale.config(command=update_usage_label)
        
        # 最小使用次数
        ttk.Label(dialog, text="最小使用次数:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        min_usage_var = tk.IntVar(value=1)
        min_usage_spin = ttk.Spinbox(dialog, from_=0, to=100, textvariable=min_usage_var, width=10)
        min_usage_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        # 清理类型
        ttk.Label(dialog, text="清理类型:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        cleanup_type_var = tk.StringVar(value="all")
        cleanup_frame = ttk.Frame(dialog)
        cleanup_frame.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        
        ttk.Radiobutton(cleanup_frame, text="全部", variable=cleanup_type_var, value="all").pack(side=tk.LEFT)
        ttk.Radiobutton(cleanup_frame, text="任务经验", variable=cleanup_type_var, value="tasks").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(cleanup_frame, text="截图知识", variable=cleanup_type_var, value="screenshots").pack(side=tk.LEFT)
        
        # 最大失败率
        ttk.Label(dialog, text="最大失败率 (0.0-1.0):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        failure_rate_var = tk.DoubleVar(value=0.8)
        failure_rate_scale = ttk.Scale(dialog, from_=0.0, to=1.0, variable=failure_rate_var, orient=tk.HORIZONTAL)
        failure_rate_scale.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        failure_rate_label = ttk.Label(dialog, text="0.8")
        failure_rate_label.grid(row=3, column=2, padx=5, pady=10)
        
        # 更新标签显示
        def update_failure_rate_label(value):
            failure_rate_label.config(text=f"{float(value):.2f}")
        
        failure_rate_scale.config(command=update_failure_rate_label)
        
        # 结果显示
        result_frame = ttk.LabelFrame(dialog, text="清理结果", padding="5")
        result_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky=tk.W+tk.E)
        
        result_text = tk.Text(result_frame, height=5, width=40)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        # 执行清理按钮
        def execute_cleanup():
            try:
                usage_threshold = usage_threshold_var.get()
                min_usage = min_usage_var.get()
                cleanup_type = cleanup_type_var.get()
                max_failure_rate = failure_rate_var.get()
                
                # 清理低使用率知识
                result_stats = self.agent.clean_low_usage_knowledge(
                    usage_threshold=usage_threshold,
                    min_usage_count=min_usage,
                    max_failure_rate=max_failure_rate,
                    experience_type=cleanup_type
                )
                
                # 更新结果显示
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"清理完成!\n")
                result_text.insert(tk.END, f"删除任务经验: {result_stats['removed_tasks']} 个\n")
                result_text.insert(tk.END, f"剩余任务经验: {result_stats['remaining_tasks']} 个\n")
                result_text.insert(tk.END, f"删除截图知识: {result_stats['removed_screenshots']} 个\n")
                result_text.insert(tk.END, f"剩余截图知识: {result_stats['remaining_screenshots']} 个\n")
                result_text.insert(tk.END, f"因高失败率删除: {result_stats['removed_for_high_failure_rate']} 个\n")
                
                # 更新知识库统计显示
                self.log_info(f"🧹 清理完成: "
                              f"删除 {result_stats['removed_tasks']} 个任务经验, "
                              f"删除 {result_stats['removed_screenshots']} 个截图知识, "
                              f"其中 {result_stats['removed_for_high_failure_rate']} 个因高失败率被删除")
                
            except Exception as e:
                messagebox.showerror("错误", f"清理过程中发生错误: {e}")
                self.log_info(f"清理错误: {e}")
        
        ttk.Button(button_frame, text="执行清理", command=execute_cleanup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def upload_md_to_knowledge(self):
        """上传MD文件并转成知识库"""
        if not self.agent:
            messagebox.showwarning("警告", "请先初始化代理")
            return
        
        # 创建文件选择对话框
        md_files = filedialog.askopenfilenames(
            title="选择Markdown文件",
            filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")]
        )
        
        if not md_files:
            return
        
        # 创建进度对话框
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("上传进度")
        progress_dialog.geometry("400x150")
        progress_dialog.resizable(False, False)
        
        # 设置为模态对话框
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # 进度条
        ttk.Label(progress_dialog, text="上传进度:").pack(pady=10)
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=100, length=300)
        progress_bar.pack(pady=10)
        
        # 状态标签
        status_var = tk.StringVar(value="准备上传...")
        status_label = ttk.Label(progress_dialog, textvariable=status_var)
        status_label.pack(pady=10)
        
        # 在新线程中执行上传
        def upload_thread():
            try:
                total_files = len(md_files)
                successful_files = 0
                
                for i, md_file in enumerate(md_files):
                    # 更新状态
                    status_var.set(f"正在上传: {os.path.basename(md_file)} ({i+1}/{total_files})")
                    progress_var.set((i / total_files) * 100)
                    progress_dialog.update()
                    
                    try:
                        # 使用代理的Markdown知识库处理
                        if hasattr(self.agent, 'md_knowledge_base') and self.agent.md_knowledge_base:
                            # 直接使用add_markdown_file方法
                            result = self.agent.md_knowledge_base.add_markdown_file(md_file)
                            if result['success']:
                                successful_files += 1
                                self.log_info(f"上传文件 {os.path.basename(md_file)} 成功: 处理了 {result['chunks_processed']} 个内容块")
                            else:
                                self.log_info(f"上传文件 {os.path.basename(md_file)} 失败: {result.get('error', '未知错误')}")
                        else:
                            # 如果没有现有知识库，创建一个新的
                            temp_db = OpenAIMarkdownVectorDB()
                            result = temp_db.add_markdown_file(md_file)
                            if result['success']:
                                successful_files += 1
                                self.log_info(f"上传文件 {os.path.basename(md_file)} 成功: 处理了 {result['chunks_processed']} 个内容块")
                            else:
                                self.log_info(f"上传文件 {os.path.basename(md_file)} 失败: {result.get('error', '未知错误')}")
                        
                    except Exception as e:
                        self.log_info(f"上传文件 {os.path.basename(md_file)} 失败: {e}")
                
                # 完成上传
                progress_var.set(100)
                status_var.set(f"上传完成! 成功: {successful_files}/{total_files}")
                
                # 更新日志
                self.log_info(f"📚 MD文件上传完成: 成功上传 {successful_files} 个文件，共 {total_files} 个文件")
                
                # 1秒后关闭对话框
                progress_dialog.after(1000, progress_dialog.destroy)
                
            except Exception as e:
                status_var.set(f"上传失败: {str(e)}")
                self.log_info(f"MD文件上传失败: {e}")
                progress_dialog.after(3000, progress_dialog.destroy)
        
        # 启动上传线程
        thread = threading.Thread(target=upload_thread)
        thread.daemon = True
        thread.start()
    
    def refresh_md_file_list(self):
        """刷新MD文件列表"""
        if not self.agent:
            messagebox.showwarning("警告", "请先初始化代理")
            return
        
        try:
            # 清空现有列表
            for item in self.md_tree.get_children():
                self.md_tree.delete(item)
            
            # 获取所有MD文件
            md_files = self.agent.get_all_md_files()
            
            # 添加到树状视图
            for md_file in md_files:
                self.md_tree.insert("", "end", values=(
                    md_file['file_name'],
                    md_file['source'],
                    md_file['chunk_count']
                ))
            
            # 更新统计信息
            total_files = len(md_files)
            total_chunks = sum(f['chunk_count'] for f in md_files)
            self.md_count_label.config(text=f"总文件数: {total_files}")
            self.md_chunks_label.config(text=f"总内容块: {total_chunks}")
            
            self.log_info(f"📚 已刷新MD文件列表，共 {total_files} 个文件，{total_chunks} 个内容块")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新MD文件列表失败: {e}")
            self.log_info(f"刷新MD文件列表失败: {e}")
    
    def delete_selected_md_file(self):
        """删除选中的MD文件"""
        selection = self.md_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的MD文件")
            return
        
        if not self.agent:
            messagebox.showwarning("警告", "请先初始化代理")
            return
        
        # 确认删除
        file_names = []
        for item in selection:
            values = self.md_tree.item(item)['values']
            file_names.append(values[0])
        
        confirm_message = f"确定要删除以下 {len(file_names)} 个MD文件吗？\n\n"
        for name in file_names:
            confirm_message += f"- {name}\n"
        
        confirm_message += "\n此操作不可撤销！"
        
        if not messagebox.askyesno("确认删除", confirm_message):
            return
        
        try:
            # 删除文件
            deleted_count = 0
            failed_count = 0
            failed_files = []
            
            for file_name in file_names:
                result = self.agent.delete_md_file(file_name)
                if result['success']:
                    deleted_count += 1
                    self.log_info(f"✅ 已删除MD文件: {file_name} (删除 {result['deleted_chunks']} 个内容块)")
                else:
                    failed_count += 1
                    failed_files.append(f"{file_name}: {result.get('error', '未知错误')}")
                    self.log_info(f"❌ 删除MD文件失败: {file_name} - {result.get('error', '未知错误')}")
            
            # 刷新文件列表
            self.refresh_md_file_list()
            
            # 显示结果
            if failed_count > 0:
                error_message = f"删除完成，但有 {failed_count} 个文件删除失败:\n\n"
                for failed in failed_files:
                    error_message += f"- {failed}\n"
                messagebox.showwarning("部分失败", error_message)
            else:
                messagebox.showinfo("成功", f"成功删除 {deleted_count} 个MD文件")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除MD文件失败: {e}")
            self.log_info(f"删除MD文件失败: {e}")
    
    def show_knowledge_stats(self):
        """显示知识库统计信息"""
        if not self.agent:
            messagebox.showwarning("警告", "请先初始化代理")
            return
        
        try:
            # 获取MD文件统计
            md_files = self.agent.get_all_md_files()
            total_files = len(md_files)
            total_chunks = sum(f['chunk_count'] for f in md_files)
            
            # 获取任务知识库统计
            self.agent.print_knowledge_statistics()
            
            # 显示统计窗口
            stats_window = tk.Toplevel(self.root)
            stats_window.title("知识库统计信息")
            stats_window.geometry("600x500")
            stats_window.resizable(False, False)
            
            # 设置为模态对话框
            stats_window.transient(self.root)
            stats_window.grab_set()
            
            # 创建文本框显示统计
            text_frame = ttk.Frame(stats_window, padding="10")
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            stats_text = tk.Text(text_frame, wrap=tk.WORD, font=("Microsoft YaHei", 10))
            stats_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.configure(yscrollcommand=stats_scrollbar.set)
            
            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 格式化统计信息
            content = "📊 知识库统计信息\n"
            content += "=" * 50 + "\n\n"
            
            # MD知识库统计
            content += "📚 MD知识库统计\n"
            content += "-" * 30 + "\n"
            content += f"总文件数: {total_files}\n"
            content += f"总内容块数: {total_chunks}\n"
            
            if total_files > 0:
                # 按内容块数排序，显示最大的5个文件
                sorted_files = sorted(md_files, key=lambda x: x['chunk_count'], reverse=True)[:5]
                content += "\n🔝 内容块最多的5个文件:\n"
                for i, f in enumerate(sorted_files, 1):
                    content += f"{i}. {f['file_name']}: {f['chunk_count']} 块\n"
            
            content += "\n" + "=" * 50 + "\n"
            content += "\n🧠 任务经验知识库统计\n"
            content += "-" * 30 + "\n"
            
            # 获取任务知识库统计
            stats = self.agent.knowledge_base.get_statistics()
            content += f"总任务数: {stats['total_tasks']}\n"
            content += f"成功任务: {stats['successful_tasks']}\n"
            content += f"失败任务: {stats['failed_tasks']}\n"
            content += f"成功率: {stats['success_rate']:.1%}\n"
            content += f"截图知识: {stats['total_screenshots']} 条\n"
            content += f"知识库大小: {stats['knowledge_base_size_mb']:.2f} MB\n"
            
            # 插入到文本框
            stats_text.insert(tk.END, content)
            stats_text.config(state=tk.DISABLED)
            
            # 关闭按钮
            close_button = ttk.Button(stats_window, text="关闭", command=stats_window.destroy)
            close_button.pack(side=tk.RIGHT, padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取知识库统计失败: {e}")
            self.log_info(f"获取知识库统计失败: {e}")
    
    def clear_info_log(self):
        """清空信息日志"""
        self.info_text.delete(1.0, tk.END)
        self.log_info("🗑️ 日志已清空")
    
    def export_info_log(self):
        """导出信息日志"""
        try:
            content = self.info_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showinfo("提示", "日志为空，无需导出")
                return
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已导出到: {file_path}")
                self.log_info(f"📥 日志已导出到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {e}")
            self.log_info(f"导出日志失败: {e}")

def main():
    root = tk.Tk()
    app = TestCaseManager(root)
    
    # 设置窗口关闭时保存历史记录和配置
    def on_closing():
        app.save_execution_history()
        app.save_config()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
