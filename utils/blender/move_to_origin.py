# -*- coding: utf-8 -*-
# @Time : 2025/12/23 上午8:22
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : move_to_origin.py
# @Project : RealEarthStudio
# @Details : 移动模型到原点


import bpy

# 1. 在游标位置创建空对象
cursor_loc = bpy.context.scene.cursor.location.copy()
bpy.ops.object.empty_add(type='PLAIN_AXES', location=cursor_loc)
parent_empty = bpy.context.active_object
parent_empty.name = "ModelCenter"

# 2. 绑定所有 Mesh 模型为子级（保持视觉位置）
mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
for obj in mesh_objects:
    world_mat = obj.matrix_world.copy()
    obj.parent = parent_empty
    obj.matrix_world = world_mat

# 3. 👇 关键步骤：将空对象移到世界原点
parent_empty.location = (0, 0, 0)
