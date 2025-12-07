"""
RAG增强GUI自动化系统使用示例
展示完整的实际应用场景
"""

import time
import os
from rag_enhanced_agent import RAGEnhancedGUIAgent
from rag_config import RAGConfig, EnvironmentConfig


def example_1_basic_usage():
    """示例1: 基础使用"""
    print("📖 示例1: 基础使用")
    print("-" * 40)
    
    # 初始化智能体
    api_key = "6c08cf37-b093-4bae-a993-0e33fc3a1805"
    agent = RAGEnhancedGUIAgent(api_key=api_key)
    
    # 简单任务
    simple_task = "在飞书中打开搜索功能"
    
    print(f"🎯 执行任务: {simple_task}")
    
    # 获取知识洞察
    insights = agent.get_knowledge_insights(simple_task)
    print(f"🧠 知识库分析: 成功率 {insights['success_rate']:.1%}")
    
    # 执行任务（演示模式，不实际执行）
    print("⚡ 模拟执行...")
    print("✅ 任务完成（演示）")


def example_2_learning_evolution():
    """示例2: 学习进化演示"""
    print("\n📖 示例2: 学习进化演示")
    print("-" * 40)
    
    agent = RAGEnhancedGUIAgent(api_key="6c08cf37-b093-4bae-a993-0e33fc3a1805")
    
    # 模拟一系列相似任务的执行过程
    tasks = [
        {"description": "搜索联系人张三", "success": False, "reason": "搜索词不准确"},
        {"description": "搜索联系人张三", "success": True, "reason": "使用完整姓名"},
        {"description": "搜索联系人李四", "success": True, "reason": "应用成功经验"},
        {"description": "搜索联系人王五", "success": True, "reason": "模式已掌握"},
    ]
    
    print("🔄 模拟任务执行历史:")
    for i, task in enumerate(tasks, 1):
        status = "✅ 成功" if task['success'] else "❌ 失败"
        print(f"  第{i}次: {task['description']} - {status}")
        
        if task['success']:
            # 模拟添加成功经验
            agent.knowledge_base.add_task_experience(
                task_description=task['description'],
                task_goal="成功找到联系人",
                success=True,
                total_steps=3,
                total_tokens=800,
                screenshots=[f"demo_{i}.png"],
                actions=[{"action_type": "click"}, {"action_type": "type"}],
                thoughts=[f"应用搜索模式: {task['reason']}"]
            )
        else:
            # 模拟添加失败经验
            agent.knowledge_base.add_task_experience(
                task_description=task['description'],
                task_goal="搜索失败",
                success=False,
                total_steps=2,
                total_tokens=500,
                screenshots=[f"demo_{i}.png"],
                actions=[{"action_type": "click"}],
                thoughts=[f"搜索失败: {task['reason']}"],
                error_message=task['reason']
            )
    
    # 分析学习效果
    print("\n📊 学习效果分析:")
    insights = agent.get_knowledge_insights("搜索联系人")
    print(f"  最终成功率: {insights['success_rate']:.1%}")
    print(f"  成功模式: {insights['common_successful_patterns']}")
    print(f"  失败模式: {insights['common_failure_patterns']}")
    
    if insights['recommendations']:
        print("  智能建议:")
        for rec in insights['recommendations']:
            print(f"    - {rec}")


def example_3_complex_task():
    """示例3: 复杂任务处理"""
    print("\n📖 示例3: 复杂任务处理")
    print("-" * 40)
    
    agent = RAGEnhancedGUIAgent(api_key="6c08cf37-b093-4bae-a993-0e33fc3a1805")
    
    # 复杂任务定义
    complex_task = {
        "task": "云文档协作：分享技术方案文档给项目组",
        "prerequisites": "已登录飞书，有目标文档和项目组",
        "steps": [
            "1. 打开云文档列表",
            "2. 找到'技术方案'文档",
            "3. 点击分享按钮",
            "4. 选择项目组",
            "5. 设置编辑权限",
            "6. 确认分享"
        ],
        "expected_result": "项目组成员能收到文档并正常编辑"
    }
    
    print(f"🎯 复杂任务: {complex_task['task']}")
    print("📋 任务步骤:")
    for step in complex_task['steps']:
        print(f"  {step}")
    
    # 获取任务分解建议
    insights = agent.get_knowledge_insights(complex_task['task'])
    
    print(f"\n🧠 RAG分析结果:")
    print(f"  相似任务经验: {insights['similar_successful_tasks']} 个成功案例")
    print(f"  预期成功率: {insights['success_rate']:.1%}")
    
    # 模拟执行策略生成
    print(f"\n📋 执行策略:")
    if insights['success_rate'] > 0.5:
        print("  ✅ 建议采用标准流程，有较高成功把握")
    else:
        print("  ⚠️ 建议先进行小规模测试")
    
    if insights['common_successful_patterns']:
        print("  🔄 推荐操作模式:")
        for pattern in insights['common_successful_patterns']:
            print(f"    - 优先使用: {pattern}")
    
    print("⚡ 模拟执行复杂任务...")
    print("✅ 任务完成（演示）")


