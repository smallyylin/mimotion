# -*- coding: utf-8 -*-
"""
虚拟设备自动绑定模块。

背景：Zepp Life(原小米运动) 新注册账号若从未绑定过任何手环/手表设备，
华米云端会拦截步数同步。本模块在检测到账号未绑定设备时，调用第三方接口
(api.aineishe.com) 自动为该账号绑定一台虚拟设备，随后即可正常上传步数。

接口文档：https://api.aineishe.com/api/v1/api/zepplife/bind
"""
import json
import os

import requests

# 第三方虚拟设备绑定接口地址
VIRTUAL_BIND_API_URL = "https://api.aineishe.com/api/v1/api/zepplife/bind"
# 默认 API Key（可通过环境变量 BIND_API_KEY 覆盖）
DEFAULT_BIND_API_KEY = "e02176-3c67d1-21a87b-84826c"
# 自定义虚拟设备显示名（接口限制 6 字以内）
DEFAULT_VIRTUAL_DEVICE_NAME = "Mi手环"


def bind_virtual_device(app_token, user_id, user=None, password=None,
                        apikey=None, device_name=None) -> (bool, str):
    """
    账号识别：若 Zepp 账号未绑定小米手环/手表设备，调用第三方接口自动绑定一台虚拟设备。

    该接口要求一次性传全账号信息（user/pass）与用户信息（userid/apptoken）。

    :param app_token:  登录后获取的 app_token
    :param user_id:    登录后获取的 user_id
    :param user:       Zepp 账号（手机号/邮箱）
    :param password:   Zepp 账号密码
    :param apikey:     第三方接口 API Key，缺省取环境变量 BIND_API_KEY 或内置默认值
    :param device_name: 自定义虚拟设备显示名（接口限制 6 字以内）
    :return: (是否发起成功, 返回信息)
    """
    if not apikey:
        apikey = os.environ.get("BIND_API_KEY") or DEFAULT_BIND_API_KEY
    if not device_name:
        device_name = os.environ.get("BIND_DEVICE_NAME") or DEFAULT_VIRTUAL_DEVICE_NAME
    if not app_token or not user_id:
        return False, "app_token 或 user_id 为空，无法绑定虚拟设备"

    params = {
        "apikey": apikey,
        # 该接口要求同时传全账号密码与 userid/apptoken
        "user": user or "",
        "pass": password or "",
        "userid": user_id,
        "apptoken": app_token,
        # 接口限制 6 字以内，超出自动截取前 6 个字
        "name": str(device_name)[:6],
    }

    try:
        resp = requests.get(VIRTUAL_BIND_API_URL, params=params, timeout=15)
    except Exception as e:
        return False, f"绑定虚拟设备请求异常: {e}"

    try:
        body = resp.json()
    except Exception:
        body = {"raw": (resp.text or "")[:200]}

    if resp.status_code != 200:
        return False, f"绑定虚拟设备HTTP异常 status={resp.status_code} body={json.dumps(body, ensure_ascii=False)}"

    # 业务层错误码（如 code=502 接口已下架、code!=0 等）
    biz_code = body.get("code") if isinstance(body, dict) else None
    if biz_code not in (None, 0, "0", 200, "200", "success"):
        return False, f"绑定虚拟设备业务失败 code={biz_code} msg={body.get('msg') or body}"

    return True, json.dumps(body, ensure_ascii=False)
