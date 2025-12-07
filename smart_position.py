from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import re
import pyautogui

def find_position(params):
        screenshot = pyautogui.screenshot()
        original_width,original_height = screenshot.size
        x ,y = params
        if x and y:
            x = int(x/1000*original_width)  # 提取第一个数字并转为绝对坐标
            y = int(y/1000*original_height)  # 提取第二个数字并转为绝对坐标  # 生成整数元组
        else:
            raise ValueError(f"坐标参数错误，换算失败")
        # print(action_point)
        # 在原图上标记动作位置
        # image = Image.open(image_path)
        # draw = ImageDraw.Draw(image)
        # draw.ellipse((action_point[0]-5, action_point[1]-5, action_point[0]+5, action_point[1]+5), fill="red")

        return x,y