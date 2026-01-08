# -*- coding: utf-8 -*-
# @Time : 2026/1/8 下午4:20
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : select_target_to_glb.py
# @Project : RealEarthStudio
# @Details : 保存选择模型为glb文件


import bpy
import os
from mathutils import Vector

export_dir = r"D:\Projects\RealEarthStudio\Blender目标模型\03"
file_name = "轿车-雷克萨斯"

# 获取当前选中的有效对象
selected_objects = [obj for obj in bpy.context.selected_objects if obj.type in {'MESH', 'ARMATURE', 'EMPTY'}]

if not selected_objects:
    print("未选中任何有效对象！")
else:
    # 1. 将每个对象的原点移到几何中心
    for obj in selected_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # 2. 计算整体包围盒（世界空间）
    depsgraph = bpy.context.evaluated_depsgraph_get()
    combined_min = Vector((float('inf'), float('inf'), float('inf')))
    combined_max = Vector((-float('inf'), -float('inf'), -float('inf')))

    has_mesh = False
    for obj in selected_objects:
        if obj.type == 'MESH':
            has_mesh = True
            obj_eval = obj.evaluated_get(depsgraph)
            mesh = obj_eval.to_mesh()
            matrix = obj.matrix_world
            for v in mesh.vertices:
                world_co = matrix @ v.co
                for i in range(3):
                    combined_min[i] = min(combined_min[i], world_co[i])
                    combined_max[i] = max(combined_max[i], world_co[i])
            obj_eval.to_mesh_clear()

    if has_mesh:
        # X、Y 居中到 0；Z 底部对齐 0
        center_xy = Vector(((combined_min.x + combined_max.x) / 2, (combined_min.y + combined_max.y) / 2, 0))
        bottom_z = combined_min.z
        target_location = Vector((0, 0, -bottom_z))  # 先抵消 Z 偏移
        xy_offset = -center_xy  # 再将 XY 移到 0
        total_offset = Vector((xy_offset.x, xy_offset.y, -bottom_z))

        for obj in selected_objects:
            obj.location += total_offset

    # 3. 应用变换
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected_objects:
        obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 4. 【可选】将选中对象临时加入一个新集合（不影响 FBX，但便于管理）
    temp_collection = bpy.data.collections.new(name=f"Export_{file_name}")
    bpy.context.scene.collection.children.link(temp_collection)
    for obj in selected_objects:
        # 从原有集合中移除（可选），或保留（推荐保留）
        # 这里只是添加到新集合，不移除原有
        if obj.name not in temp_collection.objects:
            temp_collection.objects.link(obj)

    # 5. 确保导出目录存在
    os.makedirs(export_dir, exist_ok=True)
    base_name = file_name
    ext = ".glb"
    counter = 0
    while True:
        if counter == 0:
            filename = base_name + ext
        else:
            filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(export_dir, filename)
        if not os.path.exists(file_path):
            break
        counter += 1

    # 6. 导出 FBX —— 尝试嵌入贴图（但 FBX 实际不支持，仅当贴图已打包时可能有效）
    bpy.ops.export_scene.gltf(
        filepath=file_path,
        use_selection=True,
        export_format='GLB'
    )

    print(f"✅ 模型已导出至: {file_path}")

    # 7. 删除临时集合（可选）
    bpy.context.scene.collection.children.unlink(temp_collection)
    bpy.data.collections.remove(temp_collection)

    # 8. 删除选中对象
    bpy.ops.object.delete(use_global=False)
