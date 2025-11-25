#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime
import json

# ================= 配置区域 =================

# 从环境变量获取 Key
OWM_API_KEY = os.getenv("OWM_API_KEY")
WECOM_KEY = os.getenv("WECOM_KEY")

# 经纬度配置
LAT = "27.917761"
LON = "120.694528"
UNITS = "metric"
LANG = "zh_cn"

# 降雨风险阈值
POP_THRESHOLD = 0.5  # 降雨概率阈值 (50%)
RAIN_INTENSITY_THRESHOLD = 2.5  # 降雨强度阈值 (mm/h)

# 检查 Key 是否存在
if not OWM_API_KEY or not WECOM_KEY:
    raise ValueError("未找到环境变量 OWM_API_KEY 或 WECOM_KEY，请在 GitHub Secrets 中配置")
# ===========================================


def get_hourly_weather():
    """获取 OpenWeather One Call 3.0 小时级数据"""
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": OWM_API_KEY,
        "units": UNITS,
        "lang": LANG,
        "exclude": "minutely,daily,alerts"  # 只保留 current 和 hourly
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None


def send_wechat_text(content):
    """发送普通文本消息到企业微信"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"

    headers = {"Content-Type": "application/json"}

    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print(f"推送结果: {res.text}")
    except Exception as e:
        print(f"推送失败: {e}")


def check_precipitation_risk(data):
    """
    检查未来数小时内是否存在突发降雨风险
    返回: (是否有风险, 风险详情列表)
    """
    if not data:
        return False, []

    hourly = data.get("hourly", [])
    if not hourly:
        print("未获取到小时级数据")
        return False, []

    risks = []

    # 检查未来6小时的天气数据
    for i, hour_data in enumerate(hourly[:6]):
        dt = datetime.fromtimestamp(hour_data.get("dt", 0))
        time_str = dt.strftime("%H:%M")

        # 获取降雨概率 (0-1)
        pop = hour_data.get("pop", 0)

        # 获取降雨量 (如果有的话)
        rain = hour_data.get("rain", {})
        rain_1h = rain.get("1h", 0) if isinstance(rain, dict) else 0

        # 天气描述 (defensive check for weather array)
        weather_list = hour_data.get("weather", [])
        weather_desc = weather_list[0].get("description", "未知") if weather_list else "未知"

        # 检查是否超过阈值
        is_risk = False
        risk_reason = []

        if pop >= POP_THRESHOLD:
            is_risk = True
            risk_reason.append(f"降雨概率{int(pop * 100)}%")

        if rain_1h >= RAIN_INTENSITY_THRESHOLD:
            is_risk = True
            risk_reason.append(f"降雨强度{rain_1h}mm/h")

        if is_risk:
            risks.append({
                "time": time_str,
                "pop": pop,
                "rain_1h": rain_1h,
                "weather": weather_desc,
                "reason": "、".join(risk_reason)
            })

    return len(risks) > 0, risks


def generate_alert_message(risks):
    """生成降雨预警消息"""
    if not risks:
        return None

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")

    risk_details = []
    for risk in risks:
        detail = f"⏰ {risk['time']} - {risk['weather']}（{risk['reason']}）"
        risk_details.append(detail)

    risk_str = "\n".join(risk_details)

    message = f"""【⚠️ 突发降雨预警】
📅 检测时间：{date_str}
-----------------------
📍 未来6小时内可能出现降雨：

{risk_str}

-----------------------
💡 提醒：请注意携带雨具，做好防雨准备！"""

    return message.strip()


if __name__ == "__main__":
    print(f"[{datetime.now()}] 开始执行小时级降雨检测...")

    weather_data = get_hourly_weather()

    if weather_data:
        has_risk, risks = check_precipitation_risk(weather_data)

        if has_risk:
            print(f"检测到 {len(risks)} 个降雨风险时段")
            alert_message = generate_alert_message(risks)
            print(f"预警内容:\n{alert_message}")
            send_wechat_text(alert_message)
        else:
            print("未检测到突发降雨风险")
    else:
        print("获取天气数据失败")

    print("任务结束")
