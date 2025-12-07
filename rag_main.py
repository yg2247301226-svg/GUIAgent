"""
RAG增强的GUI自动化主程序
演示如何使用RAG技术实现进化式自动化操作
"""

import time
from rag_enhanced_agent import RAGEnhancedGUIAgent


def main():
    """主函数"""
    # 初始化RAG增强的GUI智能体
    api_key = "9dc1016e-8562-42e4-addb-4bdf30d8152c"
    agent = RAGEnhancedGUIAgent(api_key=api_key, knowledge_dir="knowledge_base")
    
    # 打印知识库统计
    agent.print_knowledge_statistics()
    
    # 测试任务列表
    test_tasks = [
        {
            "task": "发送一条简单的飞书消息",
            "prerequisites": "已登录飞书并打开聊天界面",
            "steps": "1. 选择联系人'杨戈 南京邮电大学 电子信息 26届' 2. 在输入框输入'你好，今天下午的会议别忘了' 3. 点击发送按钮",
            "expected_result": "1. 消息成功发送"
        }
    ]
    
    print("\n🚀 开始RAG增强的GUI自动化测试")
    print("=" * 60)
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n📋 执行任务 {i}: {task['task']}")
        print("-" * 40)
        
        # 获取知识库洞察
        insights = agent.get_knowledge_insights(task['task'])
        print(f"🧠 知识库洞察:")
        print(f"  相似任务成功率: {insights['success_rate']:.1%}")
        print(f"  建议数量: {len(insights['recommendations'])}")
        
        if insights['recommendations']:
            print("  💡 智能建议:")
            for rec in insights['recommendations']:
                print(f"    - {rec}")
        
        # 搜索相似的成功任务
        similar_tasks = agent.search_similar_successful_tasks(task['task'], top_k=2)
        if similar_tasks:
            print("  🎯 相似成功任务:")
            for j, similar_task in enumerate(similar_tasks, 1):
                print(f"    {j}. 相似度: {similar_task.similarity_score:.2f}, "
                      f"步骤: {similar_task.total_steps}")
        
        print(f"\n⏱️  开始执行任务...")
        start_time = time.time()
        
        try:
            # 执行任务
            response, success, total_token = agent.run_rag_enhanced_goal(task)
            
            execution_time = time.time() - start_time
            
            print(f"\n📊 执行结果:")
            print(f"  成功: {'✅ 是' if success else '❌ 否'}")
            print(f"  执行时间: {execution_time:.1f} 秒")
            print(f"  总步骤数: {agent.current_step}")
            print(f"  使用token: {total_token}")
            
            if success:
                print(f"  完成信息: {response.get('thought', '无')}")
            else:
                print(f"  失败原因: 达到最大步骤限制")
            
        except Exception as e:
            print(f"❌ 任务执行异常: {e}")
        
        # 询问是否继续
        if i < len(test_tasks):
            print(f"\n⏳ 等待3秒后执行下一个任务...")
            time.sleep(3)
    
    print("\n🎉 所有任务执行完成!")
    
    # 最终统计
    print("\n" + "=" * 60)
    agent.print_knowledge_statistics()
    print("=" * 60)


def interactive_mode():
    """交互式模式"""
    api_key = "6c08cf37-b093-4bae-a993-0e33fc3a1805"
    agent = RAGEnhancedGUIAgent(api_key=api_key, knowledge_dir="knowledge_base")
    
    print("🤖 RAG增强GUI自动化交互模式")
    print("输入 'quit' 退出，输入 'stats' 查看知识库统计")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n🎯 请输入任务描述: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'stats':
                agent.print_knowledge_statistics()
                continue
            elif not user_input:
                continue
            
            # 获取知识库洞察
            insights = agent.get_knowledge_insights(user_input)
            print(f"\n🧠 知识库分析:")
            print(f"  相似任务成功率: {insights['success_rate']:.1%}")
            
            if insights['recommendations']:
                print("  💡 建议:")
                for rec in insights['recommendations']:
                    print(f"    - {rec}")
            
            # 执行任务
            print(f"\n⚡ 开始执行...")
            start_time = time.time()
            
            response, success, total_token = agent.run_rag_enhanced_goal(user_input)
            
            execution_time = time.time() - start_time
            
            print(f"\n📊 结果:")
            print(f"  {'✅ 成功' if success else '❌ 失败'}")
            print(f"  时间: {execution_time:.1f}s, 步骤: {agent.current_step}, Token: {total_token}")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    print("选择运行模式:")
    print("1. 自动测试模式")
    print("2. 交互模式")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "2":
        interactive_mode()
    else:
        main()