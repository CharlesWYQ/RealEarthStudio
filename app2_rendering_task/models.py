# python manage.py makemigrations app2_rendering_task
# python manage.py migrate app2_rendering_task
# python manage.py squashmigrations app2_rendering_task 0001 0002

import os
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver
from utils.other import execute_external_python_script

import shutil

from RealEarthStudio import settings
from app1_model_management.models import SceneModelFile, SceneModel, TargetModel
from dirtyfields import DirtyFieldsMixin


# ====== 验证器 ======
def validate_azimuth(value):
    if not (0 <= value <= 360):
        raise ValidationError("方位角必须在 0° 到 360° 之间。")


def validate_elevation(value):
    if not (0 <= value <= 90):
        raise ValidationError("高低角必须在 0° 到 90° 之间。")


def validate_positive_number_list(value):
    """验证是否为正数列表"""
    if not isinstance(value, list):
        raise ValidationError("必须是一个列表。")
    for item in value:
        if not isinstance(item, (int, float)) or item <= 0:
            raise ValidationError("所有值必须是正数。")


def validate_elevation_list(value):
    """验证高低角列表 0-90"""
    if not isinstance(value, list):
        raise ValidationError("必须是一个列表。")
    for item in value:
        if not isinstance(item, (int, float)) or not (0 <= item <= 90):
            raise ValidationError("所有高低角必须在 0° 到 90° 之间。")


# ====== 模型 ======
def rendered_result_path(instance, filename):
    """场景模型上传路径"""
    return os.path.join("Render", f"{instance.render_time}-{instance.render_id}")


def default_camera_distances():
    return [50]


def default_camera_elevations():
    return [45]


class RenderingTask(models.Model, DirtyFieldsMixin):
    # 任务信息
    render_id = models.UUIDField("渲染ID", default=uuid.uuid4, editable=False, unique=True,
                                 help_text="渲染任务的唯一标识")
    RENDER_TYPE = [
        (0, '图像数据集'),
        (1, '点云数据集'),
    ]
    render_type = models.SmallIntegerField("渲染类别", choices=RENDER_TYPE, default=0)
    render_time = models.DateTimeField(verbose_name="渲染时间", default=timezone.now)
    render_progress = models.FloatField("渲染进度", default=0.0, help_text="渲染任务的进度(0-1)")

    # 模型
    scene_models = models.ManyToManyField(SceneModel, verbose_name="场景模型", blank=True,
                                          related_name="rendering_tasks")
    target_models = models.ManyToManyField(TargetModel, verbose_name="目标模型", blank=True,
                                           related_name="rendering_tasks")

    # 日光参数
    sun_azimuth = models.FloatField("日光方位角", default=0.0, validators=[validate_azimuth],
                                    help_text="阳光照射的方位角（0°-360°）")
    sun_elevation = models.FloatField("日光高低角", default=90.0, validators=[validate_elevation],
                                      help_text="阳光照射的高低角（0°-90°）")

    # 相机参数
    camera_distances = models.JSONField("相机距离", default=default_camera_distances, blank=True,
                                        validators=[validate_positive_number_list],
                                        help_text="相机到目标的距离列表（正值）")
    camera_elevations = models.JSONField("相机高低角", default=default_camera_elevations, blank=True,
                                         validators=[validate_elevation_list],
                                         help_text="相机高低角列表（0°-90°）")
    camera_rotation_step = models.FloatField("相机方位角间隔", default=90, validators=[validate_azimuth],
                                             help_text="相机方位角采样间隔（0°-360°）")

    # 渲染分辨率
    image_width = models.PositiveIntegerField("渲染图像分辨率（宽）", default=1920)
    image_height = models.PositiveIntegerField("渲染图像分辨率（高）", default=1080)

    # 渲染器类别
    RENDERER_CHOICES = [
        ('EEVEE', 'EEVEE'),
        ('CYCLES', 'Cycles'),
    ]
    renderer_type = models.CharField("渲染器类别", max_length=10, choices=RENDERER_CHOICES, default='EEVEE')

    # 渲染结果文件
    rendered_result_dir = models.FileField("渲染图像地址",
                                           upload_to=rendered_result_path,
                                           blank=True,
                                           null=True,
                                           help_text="系统自动生成的渲染结果图像（只读）")

    class Meta:
        verbose_name = "01-渲染任务"
        verbose_name_plural = "01-渲染任务"
        ordering = ['-render_time']

    def __str__(self):
        return f"{self.render_id}"

    @property
    def render_status_display(self):
        # 计算属性：渲染状态
        if self.render_progress == 0:
            return "未渲染"
        elif 0 < self.render_progress < 100:
            return "正在渲染"
        else:
            return "完成渲染"

    @property
    def image_pixels(self):
        # 计算属性：总像素数
        return f"{self.image_width * self.image_height / 1e4 :.2f} 万像素"

    def save(self, *args, **kwargs):
        self.full_clean()

        dirty_fields = self.get_dirty_fields()
        if dirty_fields:
            # 检查特定字段是否发生变化
            monitor_fields = ['sun_azimuth', 'sun_elevation', 'camera_distances', 'camera_elevations',
                              'camera_rotation_step', 'image_width', 'image_height', 'renderer_type']

            changed_monitored_fields = [field for field in monitor_fields if field in dirty_fields]
            if changed_monitored_fields:
                delete_dataset(self)
                delete_dataset_in_fifty_one(self)
                if self.render_progress == 1:
                    self.render_progress = 0

        if not self.pk:
            # 创建目录（如果不存在）
            full_dir = os.path.join(settings.MEDIA_ROOT, "Render", str(self.render_id))
            os.makedirs(full_dir, exist_ok=True)

            # 设置 rendered_result 字段
            self.rendered_result_dir = full_dir

        super().save(*args, **kwargs)


@receiver(post_delete, sender=RenderingTask)
def delete_rendering_task_files(sender, instance, **kwargs):
    """
    渲染任务删除后，同时删除其对应的渲染结果文件夹
    """
    delete_dataset(instance)
    delete_dataset_in_fifty_one(instance)


def handle_m2m_change(sender, instance, action, **kwargs):
    """
    统一处理多对多关系变化
    """
    delete_dataset(instance)
    delete_dataset_in_fifty_one(instance)
    instance.render_progress = 0
    instance.save()


@receiver(m2m_changed, sender=RenderingTask.target_models.through)
def target_models_changed(sender, instance, action, **kwargs):
    """
    监听 target_models 多对多关系变化
    """
    handle_m2m_change(sender, instance, action, **kwargs)


@receiver(m2m_changed, sender=RenderingTask.scene_models.through)
def scene_models_changed(sender, instance, action, **kwargs):
    """
    监听 scene_models 多对多关系变化
    """
    handle_m2m_change(sender, instance, action, **kwargs)


def delete_dataset(instance):
    """
    删除数据集
    """
    if instance.rendered_result_dir:
        folder_dir = instance.rendered_result_dir.path
        if os.path.isdir(folder_dir):
            shutil.rmtree(folder_dir)


def delete_dataset_in_fifty_one(instance):
    """
    删除FiftyOne数据集
    """
    if instance.rendered_result_dir:
        folder_dir = instance.rendered_result_dir.path
        if instance.render_progress == 1:
            script_path = os.path.join(settings.BASE_DIR, "utils", "fifty_one", "delete_datasets.py")
            dataset_path = os.path.join(folder_dir, "Dataset")
            dataset_name = str(instance.render_id)
            execute_external_python_script.main(settings.FIFTYONE_ENV, script_path, dataset_path, dataset_name)
