# -*- coding: utf-8 -*-
# @Time : 2025/12/23 上午8:23
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : save_scene_to_blend.py
# @Project : RealEarthStudio
# @Details : 保存场景模型为blend文件


import bpy
import os
import glob

# ================== 配置区 ==================
modelClass = "street"  # 修改为你想要的类型名
output_dir = r"E:\Projects\OSGB数据\Blender场景模型"  # 修改为你的导出文件夹路径
# ==========================================

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)


# 生成不冲突的文件名：street_0001.fbx, street_0002.fbx, ...
def get_next_filename(base_name, directory, extension=".blend"):
    pattern = os.path.join(directory, f"{base_name}_*{extension}")
    existing_files = glob.glob(pattern)

    max_num = 0
    for f in existing_files:
        try:
            # 提取编号部分，例如 "street_0005.fbx" → 5
            num_str = os.path.basename(f).replace(f"{base_name}_", "").replace(extension, "")
            num = int(num_str)
            if num > max_num:
                max_num = num
        except ValueError:
            continue  # 忽略无法解析的文件

    next_num = max_num + 1
    return os.path.join(directory, f"{base_name}_{next_num:04d}{extension}")


# 获取下一个可用文件名
filepath = get_next_filename(modelClass, output_dir)

# 执行 Blend 导出（含嵌入贴图）
bpy.ops.file.pack_all()

# 保存文件
bpy.ops.wm.save_mainfile(filepath=filepath)

print(f"✅ 成功导出 Blend 文件：\n{filepath}")
