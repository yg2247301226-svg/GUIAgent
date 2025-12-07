import re
from typing import List, Dict, Any, Optional
import os
import json
import chromadb
from chromadb.config import Settings
import tiktoken
import openai
from openai import OpenAI

class OpenAIMarkdownVectorDB:
    """使用纯OpenAI API的Markdown向量数据库"""
    
    def __init__(self, 
                 persist_directory: str = "./openai_markdown_db",
                 embedding_model: str = "text-embedding-v4",
                 api_key: Optional[str] = None):
        
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.api_key = api_key or "sk-1b79273a7a7347349e7ce57275ab0c8c"
        
        if not self.api_key:
            raise ValueError("OpenAI API密钥未提供，请设置OPENAI_API_KEY环境变量或传入api_key参数")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(api_key=self.api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        # 初始化Chroma客户端
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name="markdown_documents",
            metadata={"description": "Markdown文档向量数据库"}
        )
        
        # 初始化tokenizer用于计算token数量
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def get_embedding(self, text: str) -> List[float]:
        """使用OpenAI API获取文本嵌入向量"""
        try:
            # 清理文本
            text = text.replace("\n", " ").strip()
            if len(text) > 8192:  # OpenAI模型的最大token限制
                text = text[:8192]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"获取嵌入向量失败: {e}")
            # 返回零向量作为fallback
            return [0.0] * 1536  # text-embedding-3-small的维度
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.encoding.encode(text))
    
    def split_markdown_content(self, md_content: str) -> List[Dict[str, Any]]:
        """分割Markdown内容为块"""
        lines = md_content.split('\n')
        chunks = []
        current_chunk = []
        current_title = ""
        
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        ordered_list_pattern = re.compile(r'^\s*\d+\.\s')
        qa_question_pattern = re.compile(r'^-\s+\*\*Q:')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 检查标题
            heading_match = heading_pattern.match(lines[i])
            if heading_match:
                if current_chunk:
                    chunks.append({
                        "title": current_title,
                        "content": "\n".join(current_chunk).strip(),
                        "token_count": self.count_tokens("\n".join(current_chunk).strip())
                    })
                    current_chunk = []
                
                current_title = heading_match.group(2).strip()
                current_chunk = [lines[i]]
                i += 1
                continue
            
            # 检查有序列表
            if ordered_list_pattern.match(lines[i]):
                if current_chunk:
                    chunks.append({
                        "title": current_title,
                        "content": "\n".join(current_chunk).strip(),
                        "token_count": self.count_tokens("\n".join(current_chunk).strip())
                    })
                
                list_match = re.match(r'^\s*(\d+\.\s+.+)$', lines[i])
                if list_match:
                    current_title = f"**{list_match.group(1).strip()}**"
                    current_chunk = [lines[i]]
                i += 1
                continue
            
            # 检查Q&A问题
            if qa_question_pattern.match(lines[i]):
                if current_chunk:
                    chunks.append({
                        "title": current_title,
                        "content": "\n".join(current_chunk).strip(),
                        "token_count": self.count_tokens("\n".join(current_chunk).strip())
                    })
                
                question_match = re.match(r'^-\s+\*\*(Q:.+)$', lines[i])
                if question_match:
                    current_title = f"- {question_match.group(1).strip()}"
                    current_chunk = [lines[i]]
                i += 1
                continue
            
            if not line and not current_chunk:
                i += 1
                continue
            
            current_chunk.append(lines[i])
            i += 1
        
        if current_chunk:
            chunks.append({
                "title": current_title,
                "content": "\n".join(current_chunk).strip(),
                "token_count": self.count_tokens("\n".join(current_chunk).strip())
            })
        
        return chunks
    
    def read_markdown_file(self, file_path: str) -> str:
        """读取Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read()
    
    def add_markdown_file(self, file_path: str) -> Dict[str, Any]:
        """添加Markdown文件到向量数据库"""
        if not os.path.exists(file_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        try:
            content = self.read_markdown_file(file_path)
            chunks = self.split_markdown_content(content)
            
            if not chunks:
                return {"success": False, "error": "文件内容为空或无法分块"}
            
            # 准备数据
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{os.path.basename(file_path)}_{i}"
                
                # 获取嵌入向量
                embedding = self.get_embedding(chunk['content'])
                
                documents.append(chunk['content'])
                metadatas.append({
                    "title": chunk['title'],
                    "source": file_path,
                    "chunk_id": i,
                    "token_count": chunk['token_count'],
                    "file_name": os.path.basename(file_path)
                })
                ids.append(chunk_id)
                embeddings.append(embedding)
            
            # 添加到向量数据库
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            total_tokens = sum(chunk['token_count'] for chunk in chunks)
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "total_tokens": total_tokens,
                "file_name": os.path.basename(file_path)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_similar(self, 
                      query: str, 
                      n_results: int = 5,
                      similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """语义相似度搜索"""
        try:
            # 获取查询的嵌入向量
            query_embedding = self.get_embedding(query)
            # 在向量数据库中搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    similarity = 1 - distance  # 将距离转换为相似度
                    
                    if similarity >= similarity_threshold:
                        formatted_results.append({
                            "content": doc,
                            "title": metadata.get("title", ""),
                            "source": metadata.get("source", ""),
                            "similarity": similarity,
                            "distance": distance,
                            "metadata": metadata
                        })
            # 按相似度排序
            formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return formatted_results
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def batch_add_files(self, directory_path: str) -> Dict[str, Any]:
        """批量添加目录下的所有Markdown文件"""
        if not os.path.exists(directory_path):
            return {"success": False, "error": f"目录不存在: {directory_path}"}
        
        md_files = []
        for file_name in os.listdir(directory_path):
            if file_name.endswith('.md'):
                md_files.append(os.path.join(directory_path, file_name))
        
        if not md_files:
            return {"success": False, "error": "目录下未找到Markdown文件"}
        
        results = {
            "total_files": len(md_files),
            "successful_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "file_results": []
        }
        
        for md_file in md_files:
            print(f"处理文件: {os.path.basename(md_file)}")
            result = self.add_markdown_file(md_file)
            
            if result['success']:
                results['successful_files'] += 1
                results['total_chunks'] += result['chunks_processed']
                results['file_results'].append({
                    "file": os.path.basename(md_file),
                    "status": "success",
                    "chunks": result['chunks_processed']
                })
            else:
                results['failed_files'] += 1
                results['file_results'].append({
                    "file": os.path.basename(md_file),
                    "status": "failed",
                    "error": result['error']
                })
        
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            return {"error": f"获取统计信息失败: {e}"}
    
    def get_all_markdown_files(self) -> List[Dict[str, Any]]:
        """获取向量数据库中所有Markdown文件的列表"""
        try:
            # 获取集合中的所有数据
            all_data = self.collection.get(include=["metadatas", "documents"])
            
            if not all_data or not all_data['metadatas']:
                return []
            
            # 提取唯一的文件信息
            unique_files = {}
            for metadata in all_data['metadatas']:
                file_name = metadata.get("file_name", "")
                source = metadata.get("source", "")
                
                if file_name and file_name not in unique_files:
                    unique_files[file_name] = {
                        "file_name": file_name,
                        "source": source,
                        "chunk_count": 0
                    }
                
                if file_name in unique_files:
                    unique_files[file_name]["chunk_count"] += 1
            
            # 转换为列表
            files_list = list(unique_files.values())
            
            # 按文件名排序
            files_list.sort(key=lambda x: x["file_name"])
            
            return files_list
            
        except Exception as e:
            print(f"获取Markdown文件列表失败: {e}")
            return []
    
    def delete_markdown_file(self, file_name: str) -> Dict[str, Any]:
        """从向量数据库中删除指定文件名的所有数据块"""
        try:
            # 获取集合中的所有数据
            all_data = self.collection.get(include=["metadatas", "ids"])
            
            if not all_data or not all_data['metadatas']:
                return {"success": False, "error": "数据库中没有数据"}
            
            # 找出要删除的ID
            ids_to_delete = []
            for i, metadata in enumerate(all_data['metadatas']):
                if metadata.get("file_name") == file_name:
                    ids_to_delete.append(all_data['ids'][i])
            
            if not ids_to_delete:
                return {"success": False, "error": f"未找到文件: {file_name}"}
            
            # 删除数据
            self.collection.delete(ids=ids_to_delete)
            
            return {
                "success": True,
                "deleted_chunks": len(ids_to_delete),
                "file_name": file_name
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_connection(self) -> bool:
        """测试OpenAI连接"""
        try:
            # 简单的测试查询
            test_embedding = self.get_embedding("测试连接")
            return len(test_embedding) > 0
        except Exception as e:
            print(f"OpenAI连接测试失败: {e}")
            return False

class MarkdownKnowledgeRetriever:
    """Markdown知识检索器"""
    
    def __init__(self, vector_db: OpenAIMarkdownVectorDB):
        self.vector_db = vector_db
    
    def query(self, 
             question: str, 
             max_results: int = 3,
             min_similarity: float = 0.4) -> Dict[str, Any]:
        """查询相关知识"""
        results = self.vector_db.search_similar(question, max_results, min_similarity)
        
        return {
            "question": question,
            "results_found": len(results),
            "min_similarity": min_similarity,
            "results": results
        }
    
    def get_context(self, question: str, max_tokens: int = 2000) -> str:
        """获取问题的上下文内容"""
        results = self.vector_db.search_similar(question, n_results=5, similarity_threshold=0.6)
        
        context_parts = []
        current_tokens = 0
        
        for result in results:
            content = f"标题: {result['title']}\n内容: {result['content']}"
            content_tokens = self.vector_db.count_tokens(content)
            
            if current_tokens + content_tokens <= max_tokens:
                context_parts.append(content)
                current_tokens += content_tokens
            else:
                break
        
        return "\n\n".join(context_parts)

def main():
    """主函数示例"""
    
    # 设置OpenAI API密钥
    api_key = "sk-1b79273a7a7347349e7ce57275ab0c8c"  # 替换为您的实际API密钥
    
    # 初始化向量数据库
    print("初始化OpenAI向量数据库...")
    vector_db = OpenAIMarkdownVectorDB(
        persist_directory="./openai_markdown_db",
        api_key=api_key
    )
    
    # 测试连接
    if not vector_db.test_connection():
        print("❌ OpenAI连接失败，请检查API密钥和网络连接")
        return
    
    print("✅ OpenAI连接成功")
    
    # 处理Markdown文件
    md_file_path = "C:\\Users\\22473\\Desktop\\训练营\\GUIAgent_tars1\\knowledge_base\\飞书云文档插入表格.md"
    
    print(f"处理文件: {md_file_path}")
    result = vector_db.add_markdown_file(md_file_path)
    
    if result['success']:
        print(f"✅ 文件处理成功，生成 {result['chunks_processed']} 个知识块")
        print(f"📊 总token数量: {result['total_tokens']}")
    else:
        print(f"❌ 文件处理失败: {result['error']}")
        return
    
    # 显示数据库统计
    stats = vector_db.get_collection_stats()
    print(f"数据库统计: {stats}")
    
    # 测试搜索
    print("\n" + "="*60)
    print("语义搜索测试")
    print("="*60)
    
    test_queries = [
        "如何在飞书云文档中插入表格",
        "表格的基本操作",
        "Markdown表格语法"
    ]
    
    retriever = MarkdownKnowledgeRetriever(vector_db)
    
    for query in test_queries:
        print(f"\n🔍 搜索: '{query}'")
        response = retriever.query(query, min_similarity=0.4)
        
        if response['results_found'] > 0:
            print(f"找到 {response['results_found']} 个相关结果:")
            for i, result in enumerate(response['results'], 1):
                print(f"{i}. 【{result['title']}】")
                print(f"   相似度: {result['similarity']:.3f}")
                print(f"   内容预览: {result['content'][:100]}...")
        else:
            print("未找到相关结果")

def interactive_search():
    """交互式搜索界面"""
    api_key = "sk-1b79273a7a7347349e7ce57275ab0c8c"  # 替换为您的实际API密钥
    
    vector_db = OpenAIMarkdownVectorDB(api_key=api_key)
    retriever = MarkdownKnowledgeRetriever(vector_db)
    
    print("\n🤖 OpenAI知识检索系统")
    print("输入问题进行搜索（输入'退出'结束）")
    
    while True:
        try:
            question = input("\n💬 请输入问题: ").strip()
            if question.lower() in ['退出', 'exit', 'quit']:
                break
            
            if not question:
                continue
            
            print("🔍 搜索中...")
            response = retriever.query(question, min_similarity=0.4)
            
            if response['results_found'] > 0:
                print(f"\n✅ 找到 {response['results_found']} 个相关知识点:")
                for i, result in enumerate(response['results'], 1):
                    print(f"\n{i}. 【{result['title']}】")
                    print(f"   相似度: {result['similarity']:.3f}")
                    print(f"   来源: {result['source']}")
                    print(f"   内容: {result['content'][:150]}...")
            else:
                print("❌ 未找到相关知识点")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

# if __name__ == "__main__":
    # 运行主示例
    # main()
    
    # 运行交互式搜索（取消注释使用）
    # interactive_search()
    
    # 批量处理示例（取消注释使用）
    # vector_db = OpenAIMarkdownVectorDB(api_key="您的API密钥")
    # batch_result = vector_db.batch_add_files("C:\\path\\to\\your\\markdown\\directory")
    # print("批量处理结果:", json.dumps(batch_result, indent=2, ensure_ascii=False))