#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from datetime import datetime

# ================= 配置区域 =================
# 1. OpenWeather 配置
OWM_API_KEY = "120de1f9dae6386eed4e4c9a28c6b300"
LAT = "27.917761"  # 举例：上海纬度
LON = "120.694528" # 举例：上海经度
UNITS = "metric" # metric=摄氏度, imperial=华氏度
LANG = "zh_cn"   # 简体中文

# 2. 企业微信 Webhook 配置
# 只需要 Key 部分，或者填入完整 URL 也可以，脚本逻辑里会处理
WECOM_KEY = "b2e863ca-0a6e-4e24-9e24-3ee796364595" 
# ===========================================

def get_weather():
    """获取 OpenWeather One Call 3.0 数据"""
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": OWM_API_KEY,
        "units": UNITS,
        "lang": LANG,
        "exclude": "minutely,hourly"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None

def send_wechat_text(content):
    """发送普通文本消息到企业微信 (兼容普通微信显示)"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    # 改为 text 类型
    data = {
        "msgtype": "text",
        "text": {
            "content": content
            # 如果需要提醒所有人，可以取消下面这行的注释
            # "mentioned_list": ["@all"] 
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data)
        print(f"推送结果: {res.text}")
    except Exception as e:
        print(f"推送失败: {e}")

def generate_report(data):
    """生成纯文本格式的天气日报"""
    if not data:
        return "获取天气数据失败，请检查服务器日志。"

    # 解析数据
    current = data.get("current", {})
    daily_today = data.get("daily", [])[0]
    
    # 基础信息
    temp_now = current.get("temp", "N/A")
    weather_desc = current.get("weather", [{}])[0].get("description", "未知")
    
    # 每日详情
    temp_min = daily_today.get("temp", {}).get("min", "N/A")
    temp_max = daily_today.get("temp", {}).get("max", "N/A")
    pop = daily_today.get("pop", 0) * 100 
    uvi = daily_today.get("uvi", 0)
    
    # 日期 (格式：2023-10-27 星期五)
    week_days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    dt = datetime.now()
    date_str = dt.strftime("%Y-%m-%d") + " " + week_days[dt.weekday()]
    
    # 逻辑提示
    tips = []
    if pop > 30:
        tips.append("☔ 今天有雨，出门记得带伞！")
    if uvi > 6:
        tips.append("🧴 紫外线较强，注意防晒。")
    if not tips:
        tips.append("✨ 今天天气不错，祝心情愉快！")
    
    tips_str = "\n".join(tips)

    # 构造纯文本消息，使用 Emoji 进行视觉分区
    text_content = f"""【早上好！今日天气日报】
📅 日期：{date_str}
-----------------------
🌤️ 天气：{weather_desc}
🌡️ 当前：{temp_now}°C
📉 最低：{temp_min}°C
📈 最高：{temp_max}°C
💧 降雨：{int(pop)}%
🕶️ 紫外线：{uvi}
-----------------------
💡 小贴士：
{tips_str}"""
    
    return text_content.strip()

if __name__ == "__main__":
    print(f"[{datetime.now()}] 开始执行任务...")
    weather_data = get_weather()
    if weather_data:
        report = generate_report(weather_data)
        # 调用发送文本的函数
        send_wechat_text(report)
    print("任务结束")


