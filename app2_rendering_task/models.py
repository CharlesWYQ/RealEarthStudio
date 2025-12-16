# python manage.py makemigrations app2_rendering_task
# python manage.py migrate app2_rendering_task

import os
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import shutil

from RealEarthStudio import settings
from app1_model_management.models import TargetModel, SceneModel


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


class RenderingTask(models.Model):
    # 任务信息
    render_id = models.UUIDField("渲染ID", default=uuid.uuid4, editable=False, unique=True,
                                 help_text="渲染任务的唯一标识")
    render_time = models.DateTimeField(verbose_name="渲染时间", default=timezone.now)
    render_progress = models.FloatField("渲染进度", default=0.0, help_text="渲染任务的进度百分比(0-100)")

    # 模型
    target_models = models.ManyToManyField(TargetModel, verbose_name="目标模型", blank=True,
                                           related_name="rendering_tasks")
    scene_models = models.ManyToManyField(SceneModel, verbose_name="场景模型", blank=True,
                                          related_name="rendering_tasks")

    # 日光参数
    sun_azimuth = models.FloatField("日光方位角", default=0.0, validators=[validate_azimuth],
                                    help_text="阳光照射的方位角（0°-360°）")
    sun_elevation = models.FloatField("日光高低角", default=90.0, validators=[validate_elevation],
                                      help_text="阳光照射的高低角（0°-90°）")

    # 相机参数
    camera_distances = models.JSONField("相机距离", default=[100], blank=True,
                                        validators=[validate_positive_number_list],
                                        help_text="相机到目标的距离列表（正值）")
    camera_elevations = models.JSONField("相机高低角", default=[45], blank=True, validators=[validate_elevation_list],
                                         help_text="相机高低角列表（0°-90°）")
    camera_rotation_step = models.FloatField("相机方位角间隔", default=45.0, validators=[validate_azimuth],
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
    rendered_result = models.FileField("渲染图像地址",
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
        return self.image_width * self.image_height

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.pk and not self.rendered_result:
            # 创建目录（如果不存在）
            full_dir = os.path.join(settings.MEDIA_ROOT, "Render", str(self.render_id))
            os.makedirs(full_dir, exist_ok=True)

            # 设置 rendered_result 字段
            self.rendered_result = full_dir

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.rendered_result:
            # 获取文件的绝对路径
            folder_dir = self.rendered_result.path
            # 如果文件存在则删除
            if os.path.isdir(folder_dir):
                shutil.rmtree(folder_dir)
        # 调用父类的delete方法删除数据库记录
        super().delete(*args, **kwargs)

# @receiver(post_save, sender=RenderingTask)
# def update_rendering_info(sender, instance, created, **kwargs):
#     """在RenderingTask完全保存后更新信息文件"""
#     print(instance.target_models.all())
#     if created:
#         # 创建占位txt文件
#         full_dir = os.path.join(settings.MEDIA_ROOT, "Render", str(instance.render_id))
#         print(full_dir)
#         print(instance.target_models)
# full_filepath = os.path.join(full_dir, "info.txt")
# with open(full_filepath, 'w', encoding='utf-8') as f:
#     f.write(f"=== 渲染任务信息 ===\n")
#     f.write(f"渲染任务ID: {self.render_id}\n")
#     f.write(f"渲染时间: {self.render_time.astimezone(timezone.get_default_timezone())}\n")
#     f.write(f"渲染器类型: {self.renderer_type}\n")
#     f.write(f"图像分辨率: {self.image_width} x {self.image_height}\n")
#     f.write(f"总像素数: {self.image_pixels}\n\n")
#
#     f.write(f"=== 模型信息 ===\n")
#     f.write(f"目标模型数量: {self.target_models.count()}\n")
#     if self.target_models.exists():
#         for i, target_model in enumerate(self.target_models.all(), 1):
#             f.write(f"  目标模型{i}: {target_model.model_id}\n")
#
#     f.write(f"场景模型数量: {self.scene_models.count()}\n")
#     if self.scene_models.exists():
#         for i, scene_model in enumerate(self.scene_models.all(), 1):
#             f.write(f"  场景模型{i}: {scene_model.model_id}\n")
#
#     f.write(f"\n=== 光照参数 ===\n")
#     f.write(f"日光方位角: {self.sun_azimuth}°\n")
#     f.write(f"日光高低角: {self.sun_elevation}°\n\n")
#
#     f.write(f"=== 相机参数 ===\n")
#     f.write(f"相机距离列表: {self.camera_distances}\n")
#     f.write(f"相机高低角列表: {self.camera_elevations}\n")
#     f.write(f"相机方位角间隔: {self.camera_rotation_step}°\n\n")
