"""
RAG知识库模块
用于存储和管理截图知识库和操作经验知识库
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from PIL import Image
import base64
import io
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle


@dataclass
class TaskExperience:
    """任务经验数据结构"""
    task_id: str
    task_description: str
    task_goal: str
    success: bool
    total_steps: int
    total_tokens: int
    screenshots: List[str]  # 截图路径列表
    actions: List[Dict]  # 操作序列
    thoughts: List[str]  # 思考过程
    action_usefulness: List[Dict] = None  # 新增：操作有用性评估
    error_message: Optional[str] = None
    similarity_score: Optional[float] = None
    usage_count: int = 0  # 新增：记录被检索使用的次数
    failure_count: int = 0  # 新增：记录检索使用但任务失败的次数
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.action_usefulness is None:
            self.action_usefulness = []
        if self.usage_count is None:
            self.usage_count = 0
        if self.failure_count is None:
            self.failure_count = 0


@dataclass
class ScreenshotKnowledge:
    """截图知识数据结构"""
    screenshot_id: str
    screenshot_path: str
    screenshot_base64: str
    task_context: str  # 任务上下文描述
    successful_actions: List[Dict]  # 在此截图下成功的操作
    failed_actions: List[Dict]  # 在此截图下失败的操作
    ui_elements: Dict[str, Any]  # UI元素描述
    similarity_tags: List[str]  # 相似性标签
    usage_count: int = 0  # 新增：记录被检索使用的次数
    failure_count: int = 0  # 新增：记录检索使用但任务失败的次数
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.usage_count is None:
            self.usage_count = 0
        if self.failure_count is None:
            self.failure_count = 0


class RAGKnowledgeBase:
    """RAG知识库管理器"""
    
    def __init__(self, knowledge_dir: str = "knowledge_base"):
        self.knowledge_dir = knowledge_dir
        self.experience_file = os.path.join(knowledge_dir, "task_experiences.json")
        self.screenshot_file = os.path.join(knowledge_dir, "screenshot_knowledge.json")
        self.vectorizer_file = os.path.join(knowledge_dir, "tfidf_vectorizer.pkl")
        self.matrix_file = os.path.join(knowledge_dir, "similarity_matrix.pkl")
        
        # 创建知识库目录
        os.makedirs(knowledge_dir, exist_ok=True)
        
        # 初始化数据存储
        self.task_experiences: List[TaskExperience] = []
        self.screenshot_knowledge: List[ScreenshotKnowledge] = []
        
        # 向量化工具
        self.vectorizer = None
        self.similarity_matrix = None
        
        # 加载已有数据
        self.load_knowledge()
        
    def load_knowledge(self):
        """加载已有知识库数据"""
        try:
            # 加载任务经验
            if os.path.exists(self.experience_file):
                with open(self.experience_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.task_experiences = [TaskExperience(**item) for item in data]
                    print(f"✅ 加载了 {len(self.task_experiences)} 条任务经验")
            
            # 加载截图知识
            if os.path.exists(self.screenshot_file):
                with open(self.screenshot_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.screenshot_knowledge = [ScreenshotKnowledge(**item) for item in data]
                    print(f"✅ 加载了 {len(self.screenshot_knowledge)} 条截图知识")
            
            # 加载向量化数据
            if os.path.exists(self.vectorizer_file) and os.path.exists(self.matrix_file):
                with open(self.vectorizer_file, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(self.matrix_file, 'rb') as f:
                    self.similarity_matrix = pickle.load(f)
                print("✅ 加载了向量化数据")
                
        except Exception as e:
            print(f"⚠️ 加载知识库数据时出错: {e}")
    
    def save_knowledge(self):
        """保存知识库数据"""
        try:
            # 保存任务经验
            with open(self.experience_file, 'w', encoding='utf-8') as f:
                data = [asdict(exp) for exp in self.task_experiences]
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存截图知识
            with open(self.screenshot_file, 'w', encoding='utf-8') as f:
                data = [asdict(sk) for sk in self.screenshot_knowledge]
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存向量化数据
            if self.vectorizer is not None:
                with open(self.vectorizer_file, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
            if self.similarity_matrix is not None:
                with open(self.matrix_file, 'wb') as f:
                    pickle.dump(self.similarity_matrix, f)
                    
            print("💾 知识库数据已保存")
            
        except Exception as e:
            print(f"❌ 保存知识库数据时出错: {e}")
    
    def add_task_experience(self, 
                           task_description: str,
                           task_goal: str,
                           success: bool,
                           total_steps: int,
                           total_tokens: int,
                           screenshots: List[str],
                           actions: List[Dict],
                           thoughts: List[str],
                           action_usefulness: List[Dict] = None,  # 新增：操作有用性评估
                           error_message: Optional[str] = None) -> str:
        """添加任务经验"""
        task_id = hashlib.md5(f"{task_description}_{time.time()}".encode()).hexdigest()[:8]
        
        experience = TaskExperience(
            task_id=task_id,
            task_description=task_description,
            task_goal=task_goal,
            success=success,
            total_steps=total_steps,
            total_tokens=total_tokens,
            screenshots=screenshots,
            actions=actions,
            thoughts=thoughts,
            action_usefulness=action_usefulness,  # 新增：操作有用性评估
            error_message=error_message
        )
        
        self.task_experiences.append(experience)
        self.update_vectorization()
        return task_id
    
    def add_screenshot_knowledge(self,
                                screenshot_path: str,
                                screenshot_base64: str,
                                task_context: str,
                                successful_actions: List[Dict],
                                failed_actions: List[Dict],
                                ui_elements: Dict[str, Any],
                                similarity_tags: List[str]) -> str:
        """添加截图知识"""
        screenshot_id = hashlib.md5(f"{screenshot_path}_{time.time()}".encode()).hexdigest()[:8]
        
        knowledge = ScreenshotKnowledge(
            screenshot_id=screenshot_id,
            screenshot_path=screenshot_path,
            screenshot_base64=screenshot_base64,
            task_context=task_context,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            ui_elements=ui_elements,
            similarity_tags=similarity_tags
        )
        
        self.screenshot_knowledge.append(knowledge)
        self.update_vectorization()
        return screenshot_id
    
    def update_vectorization(self):
        """更新向量化数据用于相似性搜索"""
        if not self.task_experiences:
            return
        
        # 准备文本数据
        texts = []
        for exp in self.task_experiences:
            text = f"{exp.task_description} {exp.task_goal} {' '.join(exp.thoughts)}"
            texts.append(text)
        
        # TF-IDF向量化
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2)
        )
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # 计算相似性矩阵
        self.similarity_matrix = cosine_similarity(tfidf_matrix)

        self.save_knowledge()
    
    def search_similar_tasks(self, 
                            current_task: str, 
                            top_k: int = 5,
                            only_successful: bool = False) -> List[TaskExperience]:
        """搜索相似任务"""
        if self.vectorizer is None or self.similarity_matrix is None:
            return []
        
        # 向量化当前任务
        current_vector = self.vectorizer.transform([current_task])
        
        # 计算与所有历史任务的相似性
        similarities = cosine_similarity(current_vector, self.vectorizer.transform([
            f"{exp.task_description} {exp.task_goal}" for exp in self.task_experiences
        ]))[0]
        
        # 获取最相似的任务索引
        similar_indices = np.argsort(similarities)[::-1]
        
        # 记录被检索的经验索引，以便后续更新失败计数
        self._current_retrieved_task_indices = []
        
        results = []
        for idx in similar_indices[:top_k * 2]:  # 取更多候选
            exp = self.task_experiences[idx]
            exp.similarity_score = float(similarities[idx])
            
            # 增加使用计数
            self.task_experiences[idx].usage_count += 1
            # 记录被检索的索引
            self._current_retrieved_task_indices.append(idx)
            
            if only_successful and not exp.success:
                continue
                
            results.append(exp)
            
            if len(results) >= top_k:
                break
        
        # 保存更新后的使用计数
        self.save_knowledge()
        
        return results
    
    def search_similar_screenshots(self, 
                                  current_context: str,
                                  top_k: int = 3) -> List[ScreenshotKnowledge]:
        """搜索相似截图"""
        if not self.screenshot_knowledge:
            return []
        
        # 简单的文本匹配搜索
        results = []
        current_lower = current_context.lower()
        matched_indices = []  # 记录匹配的索引，用于更新使用计数
        
        # 记录被检索的截图索引，以便后续更新失败计数
        self._current_retrieved_screenshot_indices = []
        
        for idx, sk in enumerate(self.screenshot_knowledge):
            # 计算匹配分数
            score = 0
            
            # 任务上下文匹配
            if any(word in sk.task_context.lower() for word in current_lower.split()):
                score += 3
            
            # 标签匹配
            for tag in sk.similarity_tags:
                if tag.lower() in current_lower:
                    score += 2
            
            # UI元素匹配
            for element_type, element_info in sk.ui_elements.items():
                if isinstance(element_info, str) and element_info.lower() in current_lower:
                    score += 1
            
            if score > 0:
                results.append((sk, score))
                matched_indices.append(idx)
                # 记录被检索的索引
                self._current_retrieved_screenshot_indices.append(idx)
        
        # 更新匹配项的使用计数
        for idx in matched_indices:
            self.screenshot_knowledge[idx].usage_count += 1
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        final_results = [sk for sk, _ in results[:top_k]]
        
        # 保存更新后的使用计数
        if matched_indices:
            self.save_knowledge()
        
        return final_results
    
    def get_successful_actions_for_context(self, context: str) -> List[Dict]:
        """根据上下文获取成功操作"""
        similar_screenshots = self.search_similar_screenshots(context)
        successful_actions = []
        
        for sk in similar_screenshots:
            successful_actions.extend(sk.successful_actions)
        
        return successful_actions
    
    def get_failure_patterns(self, context: str) -> List[Dict]:
        """根据上下文获取失败模式"""
        similar_screenshots = self.search_similar_screenshots(context)
        failure_patterns = []
        
        for sk in similar_screenshots:
            failure_patterns.extend(sk.failed_actions)
        
        return failure_patterns
    
    def get_learning_insights(self, current_task: str) -> Dict[str, Any]:
        """获取学习洞察"""
        # 搜索相似任务
        similar_tasks = self.search_similar_tasks(current_task, top_k=5)
        
        # 分析成功和失败模式
        successful_tasks = [t for t in similar_tasks if t.success]
        failed_tasks = [t for t in similar_tasks if not t.success]
        
        insights = {
            "similar_successful_tasks": len(successful_tasks),
            "similar_failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(similar_tasks) if similar_tasks else 0,
            "recommendations": [],
            "common_successful_patterns": [],
            "common_failure_patterns": []
        }
        
        # 提取成功模式
        if successful_tasks:
            # 统计常用操作
            action_counts = {}
            for task in successful_tasks:
                for action in task.actions:
                    action_type = action.get('action_type', 'unknown')
                    action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # 获取最常用的操作类型
            if action_counts:
                common_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                insights["common_successful_patterns"] = [action[0] for action in common_actions]
            else:
                insights["common_successful_patterns"] = []
        
        # 提取失败模式
        if failed_tasks:
            # 统计失败原因
            error_counts = {}
            for task in failed_tasks:
                if task.error_message:
                    error_key = task.error_message  # 取前50个字符作为错误类型
                    error_counts[error_key] = error_counts.get(error_key, 0) + 1
            
            if error_counts:
                common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                insights["common_failure_patterns"] = [error[0] for error in common_errors]
            else:
                insights["common_failure_patterns"] = []
        
        # 生成建议
        if insights["success_rate"] > 0.7:
            insights["recommendations"].append("此类型任务成功率较高，可以参考相似任务的操作模式")
        elif insights["success_rate"] < 0.3:
            insights["recommendations"].append("此类型任务挑战较大，建议先分析失败原因，尝试不同的操作策略")
        
        return insights
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        total_tasks = len(self.task_experiences)
        successful_tasks = len([t for t in self.task_experiences if t.success])
        
        # 统计任务和截图的使用次数和失败次数
        task_usage_count = sum([t.usage_count for t in self.task_experiences])
        task_failure_count = sum([t.failure_count for t in self.task_experiences])
        screenshot_usage_count = sum([s.usage_count for s in self.screenshot_knowledge])
        screenshot_failure_count = sum([s.failure_count for s in self.screenshot_knowledge])
        
        # 获取最常使用的任务和截图
        most_used_tasks = sorted(self.task_experiences, key=lambda x: x.usage_count, reverse=True)[:3]
        most_failed_tasks = sorted(self.task_experiences, key=lambda x: x.failure_count, reverse=True)[:3]
        most_used_screenshots = sorted(self.screenshot_knowledge, key=lambda x: x.usage_count, reverse=True)[:3]
        most_failed_screenshots = sorted(self.screenshot_knowledge, key=lambda x: x.failure_count, reverse=True)[:3]
        
        # 计算失败率
        task_failure_rate = task_failure_count / task_usage_count if task_usage_count > 0 else 0
        screenshot_failure_rate = screenshot_failure_count / screenshot_usage_count if screenshot_usage_count > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": total_tasks - successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "total_screenshots": len(self.screenshot_knowledge),
            "task_usage_count": task_usage_count,  # 新增：任务总使用次数
            "task_failure_count": task_failure_count,  # 新增：任务总失败次数
            "task_failure_rate": task_failure_rate,  # 新增：任务失败率
            "screenshot_usage_count": screenshot_usage_count,  # 新增：截图总使用次数
            "screenshot_failure_count": screenshot_failure_count,  # 新增：截图总失败次数
            "screenshot_failure_rate": screenshot_failure_rate,  # 新增：截图失败率
            "most_used_tasks": [{"task_id": t.task_id, "description": t.task_description[:50] + "...", "usage_count": t.usage_count} for t in most_used_tasks],
            "most_failed_tasks": [{"task_id": t.task_id, "description": t.task_description[:50] + "...", "failure_count": t.failure_count} for t in most_failed_tasks if t.failure_count > 0],
            "most_used_screenshots": [{"screenshot_id": s.screenshot_id, "context": s.task_context[:30] + "...", "usage_count": s.usage_count} for s in most_used_screenshots],
            "most_failed_screenshots": [{"screenshot_id": s.screenshot_id, "context": s.task_context[:30] + "...", "failure_count": s.failure_count} for s in most_failed_screenshots if s.failure_count > 0],
            "knowledge_base_size_mb": self._get_knowledge_base_size()
        }
    
    def _get_knowledge_base_size(self) -> float:
        """获取知识库大小（MB）"""
        total_size = 0
        for file_path in [self.experience_file, self.screenshot_file]:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        return total_size / (1024 * 1024)  # 转换为MB
    
    def clean_low_usage_data(self, 
                           usage_threshold: float = 0.2, 
                           min_usage_count: int = 1,
                           max_failure_rate: float = 0.8,  # 新增：最大失败率阈值
                           experience_type: str = "all") -> Dict[str, int]:
        """
        清除使用率低的数据
        
        Args:
            usage_threshold: 使用率阈值 (0.0-1.0)，低于此值的数据将被删除
            min_usage_count: 最小使用次数，低于此值的数据将被删除
            max_failure_rate: 最大失败率阈值 (0.0-1.0)，高于此值的数据将被删除
            experience_type: 要清理的经验类型 ("tasks", "screenshots", "all")
            
        Returns:
            删除统计信息
        """
        # 计算最大使用次数用于阈值计算
        max_task_usage = max([t.usage_count for t in self.task_experiences], default=0)
        max_screenshot_usage = max([s.usage_count for s in self.screenshot_knowledge], default=0)
        
        # 计算实际阈值（次数或百分比）
        task_threshold = max(int(max_task_usage * usage_threshold), min_usage_count)
        screenshot_threshold = max(int(max_screenshot_usage * usage_threshold), min_usage_count)
        
        stats = {
            "removed_tasks": 0,
            "remaining_tasks": 0,
            "removed_screenshots": 0,
            "remaining_screenshots": 0,
            "removed_for_high_failure_rate": 0  # 新增：因高失败率删除的计数
        }
        
        # 清理任务经验
        if experience_type in ["tasks", "all"]:
            original_count = len(self.task_experiences)
            self.task_experiences = [
                t for t in self.task_experiences 
                if (t.usage_count >= task_threshold and 
                    (t.usage_count == 0 or t.failure_count / t.usage_count <= max_failure_rate))
            ]
            removed_for_failure = sum(1 for t in self.task_experiences if 
                                   t.usage_count > 0 and t.failure_count / t.usage_count > max_failure_rate)
            stats["removed_tasks"] = original_count - len(self.task_experiences)
            stats["remaining_tasks"] = len(self.task_experiences)
            stats["removed_for_high_failure_rate"] += removed_for_failure
        
        # 清理截图知识
        if experience_type in ["screenshots", "all"]:
            original_count = len(self.screenshot_knowledge)
            self.screenshot_knowledge = [
                s for s in self.screenshot_knowledge 
                if (s.usage_count >= screenshot_threshold and 
                    (s.usage_count == 0 or s.failure_count / s.usage_count <= max_failure_rate))
            ]
            removed_for_failure = sum(1 for s in self.screenshot_knowledge if 
                                   s.usage_count > 0 and s.failure_count / s.usage_count > max_failure_rate)
            stats["removed_screenshots"] = original_count - len(self.screenshot_knowledge)
            stats["remaining_screenshots"] = len(self.screenshot_knowledge)
            stats["removed_for_high_failure_rate"] += removed_for_failure
        
        # 更新向量化数据
        if stats["removed_tasks"] > 0:
            self.update_vectorization()
        
        # 保存更新后的知识库
        self.save_knowledge()
        
        print(f"✅ 清理完成: "
              f"删除 {stats['removed_tasks']} 个任务经验, "
              f"删除 {stats['removed_screenshots']} 个截图知识, "
              f"其中 {stats['removed_for_high_failure_rate']} 个因高失败率被删除")
        
        return stats
    
    def record_task_failure(self):
        """记录当前检索到的知识在任务执行中失败"""
        updated_count = 0
        
        # 更新任务经验的失败计数
        if hasattr(self, '_current_retrieved_task_indices'):
            for idx in self._current_retrieved_task_indices:
                if 0 <= idx < len(self.task_experiences):
                    self.task_experiences[idx].failure_count += 1
                    updated_count += 1
        
        # 更新截图知识的失败计数
        if hasattr(self, '_current_retrieved_screenshot_indices'):
            for idx in self._current_retrieved_screenshot_indices:
                if 0 <= idx < len(self.screenshot_knowledge):
                    self.screenshot_knowledge[idx].failure_count += 1
                    updated_count += 1
        
        # 保存更新后的失败计数
        if updated_count > 0:
            self.save_knowledge()
            print(f"已更新 {updated_count} 条知识记录的失败计数")
        
        # 清空当前检索记录
        self._current_retrieved_task_indices = []
        self._current_retrieved_screenshot_indices = []
        
        return updated_count