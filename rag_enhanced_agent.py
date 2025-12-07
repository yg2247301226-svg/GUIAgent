"""
RAG增强的GUI智能体
集成知识库，实现进化式自动化操作能力
"""

import os
import json
import time
import base64
import io
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import pyautogui
from volcenginesdkarkruntime import Ark

from rag_knowledge_base import RAGKnowledgeBase, TaskExperience, ScreenshotKnowledge
from GUIAgent import DoubaoUITarsGUI
from prompt import COMPUTER_USE_DOUBAO1
from AutoGUI import PyAutoGUIActionExecutor
from ParseActionString import parse_action_string
import re
from markdown_rag import OpenAIMarkdownVectorDB, MarkdownKnowledgeRetriever


class RAGEnhancedGUIAgent(DoubaoUITarsGUI):
    """RAG增强的GUI智能体"""
    
    def __init__(self, api_key=None, knowledge_dir="knowledge_base"):
        """
        初始化RAG增强的GUI智能体
        
        Args:
            api_key: 火山引擎API Key
            knowledge_dir: 知识库目录
        """
        super().__init__(api_key)
        
        # 初始化知识库
        self.knowledge_base = RAGKnowledgeBase(knowledge_dir)
        self.md_knowledge_base = OpenAIMarkdownVectorDB()
        self.retriever = MarkdownKnowledgeRetriever(self.md_knowledge_base)
        
        # 当前任务信息
        self.current_task_id = None
        
        print("🧠 RAG增强GUI智能体已初始化")
        stats = self.knowledge_base.get_statistics()
        print(f"📊 知识库状态: {stats['total_tasks']} 个任务, "
              f"成功率 {stats['success_rate']:.1%}, "
              f"{stats['total_screenshots']} 个截图知识")
    
    def construct_rag_enhanced_messages(self, 
                                      instruction, 
                                      image_base64: str, 
                                      language: str = "Chinese") -> List[Dict]:
        """
        构建RAG增强的消息
        
        Args:
            instruction: 任务指令
            image_base64: 截图base64
            language: 语言
            
        Returns:
            增强后的消息列表
        """
        # 获取学习洞察
        insights = self.knowledge_base.get_learning_insights(str(instruction))

        # 获取markdown知识
        markdown_knowledge = self.retriever.query(instruction.get('task'),min_similarity=0.2).get('results')
        # 搜索相似任务
        similar_tasks = self.knowledge_base.search_similar_tasks(
            str(instruction), top_k=3, only_successful=True
        )
        # 搜索相似截图
        similar_screenshots = self.knowledge_base.search_similar_screenshots(
            str(instruction), top_k=2
        )
        
        # 构建RAG增强的系统提示
        rag_system_prompt = self._build_rag_system_prompt(
            instruction, insights, markdown_knowledge, similar_tasks, similar_screenshots, language
        )
        messages = [
            {
                "role": "user",
                "content": rag_system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        return messages
    
    def _build_rag_system_prompt(self, 
                                instruction: str,
                                insights: Dict[str, Any],
                                markdown_knowledge: List[str],
                                similar_tasks: List[TaskExperience],
                                similar_screenshots: List[ScreenshotKnowledge],
                                language: str) -> str:
        """构建RAG增强的系统提示"""
        
        base_prompt = COMPUTER_USE_DOUBAO1.format(instruction=instruction, language=language)
        
        # 添加RAG增强信息
        rag_enhancement = "\n\n## 🧠 RAG知识库增强信息\n\n"
        
        # 添加学习洞察
        if insights["success_rate"] > 0:
            rag_enhancement += f"### 📈 历史任务分析\n"
            rag_enhancement += f"- 相似任务成功率: {insights['success_rate']:.1%}\n"
            rag_enhancement += f"- 相似成功任务: {insights['similar_successful_tasks']} 个\n"
            rag_enhancement += f"- 相似失败任务: {insights['similar_failed_tasks']} 个\n\n"
            
            if insights["recommendations"]:
                rag_enhancement += "### 💡 智能建议\n"
                for rec in insights["recommendations"]:
                    rag_enhancement += f"- {rec}\n"
                rag_enhancement += "\n"
            
        
        #添加操作指南
        if markdown_knowledge:
            rag_enhancement += "### 📖 操作指南\n"
            for i, chunk in enumerate(markdown_knowledge[:2], 1):  # 只显示前2个
                rag_enhancement += f"**知识 {i}**:\n"
                rag_enhancement += f"- 标题: {chunk.get('title')}\n"
                rag_enhancement += f"- 内容: {chunk.get('content')}\n"
                rag_enhancement += "\n"

        # 添加相似任务经验
        if similar_tasks:
            rag_enhancement += "### 🎯 相似成功任务经验\n"
            for i, task in enumerate(similar_tasks[:2], 1):  # 只显示前2个
                rag_enhancement += f"**任务 {i}** (相似度: {task.similarity_score:.2f}):\n"
                rag_enhancement += f"- 目标: {task.task_goal}\n"
                rag_enhancement += f"- 步骤数: {task.total_steps}\n"
                thought_score_pairs = []
                thoughts = task.thoughts
                action_usefulness = task.action_usefulness
                for i, (thought, usefulness) in enumerate(zip(thoughts, action_usefulness)):
                    if isinstance(usefulness, dict):
                        score = usefulness.get('score', 0.0)
                    else:
                        score = usefulness.score if hasattr(usefulness, 'score') else 0.0
                    
                    thought_score_pairs.append({
                        'step': i + 1,
                        'thought': thought,
                        'score': score
                    })
                high_score_thoughts = [
                    pair['thought'] for pair in thought_score_pairs 
                    if pair['score'] >= 0.6
                ]
                rag_enhancement += f"- 关键思路: {high_score_thoughts}\n"
                rag_enhancement += "\n"
        
        
        # 添加进化学习指导
        rag_enhancement += "### 🔄 进化学习指导\n"
        rag_enhancement += "基于历史经验，请:\n"
        rag_enhancement += "1. 如果遇到困难，尝试参考相似任务的成功路径\n"
        rag_enhancement += "2. 记录关键决策点，便于后续学习\n"
        rag_enhancement += "3. 在操作过程中思考如何优化当前策略\n\n"
        
        return base_prompt + rag_enhancement
    
    def run_rag_enhanced_goal(self, goal) -> Tuple[Dict, bool, int]:
        """
        运行RAG增强的目标执行
        
        Args:
            goal: 任务目标
            
        Returns:
            Tuple[AI响应, 是否成功, 总token数]
        """
        print(f"🎯 开始RAG增强执行: {goal}")
        
        # 初始化任务跟踪
        self.task_start_time = time.time()
        self.current_screenshots = []
        self.current_actions = []
        self.current_thoughts = []
        self.current_actions_usefulness = []
        
        self.current_step = 0
        action_message = None
        self.total_token = 0
        
        while self.current_step < self.max_steps:
            self.current_step += 1
            print(f"🔄 执行步骤 {self.current_step}/{self.max_steps}")
            
            try:
                # 截图
                screenshot_path = f"screenshot/screenshot_{int(time.time())}.png"
                image = self.capture_screenshot(screenshot_path)
                self.current_screenshots.append(screenshot_path)
                
            except Exception as e:
                print(f"截图失败: {e}")
                continue
            
            # AI分析并规划下一步（使用RAG增强）
            try:
                if not action_message:
                    action_message = self.construct_rag_enhanced_messages(
                        instruction=goal, image_base64=image
                    )
                else:
                    # 维护对话历史
                    if len(action_message) > 4:
                        action_message = [action_message[0]] + action_message[-2:]
                    
                    action_message.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image}"
                                }
                            }
                        ]
                    })
                ai_response, token = self.inference(messages=action_message)
                # print(action_message)
                self.total_token += token
                
                # 记录思考过程
                thought = ai_response.get('thought', '')
                self.current_thoughts.append(thought)
                self.current_actions_usefulness.append({
                    "score": ai_response.get("action_usefulness").get("score", 0.0),
                    "reason": ai_response.get("action_usefulness").get("reasoning", "")
                })
                
                print(f"🧠 AI思考: {thought}")
                print(f"⚡ AI建议: {ai_response.get('action', '无')}")
                print(f"上一步操作置信度：{ai_response.get('action_usefulness','未知')}")
                print(f"🔤 使用token: {token}")
                
                action_message.append({
                    "role": "assistant",
                    "content": thought
                })
                
                if not ai_response:
                    print("AI分析失败")
                    continue
                    
            except Exception as e:
                print(f"AI分析失败: {e}")
                continue
            
            # 执行AI建议
            try:
                action_info = parse_action_string(ai_response.get("action"))
                if action_info:
                    # 记录操作
                    self.current_actions.append({
                        'step': self.current_step,
                        'action': ai_response.get("action"),
                        'action_info': action_info,
                        'timestamp': time.time()
                    })
                    if action_info.get("action_type") == "creategroup":
                        try:
                            task = {
                                "task": f"添加‘测试’群组",
                                "prerequisites": "",
                                "steps": "1. 进入通讯录 2. 点击我的群组 3. 点击右上方创建群组 4. 输入群名称‘测试’ 5. 点击创建",
                                "expected_result": "1. 群组创建成功"
                            }
                            _,_,token = self.run_rag_enhanced_goal(task)
                            self.total_token += token
                        except Exception as e:
                            print(f"❌ 创建群组执行失败: {e}")
                    elif action_info.get("action_type") == "createfile":
                        try:
                            task = {
                                "task": f"创建‘测试’云文档",
                                "prerequisites": "",
                                "steps": "1. 进入云文档 2. 点击新建 3. 选择文档 4. 输入文档标题‘测试’",
                                "expected_result": "1. 文档创建成功"
                            }
                            _,_,token = self.run_rag_enhanced_goal(task)
                            self.total_token += token
                        except Exception as e:
                            print(f"❌ 创建文件执行失败: {e}")
                    else:
                        message = self.action_executor.execute_parsed_action(action_info)
                        print(f"✅ 执行成功: {message}")
                    time.sleep(2)
                    
                    if action_info.get("action_type") == "finished":
                        # 任务完成，保存到知识库
                        self._save_successful_experience(goal, ai_response)
                        return ai_response, True, self.total_token
                else:
                    print("❌ 执行失败: 无法解析操作")
                    
            except Exception as e:
                print(f"❌ 执行失败: {e}")
                continue
        
        # 记录任务失败
        self.record_task_failure()
        
        # 任务失败，保存失败经验
        self._save_failed_experience(goal, "达到最大步骤数限制")
        print(f"❌ 达到最大步骤数 {self.max_steps}，目标未完成")
        return ai_response, False, self.total_token
    
    def _save_successful_experience(self, goal, final_response):
        """保存成功经验到知识库"""
        self.current_actions_usefulness = self.current_actions_usefulness[1:]
        self.current_actions_usefulness.append({"score": 1.0, "reason": "完成该操作可使任务完成"})
        try:
            task_id = self.knowledge_base.add_task_experience(
                task_description=str(goal),
                task_goal=f"任务完成: {final_response.get('thought', '')}",
                success=True,
                total_steps=self.current_step,
                total_tokens=self.total_token,
                screenshots=self.current_screenshots,
                actions=self.current_actions,
                thoughts=self.current_thoughts,
                action_usefulness=self.current_actions_usefulness
            )
            
            # 保存截图知识
            self._save_screenshot_knowledge(goal, success=True)
            # self.knowledge_base.save_knowledge()
            print(f"💾 成功经验已保存到知识库 (任务ID: {task_id})")
            
        except Exception as e:
            print(f"❌ 保存成功经验失败: {e}")
    
    def _save_failed_experience(self, goal, error_message):
        """保存失败经验到知识库"""
        try:
            task_id = self.knowledge_base.add_task_experience(
                task_description=str(goal),
                task_goal="任务失败",
                success=False,
                total_steps=self.current_step,
                total_tokens=self.total_token,
                screenshots=self.current_screenshots,
                actions=self.current_actions,
                thoughts=self.current_thoughts,
                error_message=error_message
            )
            
            # 保存截图知识
            self._save_screenshot_knowledge(goal, success=False)
            # self.knowledge_base.save_knowledge()
            print(f"💾 失败经验已保存到知识库 (任务ID: {task_id})")
            
        except Exception as e:
            print(f"❌ 保存失败经验失败: {e}")
    
    def _save_screenshot_knowledge(self, goal, success: bool):
        """保存截图知识到知识库"""
        try:
            if not self.current_screenshots:
                return
            
            # 为每个截图创建知识条目
            for i, screenshot_path in enumerate(self.current_screenshots):
                if not os.path.exists(screenshot_path):
                    continue
                
                # 读取截图
                with open(screenshot_path, 'rb') as f:
                    screenshot_data = f.read()
                    screenshot_base64 = base64.b64encode(screenshot_data).decode()
                
                # 获取对应的操作
                step_actions = [a for a in self.current_actions if a['step'] == i + 1]
                successful_actions = step_actions if success else []
                failed_actions = [] if success else step_actions
                
                # 生成相似性标签
                similarity_tags = self._generate_similarity_tags(goal, i)
                
                # 生成UI元素描述
                ui_elements = self._analyze_ui_elements(screenshot_path)
                
                self.knowledge_base.add_screenshot_knowledge(
                    screenshot_path=screenshot_path,
                    screenshot_base64=screenshot_base64,
                    task_context=str(goal),
                    successful_actions=successful_actions,
                    failed_actions=failed_actions,
                    ui_elements=ui_elements,
                    similarity_tags=similarity_tags
                )
                
        except Exception as e:
            print(f"❌ 保存截图知识失败: {e}")
    
    def _generate_similarity_tags(self, goal, step_index: int) -> List[str]:
        """生成相似性标签"""
        tags = []
        goal_str = str(goal).lower()
        
        # 基于任务描述生成标签
        if '飞书' in goal_str:
            tags.append('飞书')
        if '文档' in goal_str:
            tags.append('文档操作')
        if '分享' in goal_str:
            tags.append('分享功能')
        if '搜索' in goal_str:
            tags.append('搜索功能')
        if '消息' in goal_str:
            tags.append('消息功能')
        if '云文档' in goal_str:
            tags.append('云文档')
        
        # 基于步骤生成标签
        if step_index == 0:
            tags.append('初始状态')
        elif step_index == len(self.current_screenshots) - 1:
            tags.append('最终状态')
        else:
            tags.append(f'步骤{step_index + 1}')
        
        return tags
    
    def _analyze_ui_elements(self, screenshot_path: str) -> Dict[str, Any]:
        """分析UI元素（简化版本）"""
        try:
            with Image.open(screenshot_path) as img:
                width, height = img.size
                
                return {
                    "resolution": f"{width}x{height}",
                    "aspect_ratio": f"{width/height:.2f}",
                    "estimated_ui_type": "desktop_application" if width > 1000 else "mobile_application"
                }
        except Exception:
            return {"error": "无法分析截图"}
    
    def get_knowledge_insights(self, task_description: str) -> Dict[str, Any]:
        """获取知识库洞察"""
        return self.knowledge_base.get_learning_insights(task_description)
    
    def search_similar_successful_tasks(self, task_description: str, top_k: int = 5):
        """搜索相似的成功任务"""
        return self.knowledge_base.search_similar_tasks(
            task_description, top_k=top_k, only_successful=True
        )
    
    def print_knowledge_statistics(self):
        """打印知识库统计信息"""
        stats = self.knowledge_base.get_statistics()
        print("\n📊 知识库统计信息:")
        print(f"  总任务数: {stats['total_tasks']}")
        print(f"  成功任务: {stats['successful_tasks']}")
        print(f"  失败任务: {stats['failed_tasks']}")
        print(f"  成功率: {stats['success_rate']:.1%}")
        print(f"  截图知识: {stats['total_screenshots']} 条")
        print(f"  知识库大小: {stats['knowledge_base_size_mb']:.2f} MB")
        print(f"  任务总检索次数: {stats['task_usage_count']}")
        print(f"  任务失败次数: {stats['task_failure_count']}")
        print(f"  任务失败率: {stats['task_failure_rate']:.1%}")
        print(f"  截图总检索次数: {stats['screenshot_usage_count']}")
        print(f"  截图失败次数: {stats['screenshot_failure_count']}")
        print(f"  截图失败率: {stats['screenshot_failure_rate']:.1%}")
        
        # 显示最常使用的任务
        if stats['most_used_tasks']:
            print("\n🏆 最常使用的任务:")
            for task in stats['most_used_tasks']:
                print(f"  {task['task_id']}: {task['description']} (使用{task['usage_count']}次)")
        
        # 显示失败率最高的任务
        if stats['most_failed_tasks']:
            print("\n❌ 失败率最高的任务:")
            for task in stats['most_failed_tasks']:
                print(f"  {task['task_id']}: {task['description']} (失败{task['failure_count']}次)")
        
        # 显示最常使用的截图
        if stats['most_used_screenshots']:
            print("\n🖼️ 最常使用的截图:")
            for screenshot in stats['most_used_screenshots']:
                print(f"  {screenshot['screenshot_id']}: {screenshot['context']} (使用{screenshot['usage_count']}次)")
        
        # 显示失败率最高的截图
        if stats['most_failed_screenshots']:
            print("\n❌ 失败率最高的截图:")
            for screenshot in stats['most_failed_screenshots']:
                print(f"  {screenshot['screenshot_id']}: {screenshot['context']} (失败{screenshot['failure_count']}次)")
    
    def clean_low_usage_knowledge(self, 
                                 usage_threshold: float = 0.2, 
                                 min_usage_count: int = 1,
                                 max_failure_rate: float = 0.8,  # 新增：最大失败率阈值
                                 experience_type: str = "all") -> Dict[str, int]:
        """
        清除使用率低的知识
        
        Args:
            usage_threshold: 使用率阈值 (0.0-1.0)，低于此值的数据将被删除
            min_usage_count: 最小使用次数，低于此值的数据将被删除
            max_failure_rate: 最大失败率阈值 (0.0-1.0)，高于此值的数据将被删除
            experience_type: 要清理的经验类型 ("tasks", "screenshots", "all")
            
        Returns:
            删除统计信息
        """
        print(f"🧹 开始清理使用率低的知识 (阈值: {usage_threshold}, 最小次数: {min_usage_count}, 最大失败率: {max_failure_rate})")
        return self.knowledge_base.clean_low_usage_data(
            usage_threshold=usage_threshold,
            min_usage_count=min_usage_count,
            max_failure_rate=max_failure_rate,
            experience_type=experience_type
        )
    
    def record_task_failure(self):
        """
        记录当前任务执行失败，更新检索到的知识的失败计数
        """
        updated_count = self.knowledge_base.record_task_failure()
        if updated_count > 0:
            print(f"已记录任务失败，更新了 {updated_count} 条知识的失败计数")
        return updated_count
    
    def get_all_md_files(self) -> List[Dict[str, Any]]:
        """
        获取知识库中所有Markdown文件的列表
        
        Returns:
            包含文件信息的字典列表，每个字典包含file_name、source和chunk_count
        """
        if self.md_knowledge_base:
            return self.md_knowledge_base.get_all_markdown_files()
        return []
    
    def delete_md_file(self, file_name: str) -> Dict[str, Any]:
        """
        从知识库中删除指定文件名的所有Markdown文件数据
        
        Args:
            file_name: 要删除的文件名
            
        Returns:
            包含删除结果信息的字典
        """
        if self.md_knowledge_base:
            return self.md_knowledge_base.delete_markdown_file(file_name)
        return {"success": False, "error": "Markdown知识库未初始化"}