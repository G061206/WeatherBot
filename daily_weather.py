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
        "exclude": "minutely,hourly" # 排除分钟和小时级数据，减小体积
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None

def send_wechat_markdown(content):
    """发送 Markdown 消息到企业微信"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data)
        print(f"推送结果: {res.text}")
    except Exception as e:
        print(f"推送失败: {e}")

def generate_report(data):
    """生成 Markdown 格式的天气日报"""
    if not data:
        return "获取天气数据失败，请检查服务器日志。"

    # 解析数据
    current = data.get("current", {})
    daily_today = data.get("daily", [])[0] # 获取今天的数据
    
    # 基础信息
    temp_now = current.get("temp", "N/A")
    weather_desc = current.get("weather", [{}])[0].get("description", "未知")
    
    # 每日详情
    temp_min = daily_today.get("temp", {}).get("min", "N/A")
    temp_max = daily_today.get("temp", {}).get("max", "N/A")
    pop = daily_today.get("pop", 0) * 100 # 降水概率 (0-1 转为百分比)
    uvi = daily_today.get("uvi", 0)
    
    # 日期
    date_str = datetime.now().strftime("%Y-%m-%d %A")
    
    # 逻辑提示
    tips = []
    if pop > 30:
        tips.append("☔️ **今天有雨，出门记得带伞！**")
    if uvi > 6:
        tips.append("☀️ **紫外线较强，注意防晒。**")
    if not tips:
        tips.append("✨ 今天天气不错，保持好心情！")
    
    tips_str = "\n".join(tips)

    # 构造 Markdown (企业微信支持特定颜色: <font color="info/comment/warning">)
    # info=绿色, comment=灰色, warning=橙红色
    markdown_content = f"""
### 早上好！今日天气日报 📅
> {date_str}

**当前天气**: <font color="info">{weather_desc}</font>
**实时温度**: {temp_now}°C
**今日气温**: {temp_min}°C ~ {temp_max}°C
**降雨概率**: <font color="{'warning' if pop > 30 else 'comment'}">{int(pop)}%</font>
**紫外线指数**: {uvi}

---
{tips_str}
    """
    return markdown_content.strip()

if __name__ == "__main__":
    print(f"[{datetime.now()}] 开始执行任务...")
    weather_data = get_weather()
    if weather_data:
        report = generate_report(weather_data)
        send_wechat_markdown(report)

    print("任务结束")

