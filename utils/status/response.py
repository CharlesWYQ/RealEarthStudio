# -*- coding: utf-8 -*-
# @Time : 2025/9/17 下午2:53
# @Author : CharlesWYQ
# @Email : 1578973516@qq.com
# @File : response.py
# @Project : wangyueqi
# @Details : 


from rest_framework.response import Response
from .status_codes import APIStatus


def api_response(status: APIStatus, message: str = None, data=None, http_status=200):
    """
    {
        "status": 0,
        "message": "success",
        "data": { ... }
    }
    """
    if message is None:
        message = "success" if status == APIStatus.SUCCESS else "error"

    return Response(
        data={
            "status": status,
            "message": message,
            "data": data or {}
        },
        status=http_status
    )


def success(data=None, message="success"):
    return api_response(APIStatus.SUCCESS, message, data, 200)


def error(status: APIStatus, message=None, data=None, http_status=400):
    return api_response(status, message, data, http_status)
