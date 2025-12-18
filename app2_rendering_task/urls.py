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
    # 开始渲染
    path('<uuid:render_id>/start_render/', views.StartRender.as_view(), name='start_render_view'),
    path('<uuid:render_id>/show_dataset/', views.ShowDataset.as_view(), name='show_dataset_view'),
]
