# -*- coding: utf-8 -*-
import re
import time
import requests
from bs4 import BeautifulSoup

# 全局配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://cloud.189.cn/",
    "Origin": "https://cloud.189.cn",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def get_login_page():
    """获取登录页，提取captchaToken等参数"""
    url = "https://cloud.189.cn/web/login.html"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ 获取登录页失败: {str(e)}")
        return None

def extract_captcha_token(html):
    """从登录页提取captchaToken，适配新版页面结构"""
    # 多正则兜底匹配，覆盖不同页面格式
    patterns = [
        r'captchaToken.*?value="([^"]+)"',
        r"captchaToken' value='([^']+)'",
        r'name="captchaToken".*?value="([^"]+)"'
    ]
    for pattern in patterns:
        token_list = re.findall(pattern, html, re.S)
        if token_list:
            return token_list[0].strip()
    print("❌ 未匹配到captchaToken，页面结构已更新或触发风控")
    print("⚠️ 页面内容片段（用于排查）：", html[:1000])
    return None

def login(username, password, captcha_token):
    """执行登录"""
    url = "https://cloud.189.cn/api/portal/loginWithPwd.action"
    data = {
        "userName": username,
        "password": password,
        "captchaToken": captcha_token,
        "validateCode": "",
        "rememberMe": 1
    }
    try:
        resp = SESSION.post(url, data=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("result") == 0:
            print(f"✅ 账号 {username} 登录成功")
            return True
        else:
            print(f"❌ 账号 {username} 登录失败: {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 登录请求异常: {str(e)}")
        return False

def checkin():
    """执行签到"""
    url = "https://cloud.189.cn/api/portal/signIn.action"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("result") == 0:
            print(f"✅ 签到成功！本次获得空间: {result.get('data', {}).get('size', 0)}MB")
            print(f"ℹ️ 累计签到天数: {result.get('data', {}).get('days', 0)}天")
            return True
        else:
            print(f"❌ 签到失败: {result.get('msg', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 签到请求异常: {str(e)}")
        return False

def main():
    print("="*50)
    print("📅 天翼云盘自动签到任务启动")
    print("="*50)

    # 读取账号密码（从标准输入，适配GitHub Actions的here-doc）
    username = input().strip()
    password = input().strip()

    if not username or not password:
        print("❌ 账号或密码为空，终止任务")
        return

    # 步骤1：获取登录页
    html = get_login_page()
    if not html:
        return

    # 步骤2：提取captchaToken
    captcha_token = extract_captcha_token(html)
    if not captcha_token:
        return

    # 步骤3：登录（带重试）
    login_success = False
    for retry in range(3):
        print(f"\n🔄 第 {retry+1} 次尝试登录...")
        if login(username, password, captcha_token):
            login_success = True
            break
        time.sleep(3)
    if not login_success:
        print("❌ 3次登录均失败，终止任务")
        return

    # 步骤4：签到（带重试）
    checkin_success = False
    for retry in range(2):
        print(f"\n🔄 第 {retry+1} 次尝试签到...")
        if checkin():
            checkin_success = True
            break
        time.sleep(3)

    print("\n" + "="*50)
    if checkin_success:
        print("🎉 任务执行完成，签到成功！")
    else:
        print("⚠️ 任务执行完成，签到失败，请检查账号状态")
    print("="*50)

if __name__ == "__main__":
    main()
