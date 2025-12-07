import pyautogui
import time
import re
import logging
from typing import Dict, Any
import pyperclip
from smart_position import find_position


class PyAutoGUIActionExecutor:
    """精简版GUI动作执行器（使用您现有的坐标换算方法）"""
    
    def __init__(self, safety_check=True, pause_between_actions=0.5):
        """
        初始化动作执行器
        
        Args:
            safety_check: 是否启用安全检测
            pause_between_actions: 动作间暂停时间（秒）
        """
        self.safety_check = safety_check
        self.pause_between_actions = pause_between_actions
        
        # 设置pyautogui参数
        pyautogui.FAILSAFE = safety_check
        pyautogui.PAUSE = pause_between_actions
        
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # 快捷键映射
        self.key_mapping = {
            'ctrl': 'ctrl', 'control': 'ctrl',
            'alt': 'alt', 
            'shift': 'shift',
            'win': 'win', 'windows': 'win',
            'cmd': 'command', 'command': 'command',
            'esc': 'esc', 'escape': 'esc',
            'enter': 'enter', 'return': 'enter',
            'tab': 'tab',
            'space': 'space',
            'backspace': 'backspace',
            'delete': 'delete',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right'
        }
    
    def unescape_content(self, content: str) -> str:
        """反转义内容字符串"""
        content = content.replace("\\'", "'")
        content = content.replace('\\"', '"')
        content = content.replace("\\n", "\n")
        content = content.replace("\\t", "\t")
        return content
    
    def execute_click(self, x: int, y: int) -> Dict[str, Any]:
        """执行单击操作（使用绝对坐标）"""
        try:
            # pyautogui.moveTo(x, y, duration=0.3)
            # pyautogui.click()
            pyautogui.click(x, y)
            self.logger.info(f"✅ 单击完成: ({x}, {y})")
            return {"status": "success", "action": "click", "coordinates": (x, y)}
        except Exception as e:
            self.logger.error(f"❌ 单击失败: {e}")
            return {"status": "error", "action": "click", "error": str(e)}
    
    def execute_left_double(self, x: int, y: int) -> Dict[str, Any]:
        """执行左键双击操作"""
        try:
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.doubleClick()
            self.logger.info(f"✅ 左键双击完成: ({x}, {y})")
            return {"status": "success", "action": "left_double", "coordinates": (x, y)}
        except Exception as e:
            self.logger.error(f"❌ 左键双击失败: {e}")
            return {"status": "error", "action": "left_double", "error": str(e)}
    
    def execute_right_single(self, x: int, y: int) -> Dict[str, Any]:
        """执行右键单击操作"""
        try:
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.rightClick()
            self.logger.info(f"✅ 右键单击完成: ({x}, {y})")
            return {"status": "success", "action": "right_single", "coordinates": (x, y)}
        except Exception as e:
            self.logger.error(f"❌ 右键单击失败: {e}")
            return {"status": "error", "action": "right_single", "error": str(e)}
    
    def execute_drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """执行拖拽操作"""
        try:
            pyautogui.moveTo(start_x, start_y, duration=0.3)
            pyautogui.mouseDown()
            time.sleep(0.1)
            pyautogui.moveTo(end_x, end_y, duration=0.5)
            pyautogui.mouseUp()
            self.logger.info(f"✅ 拖拽完成: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            return {
                "status": "success", 
                "action": "drag", 
                "start_coordinates": (start_x, start_y),
                "end_coordinates": (end_x, end_y)
            }
        except Exception as e:
            self.logger.error(f"❌ 拖拽失败: {e}")
            return {"status": "error", "action": "drag", "error": str(e)}
    
    def execute_hotkey(self, key_str: str) -> Dict[str, Any]:
        """执行快捷键操作"""
        try:
            keys = key_str.lower().split()
            if len(keys) > 3:
                return {"status": "error", "action": "hotkey", "error": "快捷键不能超过3个键"}
            
            mapped_keys = [self.key_mapping.get(key, key) for key in keys]
            pyautogui.hotkey(*mapped_keys)
            self.logger.info(f"✅ 快捷键执行: {key_str}")
            return {"status": "success", "action": "hotkey", "keys": mapped_keys}
        except Exception as e:
            self.logger.error(f"❌ 快捷键失败: {e}")
            return {"status": "error", "action": "hotkey", "error": str(e)}
    
    def execute_type(self, x, y, content: str) -> Dict[str, Any]:
        """执行文本输入操作"""
        try:
            # pyautogui.moveTo(x, y, duration=0.3)
            # pyautogui.click()
            # time.sleep(0.5)
            unescaped_content = self.unescape_content(content)
            pyperclip.copy(unescaped_content)
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'v')
            self.logger.info(f"✅ 文本输入: {repr(unescaped_content)}")
            return {"status": "success", "action": "type", "content": unescaped_content}
        except Exception as e:
            self.logger.error(f"❌ 文本输入失败: {e}")
            return {"status": "error", "action": "type", "error": str(e)}
    
    def execute_scroll(self, x: int, y: int, direction: str) -> Dict[str, Any]:
        """执行滚动操作"""
        try:
            pyautogui.moveTo(x, y, duration=0.3)
            direction = direction.lower()
            scroll_amount = 100
            
            if direction == 'up':
                pyautogui.scroll(scroll_amount)
            elif direction == 'down':
                pyautogui.scroll(-scroll_amount)
            elif direction == 'right':
                pyautogui.hscroll(scroll_amount)
            elif direction == 'left':
                pyautogui.hscroll(-scroll_amount)
            else:
                return {"status": "error", "action": "scroll", "error": f"无效方向: {direction}"}
            
            self.logger.info(f"✅ 滚动完成: 方向={direction}, 位置=({x}, {y})")
            return {"status": "success", "action": "scroll", "direction": direction}
        except Exception as e:
            self.logger.error(f"❌ 滚动失败: {e}")
            return {"status": "error", "action": "scroll", "error": str(e)}
    
    def execute_wait(self, duration: float = 5.0) -> Dict[str, Any]:
        """执行等待操作"""
        try:
            self.logger.info(f"⏳ 等待 {duration} 秒...")
            time.sleep(duration)
            self.logger.info("✅ 等待完成")
            return {"status": "success", "action": "wait", "duration": duration}
        except Exception as e:
            self.logger.error(f"❌ 等待失败: {e}")
            return {"status": "error", "action": "wait", "error": str(e)}
    def execute_finished(self, content: str = "") -> Dict[str, Any]:
        """执行任务完成操作"""
        try:
            unescaped_content = self.unescape_content(content) if content else "任务完成"
            self.logger.info(f"🎉 任务完成: {unescaped_content}")
            return {"status": "success", "action": "finished", "message": unescaped_content}
        except Exception as e:
            self.logger.error(f"❌ 完成操作失败: {e}")
            return {"status": "error", "action": "finished", "error": str(e)}
        
    
    def execute_parsed_action(self, action_info):
        """
        执行解析后的动作
        """
        action_type = action_info.get("action_type")
        params = action_info.get("action_params")
        
        print(f"⚡ 执行: {action_type}")
        print(f"参数: {params}")
        
        if action_type == "click":
            x,y = find_position(params.get('point'))
            return self.execute_click(x, y)
            
        elif action_type == "left_double":
            x,y = find_position(params.get('point'))
            return self.execute_left_double(x, y)
            
        elif action_type == "right_single":
            x,y = find_position(params.get('point'))
            return self.execute_right_single(x, y)
            
        elif action_type == "drag":
            start_x, start_y = find_position(params.get('start_point'))
            end_x, end_y = find_position(params.get('end_point'))
            return self.execute_drag(
                start_x, start_y, 
                end_x, end_y
            )
        elif action_type == "hotkey":
            key = params.get('key')
            return self.execute_hotkey(key)
            
        elif action_type == "type":
            x, y = find_position(params.get('point'))
            content = params.get('content')
            return self.execute_type(x, y, content)
            
        elif action_type == "scroll":
            x,y = find_position(params.get('point'))
            direction = params.get('direction')
            return self.execute_scroll(
                x, y, direction
            )
            
        elif action_type == "wait":
            return self.execute_wait()
            
        elif action_type == "finished":
            return self.execute_finished(
                params.get("content", "")
            )
        else:
            return {"status": "error", "action": "unknown", "error": f"未知动作类型: {action_type}"}

# test
# 使用示例
# def main():
# #     """使用示例"""
# #     # 创建执行器
#     executor = PyAutoGUIActionExecutor()
#     action_info = {'action_type': 'click', 'action_params': {'point': (628, 972)}}
#     result = executor.execute_parsed_action(action_info)
#     print(result)
#     # 测试动作（使用绝对坐标）
#     test_actions = [
#         ("click", (693,954)),  # 屏幕中央点击
#         ("type", ("Hello World\\n",)),
#         ("hotkey", ("enter",)),
#         ("wait", (2,))  # 等待2秒
#     ]
    
#     for action_type, params in test_actions:
#         print(f"\n执行 {action_type}: {params}")
        
#         if action_type == "click":
#             result = executor.execute_click(*params)
#         elif action_type == "type":
#             result = executor.execute_type(*params)
#         elif action_type == "hotkey":
#             result = executor.execute_hotkey(*params)
#         elif action_type == "wait":
#             result = executor.execute_wait(*params)
        
#         print(f"结果: {result}")


# if __name__ == "__main__":
#     main()