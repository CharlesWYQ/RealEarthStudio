# -*- coding: utf-8 -*-
# @Time : 2025/9/17 下午2:51
# @Author : CharlesWYQ
# @Email : 1578973516@qq.com
# @File : status_code.py
# @Project : wangyueqi
# @Details : 


from enum import IntEnum


class APIStatus(IntEnum):
    SUCCESS = 0
    ERROR = 1
    VALIDATION_ERROR = 4000
    AUTH_FAILED = 4010
    PERMISSION_DENIED = 4030
    RESOURCE_NOT_FOUND = 4040
    SERVER_ERROR = 5000

    # 渲染任务相关
    RENDER_ERROR = 6000

    def __new__(cls, value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, value):
        _messages = {
            0: ("成功", "请求已成功处理"),
            1: ("失败", "通用失败，具体原因见 message 字段"),
            4000: ("参数校验失败", "请求参数不符合格式要求，请检查必填项、数据类型或范围"),
            4010: ("认证失败", "Token 无效或已过期，请重新登录"),
            4030: ("权限不足", "当前用户无权访问该资源"),
            4040: ("资源未找到", "请求的资源不存在，请检查 URL 或资源 ID"),
            5000: ("服务器错误", "服务端发生未预期错误，请联系管理员"),

            # 任务规划
            6000: ("渲染失败", "渲染失败"),
        }
        self.message, self.detail = _messages.get(value, ("未知状态", "无详细说明"))

    @property
    def msg(self):
        """兼容旧代码，等同于 message"""
        return self.message

    @property
    def desc(self):
        """详细描述（可用于日志或调试）"""
        return self.detail

    @classmethod
    def choices(cls):
        return [(key.value, key.message) for key in cls]


if __name__ == '__main__':
    status = APIStatus.SUCCESS
    print(status)
    print(status.message)
    print(status.desc)