def example_4_knowledge_management():
    """示例4: 知识库管理"""
    print("\n📖 示例4: 知识库管理")
    print("-" * 40)
    
    agent = RAGEnhancedGUIAgent(api_key="6c08cf37-b093-4bae-a993-0e33fc3a1805")
    
    # 显示知识库状态
    print("📊 当前知识库状态:")
    agent.print_knowledge_statistics()
    
    # 演示知识检索
    print("\n🔍 知识检索演示:")
    
    # 搜索特定类型的任务
    search_queries = [
        "搜索联系人",
        "分享文档", 
        "发送消息",
        "权限管理"
    ]
    
    for query in search_queries:
        similar_tasks = agent.search_similar_successful_tasks(query, top_k=2)
        print(f"  '{query}': 找到 {len(similar_tasks)} 个相似成功任务")
        
        for task in similar_tasks:
            print(f"    - {task.task_description[:30]}... (相似度: {task.similarity_score:.2f})")
    
    # 演示知识库优化建议
    print(f"\n💡 知识库优化建议:")
    stats = agent.knowledge_base.get_statistics()
    
    if stats['success_rate'] < 0.5:
        print("  ⚠️ 整体成功率偏低，建议:")
        print("    - 分析失败模式，优化操作策略")
        print("    - 增加更多成功案例训练")
    
    if stats['total_tasks'] < 10:
        print("  📈 知识库规模较小，建议:")
        print("    - 执行更多样化的任务")
        print("    - 收集不同场景的操作经验")
    
    if stats['knowledge_base_size_mb'] > 100:
        print("  🗄️ 知识库较大，建议:")
        print("    - 定期清理低质量数据")
        print("    - 压缩历史数据")


def example_5_configuration():
    """示例5: 配置管理"""
    print("\n📖 示例5: 配置管理")
    print("-" * 40)
    
    # 显示当前配置
    from rag_config import print_current_config
    print_current_config()
    
    # 演示配置调整
    print(f"\n🔧 演示配置调整:")
    
    # 调整RAG增强参数
    original_rag = RAGConfig.ENABLE_RAG_ENHANCEMENT
    original_steps = RAGConfig.DEFAULT_MAX_STEPS
    
    print(f"  原始RAG增强: {original_rag}")
    print(f"  原始最大步骤: {original_steps}")
    
    # 更新配置
    RAGConfig.update_config({
        "ENABLE_RAG_ENHANCEMENT": False,  # 关闭RAG增强
        "DEFAULT_MAX_STEPS": 15,          # 减少最大步骤
        "DEBUG_MODE": True                 # 开启调试模式
    })
    
    print(f"  ✅ 配置已更新")
    
    # 恢复原始配置
    RAGConfig.update_config({
        "ENABLE_RAG_ENHANCEMENT": original_rag,
        "DEFAULT_MAX_STEPS": original_steps,
        "DEBUG_MODE": False
    })
    
    print(f"  🔄 配置已恢复")


def example_6_error_handling():
    """示例6: 错误处理和恢复"""
    print("\n📖 示例6: 错误处理和恢复")
    print("-" * 40)
    
    agent = RAGEnhancedGUIAgent(api_key="6c08cf37-b093-4bae-a993-0e33fc3a1805")
    
    # 模拟各种错误场景
    error_scenarios = [
        {
            "task": "搜索不存在的联系人",
            "error": "未找到匹配结果",
            "recovery": "尝试模糊搜索或检查输入"
        },
        {
            "task": "分享无权限的文档", 
            "error": "权限不足",
            "recovery": "联系文档所有者申请权限"
        },
        {
            "task": "发送消息给已离职员工",
            "error": "用户不存在",
            "recovery": "更新联系人列表"
        }
    ]
    
    print("🚨 错误场景模拟:")
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n  场景{i}: {scenario['task']}")
        print(f"    ❌ 错误: {scenario['error']}")
        print(f"    💡 恢复策略: {scenario['recovery']}")
        
        # 添加失败经验到知识库
        agent.knowledge_base.add_task_experience(
            task_description=scenario['task'],
            task_goal="任务失败",
            success=False,
            total_steps=2,
            total_tokens=400,
            screenshots=[f"error_demo_{i}.png"],
            actions=[{"action_type": "click"}],
            thoughts=[f"遇到错误: {scenario['error']}"],
            error_message=scenario['error']
        )
    
    # 分析错误模式
    print(f"\n📊 错误模式分析:")
    insights = agent.get_knowledge_insights("错误处理")
    
    if insights['common_failure_patterns']:
        print("  常见错误类型:")
        for pattern in insights['common_failure_patterns']:
            print(f"    - {pattern}")
    
    print("  💡 系统学习能力:")
    print("    - 自动识别错误模式")
    print("    - 生成恢复建议")
    print("    - 避免重复错误")


def main():
    """主函数"""
    print("🎭 RAG增强GUI自动化系统 - 完整使用示例")
    print("=" * 60)
    
    # 确保环境配置正确
    EnvironmentConfig.ensure_directories()
    
    try:
        # 运行各个示例
        example_1_basic_usage()
        example_2_learning_evolution()
        example_3_complex_task()
        example_4_knowledge_management()
        example_5_configuration()
        example_6_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 所有示例演示完成!")
        
        print("\n📚 接下来你可以:")
        print("  1. 运行 python rag_main.py 体验完整系统")
        print("  2. 运行 python rag_demo.py 查看技术演示")
        print("  3. 修改 rag_config.py 自定义配置")
        print("  4. 查看 README_RAG.md 了解详细文档")
        
        print("\n🚀 开始你的RAG增强GUI自动化之旅吧!")
        
    except Exception as e:
        print(f"❌ 示例执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()