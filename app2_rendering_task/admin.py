from django.contrib import admin
from .models import *
from django.utils.safestring import mark_safe
from django.urls import reverse


@admin.register(RenderingTask)
class RenderingTaskAdmin(admin.ModelAdmin):
    list_display = ['render_id', 'render_time', 'renderer_type', 'image_width', 'image_height',
                    'render_progress_display']
    search_fields = ['render_id']
    list_filter = ['renderer_type', 'render_time']
    readonly_fields = ['render_id', 'render_time', 'render_progress', 'rendered_result_dir']

    # 字段分组显示
    fieldsets = (
        ('任务信息', {
            'fields': ('render_id', 'render_time', 'renderer_type', 'render_progress')
        }),
        ('模型配置', {
            'fields': ('target_models', 'scene_models')
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
        url_show = "#"
        if obj.render_progress == 0:
            return mark_safe(f'<a href="{url_render}">开始渲染</a>')
        elif obj.render_progress == 1:
            return mark_safe(f'<a href="{url_show}" target="_blank">查看结果</a> | <a href="{url_render}">重新渲染</a>')
        else:
            return f"{obj.render_progress * 100:.2f}%"
