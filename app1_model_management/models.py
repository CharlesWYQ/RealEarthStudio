from django.db import models
from django.utils import timezone
import uuid
import os


def get_model_upload_path(prefix, instance, filename):
    """
    模型文件上传路径生成函数
    :param prefix: 路径前缀，如 "TargetModels" 或 "SceneModels"
    :param instance: 模型实例
    :param filename: 原始文件名
    :return: 上传路径
    """
    ext = filename.split('.')[-1].lower()
    if ext != 'fbx':
        ext = 'fbx'
    return os.path.join("Models", prefix, instance.category, f"{instance.model_id}.{ext}")


def target_model_upload_path(instance, filename):
    """目标模型上传路径"""
    return get_model_upload_path("TargetModels", instance, filename)


def scene_model_upload_path(instance, filename):
    """场景模型上传路径"""
    return get_model_upload_path("SceneModels", instance, filename)


class TargetModel(models.Model):
    model_id = models.CharField(verbose_name="模型ID", max_length=36, unique=True, editable=False)
    uploaded_at = models.DateTimeField(verbose_name="上传时间", default=timezone.now)
    category = models.CharField(verbose_name="模型类别", max_length=100, help_text="模型所属的类别")
    file = models.FileField(
        verbose_name="模型文件",
        upload_to=target_model_upload_path,
        help_text="请上传 *.fbx 格式的3D模型文件"
    )

    class Meta:
        verbose_name = "01-目标模型"
        verbose_name_plural = "01-目标模型"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.model_id} ({self.category})"

    def save(self, *args, **kwargs):
        # 如果这是现有对象且文件字段被修改，则删除旧文件
        if self.pk:  # 检查是否为现有对象
            try:
                old_instance = TargetModel.objects.get(pk=self.pk)
                # 如果文件字段发生变化，删除旧文件
                if old_instance.file and old_instance.file != self.file:
                    if os.path.isfile(old_instance.file.path):
                        os.remove(old_instance.file.path)
            except SceneModel.DoesNotExist:
                pass  # 新对象，无需处理

        # 设置model_id（如果是新对象）
        if not self.model_id:
            self.model_id = str(uuid.uuid4())

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 删除文件系统中的文件
        if self.file:
            # 获取文件的绝对路径
            file_path = self.file.path
            # 如果文件存在则删除
            if os.path.isfile(file_path):
                os.remove(file_path)
        # 调用父类的delete方法删除数据库记录
        super().delete(*args, **kwargs)


class SceneModel(models.Model):
    model_id = models.CharField(verbose_name="模型ID", max_length=36, unique=True, editable=False)
    uploaded_at = models.DateTimeField(verbose_name="上传时间", default=timezone.now)
    category = models.CharField(verbose_name="模型类别", max_length=100, help_text="模型所属的类别")
    file = models.FileField(
        verbose_name="模型文件",
        upload_to=scene_model_upload_path,
        help_text="请上传 *.fbx 格式的3D模型文件"
    )

    class Meta:
        verbose_name = "02-场景模型"
        verbose_name_plural = "02-场景模型"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.model_id} ({self.category})"

    def save(self, *args, **kwargs):
        # 如果这是现有对象且文件字段被修改，则删除旧文件
        if self.pk:  # 检查是否为现有对象
            try:
                old_instance = SceneModel.objects.get(pk=self.pk)
                # 如果文件字段发生变化，删除旧文件
                if old_instance.file and old_instance.file != self.file:
                    if os.path.isfile(old_instance.file.path):
                        os.remove(old_instance.file.path)
            except SceneModel.DoesNotExist:
                pass  # 新对象，无需处理

        # 设置model_id（如果是新对象）
        if not self.model_id:
            self.model_id = str(uuid.uuid4())

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 删除文件系统中的文件
        if self.file:
            # 获取文件的绝对路径
            file_path = self.file.path
            # 如果文件存在则删除
            if os.path.isfile(file_path):
                os.remove(file_path)
        # 调用父类的delete方法删除数据库记录
        super().delete(*args, **kwargs)
