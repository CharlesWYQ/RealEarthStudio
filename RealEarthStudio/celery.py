# -*- coding: utf-8 -*-
# @Time : 2025/12/17 上午10:55
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : celery.py
# @Project : RealEarthStudio
# @Details : Celery配置文件


import os
from celery import Celery

# 设置 Django 的默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RealEarthStudio.settings')

app = Celery('RealEarthStudio')

# 从 Django settings 中加载配置，以 CELERY_ 开头的项
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各 app 下的 tasks.py
app.autodiscover_tasks()

# 可选：显式指定要发现任务的应用
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
