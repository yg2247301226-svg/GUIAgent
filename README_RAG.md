# RAG增强的GUI自动化系统

## 🧠 概述

本项目是一个集成了RAG（Retrieval-Augmented Generation）技术的GUI自动化测试系统，实现了基于知识库的进化式自动化操作能力。系统能够从过去的成功和失败经验中学习，不断提升操作成功率。

## ✨ 核心特性

### 1. 双重知识库
- **任务经验知识库**: 存储历史任务的完整执行过程
- **操作指南知识库**: 存储飞书的操作指南

### 2. 智能检索
- 基于TF-IDF的相似任务检索
- 上下文相关的截图匹配
- 成功/失败模式分析

### 3. 进化学习
- 自动从成功案例中提取最佳实践
- 识别并避免无关的操作

### 4. RAG增强推理
- 将相关知识注入到AI推理过程
- 提供历史成功路径参考
- 实时生成操作指导

## 🏗️ 架构设计

```
GUIAgent_tars1/
├── rag_knowledge_base.py      # 知识库核心模块
├── rag_enhanced_agent.py      # RAG增强智能体
├── rag_main.py               # 主程序入口
├── GUIAgent.py               # 原始GUI智能体
├── knowledge_base/           # 知识库存储目录
└── screenshot/               # 截图存储目录
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置API密钥
```bash
export ARK_API_KEY="your_api_key_here"
```

### 3. 运行系统

#### 自动测试模式
```bash
python rag_main.py
# 选择 1
```

#### 交互模式
```bash
python rag_main.py
# 选择 2
```

## 📊 核心功能详解

### 1. 任务经验存储
每个任务执行完成后，系统会自动保存：
- 任务描述和目标
- 执行步骤和操作序列
- AI思考过程
- 截图信息
- 成功/失败状态
- Token消耗统计

### 2. 截图知识提取
对每个执行步骤，系统会分析：
- 截图上下文信息
- 成功的操作模式
- 失败的操作模式
- UI元素特征
- 相似性标签

### 3. 智能检索机制

#### 相似任务检索
```python
# 搜索相似的成功任务
similar_tasks = agent.search_similar_successful_tasks(
    task_description, top_k=5
)
```

#### 截图模式匹配
```python
# 获取上下文相关的成功操作
successful_actions = knowledge_base.get_successful_actions_for_context(context)
```

### 4. RAG增强推理
系统在执行新任务时，会：
1. 分析当前任务特征
2. 检索相关历史经验
3. 提取成功/失败模式
4. 生成增强的系统提示
5. 指导AI做出更优决策

## 🎯 使用示例

### 基础使用
```python
from rag_enhanced_agent import RAGEnhancedGUIAgent

# 初始化智能体
agent = RAGEnhancedGUIAgent(api_key="your_api_key")

# 执行任务
task = {
    "task": "在飞书中搜索联系人并发送消息",
    "prerequisites": "已登录飞书",
    "steps": "1. 打开搜索 2. 输入联系人 3. 发送消息",
    "expected_result": "消息发送成功"
}

response, success, tokens = agent.run_rag_enhanced_goal(task)
```

### 获取知识洞察
```python
# 获取任务相关的知识洞察
insights = agent.get_knowledge_insights("搜索联系人")
print(f"相似任务成功率: {insights['success_rate']:.1%}")
print(f"建议: {insights['recommendations']}")
```

## 📈 进化效果

### 学习曲线
- **初期**: 系统依赖基础推理
- **中期**: 开始利用相似任务经验
- **成熟期**: 形成稳定的操作模式库

### 性能提升
- **成功率提升**: 通过学习历史成功模式
- **效率优化**: 减少无效尝试
- **错误避免**: 规避已知失败模式

## 🔧 高级配置

### 知识库参数调整
```python
# 自定义知识库目录
agent = RAGEnhancedGUIAgent(
    api_key="your_key", 
    knowledge_dir="custom_knowledge"
)

# 调整检索参数
similar_tasks = agent.search_similar_tasks(
    task, 
    top_k=10,           # 增加检索数量
    only_successful=True # 仅检索成功案例
)
```

### 向量化配置
```python
# 在rag_knowledge_base.py中调整
self.vectorizer = TfidfVectorizer(
    max_features=2000,      # 增加特征数量
    ngram_range=(1, 3),     # 使用三元组
    min_df=1,              # 最小文档频率
    max_df=0.8             # 最大文档频率
)
```

## 📊 监控和分析

### 知识库统计
```python
stats = agent.knowledge_base.get_statistics()
print(f"总任务数: {stats['total_tasks']}")
print(f"成功率: {stats['success_rate']:.1%}")
print(f"知识库大小: {stats['knowledge_base_size_mb']:.2f} MB")
```

### 性能分析
系统提供详细的执行分析：
- Token使用效率
- 步骤优化程度
- 时间消耗分析
- 错误模式识别

## 🔄 持续进化

### 自动学习
- 每次任务执行都会更新知识库
- 成功案例强化正确模式
- 失败案例标记风险操作

### 知识清理
```python
# 清理低质量数据（可选功能）
knowledge_base.cleanup_low_quality_data(min_success_rate=0.3)
```

### 模式优化
系统会自动识别：
- 高效操作序列
- 常见错误模式
- 最佳实践路径

## 🛠️ 故障排除

### 常见问题
1. **知识库加载失败**: 检查文件权限和磁盘空间
2. **向量化错误**: 确认scikit-learn版本兼容性
3. **截图保存失败**: 检查screenshot目录权限

### 调试模式
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 扩展开发

### 自定义检索算法
```python
class RLAGUIAgent(RAGEnhancedGUIAgent):
    def __init__(self, api_key, knowledge_dir):
        super().__init__(api_key, knowledge_dir)
        self.rl_policy = load_policy_model()
        self.value_network = load_value_network()
    
    def select_action(self, state, retrieved_experiences):
        # 结合RAG检索和RL策略
        rag_actions = self.rag_policy.select(state, retrieved_experiences)
        rl_actions = self.rl_policy.select(state)
        # 使用探索策略平衡两者
        return self.exploration_strategy.select(rag_actions, rl_actions)
    pass
```

### 增强UI分析
```python
def advanced_ui_analysis(self, screenshot_path):
    def __init__(self):
        self.sam_model = load_sam_model()
        self.ocr_model = load_ocr_model()
        self.clip_model = load_clip_model()
    
    def detect_ui_elements(self, screenshot):
        # 使用SAM分割UI元素
        masks = self.sam_model.generate_masks(screenshot)
        # 使用OCR识别文本
        texts = self.ocr_model.extract_text(screenshot)
        # 使用CLIP理解语义
        embeddings = self.clip_model.encode(screenshot)
        return structured_ui_representation
    pass
```