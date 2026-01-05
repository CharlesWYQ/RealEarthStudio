# -*- coding: utf-8 -*-
# @Time : 2025/11/25 上午10:38
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : SceneRenderer.py
# @Project : RealEarthStudio
# @Details : 


import os
import datetime
import random
import string
import bpy
import math
import json
from mathutils import Vector, Matrix
from pathlib import Path
import numpy as np

from utils.other.decorator_timer import timer
from bpy_extras.object_utils import world_to_camera_view


class SceneRenderer:
    """ 场景渲染 """

    def __init__(self, scene_model, target_model_list, render_id=None,
                 output_dir=r"D:\Projects\RealEarthStudio\Blender照片", index=0):
        """
        初始化对象
        :param scene_model: 场景模型
        :param target_model_list: 目标模型
        :param output_dir: 渲染图像导出目录
        :param index: 已经渲染图像数量
        """
        # 生成渲染ID
        self.render_id = render_id if render_id else self.generate_render_id()

        # 获取输出文件夹
        self.output_dir = os.path.join(output_dir, self.render_id)
        self.annotations_file = os.path.join(self.output_dir, "metadata.json")

        # 导入场景模型
        self.scene_model_name = Path(scene_model["path"]).stem
        self.scene_model_class = scene_model["class"]
        self.scene_model_point = scene_model["points"]
        if self.scene_model_point is None:
            self.scene_model_point = [[0, 0, 0], [0, 1, 0]]
        self.bpy = self.load_scene_model(scene_model["path"])
        self.scene = self.bpy.context.scene

        # 导入目标模型
        self.target_model_list = target_model_list
        self.target_model_name = None
        self.target_model_class = None
        self.target_obj = None

        # 添加初始光照
        sun_height = 100
        self.bpy.ops.object.light_add(type='SUN', location=(0, 0, sun_height))
        self.sun_obj = bpy.context.active_object
        self.sun_obj.name = "mainSun"

        self.sun_energy = None
        self.sun_azimuth_deg = None
        self.sun_elevation_deg = None
        self.configure_sun()

        # 创建相机
        self.bpy.ops.object.camera_add(location=(0, 0, 0))
        self.camera_obj = bpy.context.active_object
        self.bpy.context.scene.camera = self.camera_obj

        # 初始化分辨率及图片格式
        self.set_resolution()
        self.scene.render.image_settings.file_format = "PNG"

        # 初始化渲染器
        self.renderer = None
        self.set_renderer("EEVEE")

        # 初始化标注信息
        self.annotation_lines = {}

        # 初始化索引
        self.index = index

    @staticmethod
    def generate_render_id():
        # 获取当前时间并格式化为渲染ID
        now = datetime.datetime.now()
        time_str = now.strftime("%Y%m%d_%H%M%S")

        # 生成 6 位随机字母（大小写）+ 数字
        chars = string.ascii_letters + string.digits
        random_suffix = ''.join(random.choices(chars, k=6))

        return f"{time_str}_{random_suffix}"

    def load_scene_model(self, scene_model_path):
        """
        导入场景模型
        """
        # 确保模型文件存在
        if not os.path.exists(scene_model_path):
            raise FileNotFoundError(f"场景模型文件不存在: {scene_model_path}")

        ext = scene_model_path.split('.')[-1].lower()
        if ext == "fbx":
            # 清空当前场景
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False, confirm=False)

            # 导入场景模型
            bpy.ops.import_scene.fbx(filepath=scene_model_path)
        elif ext == "blend":
            # 导入场景模型
            bpy.ops.wm.open_mainfile(filepath=scene_model_path)
        else:
            raise FileNotFoundError(f"不支持的场景模型格式: {scene_model_path}")

        if self.scene_model_point != [[0, 0, 0], [0, 1, 0]]:
            p1 = Vector(self.scene_model_point[0])
            p2 = Vector(self.scene_model_point[1])
            direction = p2 - p1
            dir_xy = Vector((direction.x, direction.y, 0.0))
            if dir_xy.length == 0:
                pass
            else:
                delta_angle = -math.pi / 2 - math.atan2(dir_xy.y, dir_xy.x)
                while delta_angle > math.pi:
                    delta_angle -= 2 * math.pi
                while delta_angle < -math.pi:
                    delta_angle += 2 * math.pi
                rot_matrix = Matrix.Rotation(delta_angle, 4, 'Z')
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=p1)
                parent_empty = bpy.context.active_object
                parent_empty.name = "sceneModel"

                mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
                for obj in mesh_objects:
                    world_mat = obj.matrix_world.copy()
                    obj.parent = parent_empty
                    obj.matrix_world = world_mat

                # 安全应用旋转：保留位置和缩放
                scale = parent_empty.scale.copy()

                # 应用相对旋转（乘以当前矩阵）
                parent_empty.matrix_world @= rot_matrix

                # 恢复位置和缩放（防止浮点误差）
                parent_empty.scale = scale
                parent_empty.location = (0, 0, 0)
        print(f"✅ 场景模型 {self.scene_model_name} 导入成功")
        return bpy

    def load_target_model(self, target_model):
        """
        导入目标模型
        """
        target_model_path = target_model["path"]

        # 导入目标模型
        if not os.path.exists(target_model_path):
            raise FileNotFoundError(f"目标模型文件不存在: {target_model_path}")
        self.target_model_name = Path(target_model_path).stem

        target_model_class = target_model["class"]
        self.target_model_class = target_model_class

        # 在导入新模型前先删除可能存在的旧模型对象
        existing_target = self.bpy.data.objects.get("targetModel")
        if existing_target:
            self.bpy.data.objects.remove(existing_target, do_unlink=True)

        self.bpy.ops.import_scene.fbx(filepath=target_model_path)
        for obj in self.bpy.context.selected_objects:
            if obj.type == 'MESH':
                obj.name = "targetModel"
                break

        self.target_obj = self.bpy.data.objects.get("targetModel")
        if not self.target_obj:
            raise ValueError("场景中未找到目标对象！")
        print(f"✅ 目标模型 {self.target_model_name} 导入成功")

    def export_blender_file(self, file_dir, file_name="导出模型.blend"):
        """
        导出到Blender文件
        :param file_dir: 导出文件路径
        :param file_name: 文件名
        """
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, file_name)
        self.bpy.ops.wm.save_as_mainfile(filepath=file_path)

    def configure_sun(self, energy=5.0, azimuth_deg=0.0, elevation_deg=90.0):
        """
        调整日光参数
        :param energy: 光照强度
        :param azimuth_deg: 水平方向角度 (0°:从+Y方向照射, 90°:从-X方向照射)
        :param elevation_deg: 仰角(0°:平行地面, 90°:垂直向下)
        """
        self.sun_energy = energy
        self.sun_azimuth_deg = azimuth_deg
        self.sun_elevation_deg = elevation_deg
        self.sun_obj.data.energy = energy

        # 将角度转换为弧度
        az_rad = math.radians(azimuth_deg)
        el_rad = math.radians(-elevation_deg)

        # 计算方向向量（单位向量）,先在 XZ 平面投影，再考虑仰角
        dir_x = math.cos(el_rad) * math.sin(az_rad)
        dir_y = math.cos(el_rad) * math.cos(az_rad)
        dir_z = math.sin(el_rad)  # 仰角决定 Z 分量

        # 让光源朝向 (dir_x, dir_y, dir_z)
        look_at = Vector((dir_x, dir_y, dir_z))
        rot_quat = look_at.to_track_quat('-Z', 'Y')  # -Z是光的前向，Y是上向
        self.sun_obj.rotation_mode = 'QUATERNION'
        self.sun_obj.rotation_quaternion = rot_quat

    def configure_camara(self, x, y, z):
        """
        修改相机参数
        :param x: X轴坐标
        :param y: Y轴坐标
        :param z: Z轴坐标
        """
        # 调整相机位置
        self.camera_obj.location = (x, y, z)

        # 对准原点
        direction = Vector((0, 0, 0)) - self.camera_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        self.camera_obj.rotation_euler = rot_quat.to_euler()

    def set_renderer(self, renderer):
        """
        修改渲染器
        :param renderer: 渲染器类型
        """
        self.renderer = renderer.upper()
        prefs = self.bpy.context.preferences
        self.scene.render.use_simplify = True

        if self.renderer == "CYCLES":
            # 设置渲染引擎为 Cycles
            self.scene.render.engine = 'CYCLES'
            self.scene.cycles.samples = 64  # 降低采样加快速度
            self.scene.cycles.preview_samples = 16
            self.scene.cycles.use_camera_cull = True  # 使用相机裁剪

            # 确保 cycles 插件启用
            if "cycles" not in prefs.addons:
                self.bpy.ops.preferences.addon_enable(module='cycles')
            cycles_prefs = prefs.addons["cycles"].preferences

            # 刷新设备列表
            try:
                cycles_prefs.get_devices()
            except Exception as e:
                print(f"⚠️ 获取设备失败: {e}")
                return False

            # 查看可用设备类型
            available_types = {d.type for d in cycles_prefs.devices}
            print(f"🔍 可用的设备类型: {available_types}")

            # 选择后端（OptiX > CUDA）
            backend_selected = None
            for backend in ['OPTIX', 'CUDA', 'METAL', 'HIP']:
                if backend in available_types:
                    if hasattr(cycles_prefs, 'compute_device_type'):
                        cycles_prefs.compute_device_type = backend
                        backend_selected = backend
                        print(f"✅ 使用渲染设备: {backend}")
                    break

            if not backend_selected:
                print("❌ 无GPU渲染设备可用.")
                self.scene.cycles.device = 'CPU'
                return False

            # 启用所有非CPU设备
            gpu_found = False
            for device in cycles_prefs.devices:
                if device.type == "CPU":
                    device.use = False
                    print(f"🚫 禁用CPU: {device.name}")
                else:
                    device.use = True
                    gpu_found = True
                    print(f"✅ 启用GPU: {device.name} ({device.type})")

            # 设置 GPU 渲染
            self.scene.cycles.device = 'GPU' if gpu_found else 'CPU'
            print(f"🔧 CYCLES渲染设备设置为: {self.scene.cycles.device}")

        else:
            self.scene.render.engine = 'BLENDER_EEVEE'

    def set_resolution(self, width=1920, height=1080):
        """
        修改分辨率及图像格式
        :param width: 宽度
        :param height: 高度
        """
        self.scene.render.resolution_x = width
        self.scene.render.resolution_y = height

    def get_visible_info(self, occlusion_threshold=0.8, sample_rate=0.1):
        """
        使用射线投射快速判断目标是否可见（遮挡比例 <= threshold）
        返回: (is_visible: bool, occlusion_ratio: float, bbox: (cx,cy,w,h) or None)
        """
        camera_loc = self.camera_obj.matrix_world.translation
        deps_graph = bpy.context.evaluated_depsgraph_get()

        # 获取目标顶点（世界坐标）
        eval_obj = self.target_obj.evaluated_get(deps_graph)
        mesh = eval_obj.to_mesh()
        vertices_world = [self.target_obj.matrix_world @ v.co for v in mesh.vertices]
        eval_obj.to_mesh_clear()

        if not vertices_world:
            return False, 1.0, None

        # 随机采样
        num_vertices = len(vertices_world)
        sample_count = max(50, int(num_vertices * sample_rate))
        indices = np.random.choice(num_vertices, size=min(sample_count, num_vertices), replace=False)
        sampled_points = [vertices_world[i] for i in indices]

        visible_2d = []
        occluded = 0

        for pt in sampled_points:
            direction = (pt - camera_loc).normalized()
            # 射线投射（忽略目标自身）
            result, location, normal, index, hit_obj, matrix = self.scene.ray_cast(
                deps_graph, camera_loc, direction, distance=(pt - camera_loc).length - 1e-4
            )

            if not result or hit_obj == self.target_obj:
                # 无遮挡，或仅击中自己（视为可见）
                co_2d = world_to_camera_view(self.scene, self.camera_obj, pt)
                if 0 <= co_2d.x <= 1 and 0 <= co_2d.y <= 1 and co_2d.z > 0:
                    visible_2d.append((co_2d.x, co_2d.y))
            else:
                occluded += 1

        total = len(sampled_points)
        if total == 0:
            return False, 1.0, None

        occlusion_ratio = occluded / total
        is_visible = occlusion_ratio <= occlusion_threshold

        # 计算 bbox（仅基于可见点）
        if visible_2d:
            xs = [p[0] for p in visible_2d]
            ys = [p[1] for p in visible_2d]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            cx = (x_min + x_max) / 2
            cy = 1 - (y_min + y_max) / 2
            w = x_max - x_min
            h = y_max - y_min
            bbox = (float(cx), float(cy), float(w), float(h))
        else:
            bbox = None

        return is_visible, occlusion_ratio, bbox

    def annotations_to_json(self, filename, distance, elevation_deg, azimuth_deg, cx, cy, w, h, occlusion_ratio):
        """
        将标注信息导出为JSON格式
        :param filename: 文件名
        :param distance: 摄像机与目标模型的距离
        :param elevation_deg: 摄像机与目标模型的仰角
        :param azimuth_deg: 摄像机环绕拍摄时的角度间隔
        :param cx: 归一化标注框（图像中心x）
        :param cy: 归一化标注框（图像中心y）
        :param w: 归一化图像宽度
        :param h: 归一化图像高度
        :param occlusion_ratio: 遮挡概率
        """
        self.annotation_lines.update({
            filename: [
                {
                    "target_name": self.target_model_name,
                    "target_class": self.target_model_class,
                    "scene_name": self.scene_model_name,
                    "scene_class": self.scene_model_class,
                    "sun_energy": self.sun_energy,
                    "sun_azimuth_deg": self.sun_azimuth_deg,
                    "sun_elevation_deg": self.sun_elevation_deg,
                    "distance": distance,
                    "elevation_deg": elevation_deg,
                    "azimuth_deg": azimuth_deg,
                    "bbox": [cx, cy, w, h],
                    "occlusion": occlusion_ratio,
                    "renderer": self.renderer,
                }
            ],
        })

    def render_with_annotations(self, distance, elevation_deg, rotation_step_deg=45):
        """
        导出渲染图像与标注信息
        :param distance: 摄像机与目标模型的距离
        :param elevation_deg: 摄像机与目标模型的仰角
        :param rotation_step_deg: 摄像机环绕拍摄时的角度间隔
        """
        # 确保数据集导出文件夹存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 计算环绕角度
        angles = []
        current = 0
        while current < 360:
            angles.append(current)
            current += rotation_step_deg
        angles = sorted(set(angles))

        # 调整相机
        for azimuth_deg in angles:
            # 计算相机位置
            elevation_deg = 89 if elevation_deg >= 90 else elevation_deg
            elev = math.radians(elevation_deg)
            azim = math.radians(azimuth_deg)
            x = distance * math.cos(elev) * math.sin(azim)
            y = distance * math.cos(elev) * math.cos(azim)
            z = distance * math.sin(elev)
            self.configure_camara(x, y, z)

            # 检测遮挡与 bbox
            result = self.get_visible_info()
            if not result[0]:
                print(f"⚠️ 相机距离 {distance} 米，高低角 {elevation_deg}°，视角 {azimuth_deg}°：目标不可见，跳过保存")
                continue

            is_visible, occlusion_ratio, (cx, cy, w, h) = result
            if occlusion_ratio > 0.6:
                print(
                    f"❌ 相机距离 {distance} 米，高低角 {elevation_deg}°，视角 {azimuth_deg}°：遮挡比例过高，跳过保存 | 遮挡比例: {occlusion_ratio:.2%}")
                continue

            # 保存图像
            self.index += 1
            filename = f"image_{self.index:04d}.png"
            self.scene.render.filepath = os.path.join(self.output_dir, filename)
            self.bpy.ops.render.render(write_still=True)

            # 保存标注信息
            self.annotations_to_json(filename, distance, elevation_deg, azimuth_deg, cx, cy, w, h, occlusion_ratio)

            print(
                f"✅ 相机距离 {distance} 米，高低角 {elevation_deg}°，视角 {azimuth_deg}°：已保存 {filename} | 遮挡比例: {occlusion_ratio:.2%}")

        # 保存标注文件
        if not os.path.exists(self.annotations_file):
            with open(self.annotations_file, 'w', encoding="utf-8") as f:
                json.dump(self.annotation_lines, f, indent=4)
        else:
            with open(self.annotations_file, 'r+', encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                    existing_data.update(self.annotation_lines)
                    f.seek(0)
                    f.truncate()
                    json.dump(existing_data, f, indent=4)
                except json.JSONDecodeError:
                    f.seek(0)
                    f.truncate()
                    json.dump(self.annotation_lines, f, indent=4)
        print(f"📄 标注文件已保存: {self.annotations_file}")

    def batch_render_with_annotations(self, distance_list: list, elevation_deg_list: list, rotation_step_deg=45):
        """
        批量导出渲染图像与标注信息
        :param distance_list: 摄像机与目标模型的距离列表
        :param elevation_deg_list: 摄像机与目标模型的仰角列表
        :param rotation_step_deg: 摄像机环绕拍摄时的角度间隔
        """
        render_task_index = 0
        render_target_num = len(self.target_model_list)
        for target_model in self.target_model_list:
            render_task_index += 1
            print(f"➡️ ---------- 渲染目标 {render_task_index} / {render_target_num} 开始 ----------")
            self.load_target_model(target_model)
            for distance in distance_list:
                for elevation_deg in elevation_deg_list:
                    self.render_with_annotations(distance, elevation_deg, rotation_step_deg)
            print(f"🔆 ---------- 渲染目标 {render_task_index} / {render_target_num} 完成 ----------")


@timer
def main(config: dict):
    scene_renderer_object = SceneRenderer(config['scene_model'], config['target_model_list'],
                                          render_id=config['render_id'], output_dir=config['output_dir'],
                                          index=config['index'])

    # 修改日光参数
    scene_renderer_object.configure_sun(azimuth_deg=config['sun_azimuth_deg'],
                                        elevation_deg=config['sun_elevation_deg'])

    # 保存模型
    # scene_renderer_object.export_blender_file(scene_renderer_object.output_dir,
    #                                           f'image_{scene_renderer_object.index + 1:04d}.blend')

    # 修改分辨率
    scene_renderer_object.set_resolution(config['resolution'][0], config['resolution'][1])

    # 修改渲染器
    scene_renderer_object.set_renderer(config['renderer'])

    # 批量渲染
    scene_renderer_object.batch_render_with_annotations(config['camera_distances'], config['camera_elevations'],
                                                        config['camera_rotation_step_deg'])

    return scene_renderer_object.index, scene_renderer_object.render_id


if __name__ == '__main__':
    CONFIG = {
        "render_id": None,
        "scene_model": {
            "path": r"D:\Projects\RealEarthStudio\Blender场景模型\street_0001.fbx",
            "class": ["道路"],
            "points": [[186.8546142578125, -63.27665328979492, 97.02672576904297],
                       [179.08160400390625, -63.395328521728516, 97.14110565185547]]
        },
        "target_model_list": [
            {
                "path": r"D:\Projects\RealEarthStudio\Blender目标模型\01\宾利.000.fbx",
                "class": ['宾利', '车辆']
            },
            {
                "path": r"D:\Projects\RealEarthStudio\Blender目标模型\01\宝马-Z4.000.fbx",
                "class": ['宝马', '车辆']
            }
        ],
        "output_dir": r"D:\Projects\RealEarthStudio\Blender照片",
        "renderer": "eevee",
        "resolution": [1920, 1080],
        "sun_azimuth_deg": 45,
        "sun_elevation_deg": 60,
        "camera_distances": [20],
        "camera_elevations": [30],
        "camera_rotation_step_deg": 180,
        "index": 0,
    }
    _index, _render_id = main(CONFIG)
    print(f"渲染任务 {_render_id} 已渲染 {_index} 张图片")
