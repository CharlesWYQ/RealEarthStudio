# -*- coding: utf-8 -*-
# @Time : 2025/12/25 下午2:44
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : decorator_timer.py
# @Project : RealEarthStudio
# @Details : 计时装饰器

import time
import functools


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"🕗️ 任务执行时间: {end - start:.2f}秒")
        return result

    return wrapper
