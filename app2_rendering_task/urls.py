# -*- coding: utf-8 -*-
# @Time : 2025/12/16 下午3:52
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : urls.py
# @Project : RealEarthStudio
# @Details : app路由


from django.urls import path
from . import views

app_name = 'app2_rendering_task'

urlpatterns = [
    # 子路由
    # path('start_render', views.RenderingTaskListView.as_view(), name='list'),
]
