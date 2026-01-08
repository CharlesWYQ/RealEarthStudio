# -*- coding: utf-8 -*-
# @Time : 2025/12/23 下午12:23
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : save_target_to_fbx.py
# @Project : RealEarthStudio
# @Details : 保存目标模型为fbx文件


import bpy
import os

# ================== 配置区 ==================
# 修改为你自己的输出路径
OUTPUT_DIR = r"\\Mm-202311022138\DATA\Blender目标模型\01"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# ==========================================

# 获取所有可见的 Mesh 对象
objects_to_export = [
    obj for obj in bpy.context.visible_objects
    if obj.type == 'MESH'
]

print(f"准备导出 {len(objects_to_export)} 个模型（嵌入贴图）...")

for obj in objects_to_export:
    print(f" → 导出: {obj.name}")

    # 1. 创建副本
    obj_copy = obj.copy()
    obj_copy.data = obj.data.copy()
    obj_copy.location = (0, 0, 0)  # 移动到原点

    # 2. 添加到场景并选中
    bpy.context.collection.objects.link(obj_copy)
    bpy.ops.object.select_all(action='DESELECT')
    obj_copy.select_set(True)
    bpy.context.view_layer.objects.active = obj_copy

    # 3. 应用位置变换
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    # 4. 导出为 FBX（关键：embed_textures=True）
    filepath = os.path.join(OUTPUT_DIR, f"{obj.name}.glb")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,
        export_format='GLB'
    )

    # 5. 清理临时对象
    bpy.data.objects.remove(obj_copy, do_unlink=True)

print(f"\n✅ 完成！所有 GLB 文件已嵌入贴图并居中。\n路径: {OUTPUT_DIR}")
