from django.contrib import admin
from .models import *
from django.utils.safestring import mark_safe
from django.urls import reverse

from django_celery_results.apps import CeleryResultConfig
from django_celery_results.models import GroupResult, TaskResult
from django_celery_results.admin import GroupResultAdmin, TaskResultAdmin


@admin.register(RenderingTask)
class RenderingTaskAdmin(admin.ModelAdmin):
    list_display = ['render_id', 'render_type', 'render_time', 'renderer_type', 'image_width', 'image_height',
                    'render_progress_display']
    search_fields = ['render_id']
    list_filter = ['renderer_type', 'render_time']
    readonly_fields = ['render_id', 'render_time', 'render_progress', 'rendered_result_dir']

    # 字段分组显示
    fieldsets = (
        ('任务信息', {
            'fields': ('render_id', 'render_time', 'render_type', 'renderer_type', 'render_progress')
        }),
        ('模型配置', {
            'fields': ('scene_models', 'target_models')
        }),
        ('光照参数', {
            'fields': ('sun_azimuth', 'sun_elevation')
        }),
        ('相机参数', {
            'fields': ('camera_distances', 'camera_elevations', 'camera_rotation_step')
        }),
        ('图像设置', {
            'fields': ('image_width', 'image_height')
        }),
        ('渲染结果', {
            'fields': ('rendered_result_dir',)
        })
    )

    @admin.display(description="渲染状态")
    def render_progress_display(self, obj):
        url_render = reverse('app2_rendering_task:start_render_view', args=[obj.render_id])
        url_show = reverse('app2_rendering_task:show_dataset_view', args=[obj.render_id])
        if obj.render_progress == 0:
            return mark_safe(f'<a href="{url_render}">开始渲染</a>')
        elif obj.render_progress == 1:
            return mark_safe(f'<a href="{url_show}" target="_blank">查看结果</a> | <a href="{url_render}">重新渲染</a>')
        elif obj.render_progress == 0.9:
            return mark_safe(f'{obj.render_progress * 100:.2f}% | <a href="{url_render}">重新渲染</a>')
        else:
            return mark_safe(f'{obj.render_progress * 100:.2f}% | <a href="{url_render}">重新渲染</a>')


class CustomGroupResultAdmin(GroupResultAdmin):
    date_hierarchy = None  # 禁用日期层级导航


class CustomTaskResultAdmin(TaskResultAdmin):
    date_hierarchy = None  # 禁用日期层级导航


# 重新注册
try:
    admin.site.unregister(GroupResult)
    admin.site.unregister(TaskResult)
except:
    pass

admin.site.register(GroupResult, CustomGroupResultAdmin)
admin.site.register(TaskResult, CustomTaskResultAdmin)

GroupResult._meta.verbose_name = "组结果"
GroupResult._meta.verbose_name_plural = "组结果"

TaskResult._meta.verbose_name = "任务结果"
TaskResult._meta.verbose_name_plural = "任务结果"

CeleryResultConfig.verbose_name = "🏷️ Celery 任务执行结果管理"
