# -*- coding: utf-8 -*-
# @Time : 2025/12/23 下午12:22
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : remove_models.py
# @Project : RealEarthStudio
# @Details : 清除不需要的模型


import bpy

# 获取当前选中的对象（要保留的）
selected_objects = set(bpy.context.selected_objects)

# 遍历场景中所有对象
for obj in bpy.data.objects:
    if obj not in selected_objects:
        # 取消链接（从所有集合中移除）并删除
        bpy.data.objects.remove(obj, do_unlink=True)
