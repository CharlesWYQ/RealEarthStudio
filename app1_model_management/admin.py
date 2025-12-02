# D:/Projects/RealEarthStudio/RealEarthStudio/app1_model_management/admin.py

from django.contrib import admin
from .models import TargetModel, SceneModel  # 明确导入模型以避免 * 导入问题
from django.utils.safestring import mark_safe


admin.site.site_header = '🌏 REAL EARTH STUDIO'
admin.site.site_title = 'RealEarthStudio'
admin.site.index_title = '数据维护管理系统'


class BaseModelAdmin(admin.ModelAdmin):
    # 共有字段展示
    list_display = ['model_id', 'category', 'uploaded_at', 'file_link']
    list_display_links = ['model_id']
    list_filter = ['category', 'uploaded_at']
    search_fields = ['category', 'model_id']
    readonly_fields = ['model_id', 'uploaded_at', 'file_preview']

    fieldsets = (
        ('基本信息', {
            'fields': ('model_id', 'uploaded_at', 'category')
        }),
        ('文件信息', {
            'fields': ('file', 'file_preview')
        }),
    )

    @admin.display(description="文件")
    def file_link(self, obj):
        if obj.file:
            return mark_safe(f'<a href="{obj.file.url}" target="_blank">下载模型</a>')
        return "无文件"

    @admin.display(description="文件详情")
    def file_preview(self, obj):
        if obj.file:
            size_mb = obj.file.size / (1024 * 1024)
            return mark_safe(f"文件名: {obj.file.name.split('/')[-1]}<br>大小: {size_mb:.2f} MB")
        return "无文件"

    class Meta:
        abstract = True  # 标记为抽象类，防止被注册成实际管理界面


@admin.register(TargetModel)
class TargetModelAdmin(BaseModelAdmin):
    pass


@admin.register(SceneModel)
class SceneModelAdmin(BaseModelAdmin):
    pass
