# -*- coding: utf-8 -*-
# @Time : 2025/12/25 上午10:23
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : get_marker_positions.py
# @Project : RealEarthStudio
# @Details : 获取两个标记点的位置


import bpy


def get_marker_positions():
    obj1 = bpy.data.objects.get("空物体")
    obj2 = bpy.data.objects.get("空物体.001")

    if not obj1 or not obj2:
        print("错误：未找到标记点！")
        return None, None

    pos1 = obj1.location.copy()
    pos2 = obj2.location.copy()

    print(f"[{list(pos1)}, {list(pos2)}]")


# 执行
get_marker_positions()
