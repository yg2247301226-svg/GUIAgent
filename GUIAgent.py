import os
import base64
import re
import time
from PIL import Image, ImageDraw
import pyautogui
from volcenginesdkarkruntime import Ark
from prompt import COMPUTER_USE_DOUBAO1
import matplotlib.pyplot as plt
from AutoGUI import PyAutoGUIActionExecutor
from ParseActionString import parse_action_string
import json
import io
from smart_position import find_position

class DoubaoUITarsGUI:
    def __init__(self, api_key=None):
        """
        初始化Doubao UI-TARS GUI操作工具 
        
        Args:
            api_key: 火山引擎API Key，如果为None则从环境变量ARK_API_KEY读取
        """
        self.api_key = api_key or os.getenv('ARK_API_KEY')
        if not self.api_key:
            raise ValueError("请提供API Key或设置ARK_API_KEY环境变量")
            
        self.client = Ark(api_key=self.api_key)
        self.model_name = "doubao-1-5-ui-tars-250428"
        self.action_executor = PyAutoGUIActionExecutor()
        self.max_steps = 25
    
    def capture_screenshot(self, save_path=None):
        """
        捕获屏幕截图
        
        Args:
            save_path: 截图保存路径，如果为None则使用临时文件
            
        Returns:
            str: 截图文件路径
        """
        if save_path is None:
            save_path = f"screenshot/screenshot_{int(time.time())}.png"
        
        screenshot = pyautogui.screenshot()
        new_size = (960,540)
        screenshot = screenshot.resize(new_size,Image.Resampling.LANCZOS)
        screenshot.save(save_path)
        self.screenshot_size = screenshot.size
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    
    def construct_messages(self, instruction, image_base64, language="Chinese"):
        system_prompt = COMPUTER_USE_DOUBAO1.format(instruction=instruction, language=language)

        message = [
                    {
                        "role": "user",
                        "content": system_prompt
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
        return message
    
    def inference(self, messages):
        response = self.client.chat.completions.create(
            # 按需替换 model id
            model=self.model_name,
            messages=messages,
            temperature=0.0,  # 固定温度保证输出稳定
            stream=False       # 流式获取响应（可选）
        )
        token = response.usage.total_tokens
        response = response.choices[0].message.content
        # print(response)
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1]
        else:
            # 尝试直接解析整个响应
            response = response.strip()
        try:
            response = self.clean_json_response(response)
            response = json.loads(response)
        except Exception as e:
            print("json解析失败",e)
            print(response)
        return response,token
    def clean_json_response(self,response_text):
        """移除JSON中的注释，使其可解析"""
        # 移除单行注释
        lines = response_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 查找注释开始位置
            comment_pos = line.find('//')
            if comment_pos != -1:
                # 检查注释是否在字符串内
                before_comment = line[:comment_pos]
                quote_count = before_comment.count('"')
                if quote_count % 2 == 0:  # 偶数个引号，说明注释不在字符串内
                    line = before_comment.rstrip(',').rstrip()
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def run_autonomous_goal(self, goal):
        """自主执行总目标"""
        print(f"🎯 开始执行总目标: {goal}")
        print(f"📊 最大尝试步骤: {self.max_steps}")
        self.current_step = 0
        action_message = None
        self.total_token = 0
        while self.current_step < self.max_steps:
            self.current_step += 1
            print(f"🔄 执行步骤 {self.current_step}/{self.max_steps}")
            try:
                # 截图
                image = self.capture_screenshot()
            except Exception as e:
                print("截图失败",e)
                continue
            # AI分析并规划下一步
            try:
                if not action_message:
                    action_message = self.construct_messages(instruction=goal, image_base64=image)
                else:
                    if len(action_message)>5:
                        action_message = [action_message[0]] + action_message[-4:]
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
                ai_response,token = self.inference(messages=action_message)
                action_message = action_message[:-1]
                self.total_token += token
                print(f"AI思考: {ai_response.get('thought', '无')}")
                print(f"AI建议: {ai_response.get('action', '无')}")
                print(f"AI使用token数: {token}")
                action_message.append({
                    "role": "assistant",
                    "content": ai_response.get("thought")
                })
                if not ai_response:
                    print("AI分析失败")
                    continue
            except Exception as e:
                print("AI分析失败",e)
                continue

            # 执行AI建议
            try:
                action_info = parse_action_string(ai_response.get("action"))
                if action_info:
                    message = self.action_executor.execute_parsed_action(action_info)
                    print("执行成功", message)
                    time.sleep(1)
                    if action_info.get("action_type") == "finished":
                        # print("AI判断目标已完成！")
                        return ai_response, True, self.total_token
                else:
                    print("执行失败")
            except Exception as e:
                print("执行失败",e)
                continue
        print(f"达到最大步骤数 {self.max_steps}，目标未完成")
        return ai_response, False,self.total_token


# def main():
#     api_key = "6c08cf37-b093-4bae-a993-0e33fc3a1805"
#     doubao_gui = DoubaoUITarsGUI(api_key=api_key)
#     instruction = "在飞书中搜索联系人'杨戈 南京邮电大学 电子信息 26届'并发送消息'你好，这是自动化测试'"
#     image = doubao_gui.capture_screenshot()
#     messages = doubao_gui.construct_messages(instruction=instruction, image_base64=image)
#     response = doubao_gui.inference(messages)
#     print(response)
#     action_info = parse_action_string(response.get("action"))
#     print(action_info)
#     doubao_gui.action_executor.execute_parsed_action(action_info)
    
# if __name__ == "__main__":
#     main()