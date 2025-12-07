import re
import json
from typing import Dict, Any, List, Tuple

def parse_point_string(point_str: str) -> Tuple[int, int]:
    """
    解析point字符串，返回(x,y)坐标元组
    
    Args:
        point_str: point字符串，如 "<point>100 200</point>" 或 "100 200"
    
    Returns:
        tuple: (x, y)坐标元组
    """
    # 移除<point>和</point>标签
    cleaned_str = re.sub(r'</?point>', '', point_str).strip()
    
    # 匹配数字对
    match = re.match(r'(\d+)\s+(\d+)', cleaned_str)
    if not match:
        raise ValueError(f"无效的坐标格式: {point_str}")
    
    x = int(match.group(1))
    y = int(match.group(2))
    
    return (x, y)

def parse_action_string(action_str):
    """
    解析操作字符串，返回包含action_type和action_params的字典
    
    Args:
        action_str: 操作字符串，如 "click(point='<point>x1 y1</point>')"
    
    Returns:
        dict: 包含action_type和action_params的字典
    """
    # 清理字符串两端的空白字符
    action_str = action_str.strip()
    
    # 匹配操作类型和参数部分
    pattern = r'^(\w+)\((.*)\)$'
    match = re.match(pattern, action_str, re.DOTALL)
    
    if not match:
        raise ValueError(f"无效的操作字符串格式: {action_str}")
    
    action_type = match.group(1)
    params_str = match.group(2)
    
    # 解析参数字符串
    action_params = parse_params(params_str)
    
    action_json= {
        "action_type": action_type,
        "action_params": action_params
    }
    return action_json

def parse_params(params_str):
    """
    解析参数字符串，返回参数字典
    
    Args:
        params_str: 参数字符串，如 "point='<point>x1 y1</point>'"
    
    Returns:
        dict: 参数字典
    """
    params = {}
    
    # 使用正则表达式匹配键值对
    # 匹配模式：key='value' 或 key="value"
    pattern = r"(\w+)=('([^']*)'|\"([^\"]*)\")"
    matches = re.findall(pattern, params_str, re.DOTALL)
    
    for match in matches:
        key = match[0]
        # 使用单引号或双引号中的值
        value = match[2] if match[2] else match[3]
        if key == "point" or key == "start_point" or key == "end_point":
            value = parse_point_string(value)
        params[key] = value
    
    return params

def parse_multiple_actions(actions_text):
    """
    解析多行操作文本
    
    Args:
        actions_text: 包含多个操作字符串的文本
    
    Returns:
        list: 包含所有操作字典的列表
    """
    actions = []
    
    # 按行分割，忽略空行和注释行
    lines = actions_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        # 忽略空行和注释行（以#开头的行）
        if not line or line.startswith('#'):
            continue
        
        try:
            action_dict = parse_action_string(line)
            actions.append(action_dict)
        except ValueError as e:
            print(f"警告: 无法解析行: {line}, 错误: {e}")
            continue
    
    return actions

if __name__ == "__main__":
    # 测试单个操作字符串
    test_cases = [
        "type(content='你好，这是自动化测试\n')"
    ]
    
    print("=== 单个操作测试 ===")
    for test_case in test_cases:
        try:
            result = parse_action_string(test_case)
            print(f"输入: {test_case}")
            print(f"输出: {json.dumps(result, ensure_ascii=False, indent=2)}")
            print("-" * 50)
        except Exception as e:
            print(f"错误: {e}")