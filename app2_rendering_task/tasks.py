# -*- coding: utf-8 -*-
# @Time : 2025/12/17 上午11:00
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : tasks.py
# @Project : RealEarthStudio
# @Details : 定义异步任务


from django.conf import settings
from celery import shared_task
import os
from django.utils import timezone
from .models import RenderingTask

from utils.rearth import SceneRenderer
from utils.other import execute_external_python_script


@shared_task
def execute_render_task(render_id):
    """
    异步执行渲染任务
    """
    try:
        print(f"⭕ 渲染任务：{render_id} 开始渲染")
        render_task = RenderingTask.objects.get(render_id=render_id)
        render_task.render_progress = 0
        render_task.save()

        # 写入信息文件
        os.makedirs(render_task.rendered_result_dir.path, exist_ok=True)
        full_filepath = os.path.join(render_task.rendered_result_dir.path, "info.txt")
        with open(full_filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== 渲染任务信息 ===\n")
            f.write(f"渲染任务ID: {render_task.render_id}\n")
            f.write(f"渲染时间: {render_task.render_time.astimezone(timezone.get_default_timezone())}\n")
            f.write(f"渲染器类型: {render_task.renderer_type}\n")
            f.write(f"图像分辨率: {render_task.image_width} × {render_task.image_height}\n")
            f.write(f"总像素数: {render_task.image_pixels}\n\n")

            f.write(f"=== 模型信息 ===\n")
            scene_model_list = []
            scene_models_num = render_task.scene_models.count()
            f.write(f"场景模型数量: {scene_models_num}\n")
            if render_task.scene_models.exists():
                for i, scene_model in enumerate(render_task.scene_models.all(), 1):
                    all_categories = get_parent_categories(set(scene_model.scene_model.category.all()))
                    all_categories = [str(cat.name) for cat in all_categories]
                    category_names = ", ".join(all_categories)
                    f.write(f"  场景模型{i}: {scene_model.scene_model.model_id} ({category_names})\n")

                    scene_model_list.append({
                        "path": scene_model.scene_model.file.path,
                        "class": all_categories,
                        "points": scene_model.points,
                    })

            target_model_list = []
            target_models_num = render_task.target_models.count()
            f.write(f"目标模型数量: {target_models_num}\n")
            if render_task.target_models.exists():
                for i, target_model in enumerate(render_task.target_models.all(), 1):
                    all_categories = get_parent_categories(set(target_model.category.all()))
                    all_categories = [str(cat.name) for cat in all_categories]
                    category_names = ", ".join(all_categories)
                    f.write(f"  目标模型{i}: {target_model.model_id} ({category_names})\n")

                    target_model_list.append({
                        "path": target_model.file.path,
                        "class": all_categories,
                    })

            f.write(f"\n=== 光照参数 ===\n")
            f.write(f"日光方位角: {render_task.sun_azimuth}°\n")
            f.write(f"日光高低角: {render_task.sun_elevation}°\n\n")

            f.write(f"=== 相机参数 ===\n")
            f.write(f"相机距离列表: {render_task.camera_distances}\n")
            f.write(f"相机高低角列表: {render_task.camera_elevations}\n")
            f.write(f"相机方位角间隔: {render_task.camera_rotation_step}°\n\n")
        render_task.render_progress = 0.1
        render_task.save()

        # 开始渲染
        config = {
            "render_id": "Dataset",
            "scene_model": None,
            "target_model_list": None,
            "output_dir": render_task.rendered_result_dir.path,
            "renderer": render_task.renderer_type,
            "resolution": [render_task.image_width, render_task.image_height],
            "sun_azimuth_deg": render_task.sun_azimuth,
            "sun_elevation_deg": render_task.sun_elevation,
            "camera_distances": render_task.camera_distances,
            "camera_elevations": render_task.camera_elevations,
            "camera_rotation_step_deg": render_task.camera_rotation_step,
            "index": None,
        }

        index = 0
        render_task_index = 0
        render_task_num = scene_models_num
        delta_progress = 1 / render_task_num * 0.8

        for scene_model in scene_model_list:
            render_task_index += 1
            print(f"➡️ ========== 渲染场景 {render_task_index} / {render_task_num} 开始 ==========")
            config.update({
                "scene_model": scene_model,
                "target_model_list": target_model_list,
                "index": index,
            })
            index, _ = SceneRenderer.main(config)
            render_task.render_progress += delta_progress
            render_task.save()
            print(f"🔆 ========== 渲染场景 {render_task_index} / {render_task_num} 完成 ==========")

        # 导入FiftyOne
        print(f"➡️ 导入数据集 {render_id} 到FiftyOne")
        script_path = os.path.join(settings.BASE_DIR, "utils", "fifty_one", "show_in_fiftyone.py")
        dataset_path = os.path.join(render_task.rendered_result_dir.path, "Dataset")
        dataset_name = str(render_id)
        execute_external_python_script.main(settings.FIFTYONE_ENV, script_path, dataset_path, dataset_name)
        print("🔆 数据集导入FiftyOne完成")

        render_task.render_progress = 1
        render_task.save()

        return f"\n⭕ 渲染任务：{render_id} 完成渲染"
    except Exception as e:
        import logging
        logging.error(f"渲染失败: {str(e)}")
        return f"\n❌ 渲染任务：{render_id} 渲染失败"


def get_parent_categories(all_categories):
    for cat in list(all_categories):
        parent = cat.parent
        while parent:
            all_categories.add(parent)
            parent = parent.parent
    return sorted(list(all_categories), key=lambda x: x.level)
