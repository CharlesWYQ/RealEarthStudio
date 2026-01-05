# python manage.py makemigrations app1_model_management
# python manage.py migrate app1_model_management
# python manage.py squashmigrations app1_model_management 0009 0012

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
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
    return os.path.join("Models", prefix, f"{instance.model_id}.{ext}")


def scene_model_upload_path(instance, filename):
    """场景模型上传路径"""
    return get_model_upload_path("SceneModels", instance, filename)


def target_model_upload_path(instance, filename):
    """目标模型上传路径"""
    return get_model_upload_path("TargetModels", instance, filename)


class Category(models.Model):
    MODEL_TYPE_CHOICES = [
        ('target', '目标模型分类'),
        ('scene', '场景模型分类'),
        ('general', '通用分类'),
    ]
    model_type = models.CharField(
        "标签类别",
        max_length=10,
        choices=MODEL_TYPE_CHOICES,
        default='target',
        help_text="指定该分类适用于哪种模型类型"
    )
    name = models.CharField("分类名称", max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="父级分类"
    )
    level = models.PositiveSmallIntegerField("层级", default=0, editable=False)

    class Meta:
        verbose_name = "01-分类标签"
        verbose_name_plural = "01-分类标签"
        ordering = ['model_type', 'level', 'name']

    def __str__(self):
        # 显示完整路径
        return self.full_name()

    def full_name(self):
        # 递归生成完整路径
        if self.parent:
            return f"{self.parent.full_name()} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        # 自动计算层级
        self.level = self.parent.level + 1 if self.parent else 0
        super().save(*args, **kwargs)

    @property
    def is_leaf(self):
        # 是否为叶子节点（无子分类）
        return not self.children.exists()


class SceneModelFile(models.Model):
    model_id = models.UUIDField(verbose_name="模型ID", default=uuid.uuid4, editable=False, unique=True,
                                help_text="场景模型的唯一标识")
    uploaded_at = models.DateTimeField(verbose_name="上传时间", default=timezone.now)
    category = models.ManyToManyField(verbose_name="模型类别", to=Category, blank=True, help_text="模型所属的类别")
    file = models.FileField(
        verbose_name="模型文件",
        upload_to=scene_model_upload_path,
        help_text="请上传 *.blend 格式的3D模型文件",
        validators=[FileExtensionValidator(allowed_extensions=['blend', 'fbx'])]
    )

    class Meta:
        verbose_name = "02-场景模型文件"
        verbose_name_plural = "02-场景模型文件"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{'、'.join([obj.name for obj in self.category.all()])} ({self.model_id})"

    def save(self, *args, **kwargs):
        # 如果这是现有对象且文件字段被修改，则删除旧文件
        if self.pk:  # 检查是否为现有对象
            try:
                old_instance = SceneModelFile.objects.get(pk=self.pk)
                # 如果文件字段发生变化，删除旧文件
                if old_instance.file and old_instance.file != self.file:
                    if os.path.isfile(old_instance.file.path):
                        os.remove(old_instance.file.path)
            except SceneModelFile.DoesNotExist:
                pass  # 新对象，无需处理
        super().save(*args, **kwargs)


def default_points():
    return [[0, 0, 0], [0, 1, 0]]


class SceneModel(models.Model):
    scene_id = models.UUIDField(verbose_name="场景ID", default=uuid.uuid4, editable=False, unique=True,
                                help_text="场景的唯一标识")
    scene_model = models.ForeignKey(verbose_name="场景模型", to=SceneModelFile, blank=False, null=False,
                                    on_delete=models.CASCADE, help_text="场景模型文件")
    points = models.JSONField("控制点", default=default_points, blank=True,
                              help_text="场景模型控制点")

    class Meta:
        verbose_name = "03-场景模型"
        verbose_name_plural = "03-场景模型"
        ordering = ['scene_model', 'scene_id']

    def __str__(self):
        return f"{'、'.join([obj.name for obj in self.scene_model.category.all()])} ({self.scene_id})"


class TargetModel(models.Model):
    model_id = models.UUIDField(verbose_name="模型ID", default=uuid.uuid4, editable=False, unique=True,
                                help_text="目标模型的唯一标识")
    uploaded_at = models.DateTimeField(verbose_name="上传时间", default=timezone.now)
    category = models.ManyToManyField(verbose_name="模型类别", to=Category, blank=True, help_text="模型所属的类别")
    file = models.FileField(
        verbose_name="模型文件",
        upload_to=target_model_upload_path,
        help_text="请上传 *.fbx 格式的3D模型文件",
        validators=[FileExtensionValidator(allowed_extensions=['fbx'])]
    )

    class Meta:
        verbose_name = "04-目标模型"
        verbose_name_plural = "04-目标模型"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{'、'.join([obj.name for obj in self.category.all()])} ({self.model_id})"

    def save(self, *args, **kwargs):
        # 如果这是现有对象且文件字段被修改，则删除旧文件
        if self.pk:  # 检查是否为现有对象
            try:
                old_instance = TargetModel.objects.get(pk=self.pk)
                # 如果文件字段发生变化，删除旧文件
                if old_instance.file and old_instance.file != self.file:
                    if os.path.isfile(old_instance.file.path):
                        os.remove(old_instance.file.path)
            except TargetModel.DoesNotExist:
                pass  # 新对象，无需处理
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


@receiver(post_delete, sender=SceneModelFile)
def delete_scene_model_file(sender, instance, **kwargs):
    """
    场景模型删除后，同时删除其对应的物理文件
    """
    if instance.file:
        file_path = instance.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)


@receiver(post_delete, sender=TargetModel)
def delete_target_model_file(sender, instance, **kwargs):
    """
    目标模型删除后，同时删除其对应的物理文件
    """
    if instance.file:
        file_path = instance.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)
