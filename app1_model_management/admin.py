from django.contrib import admin
from .models import *
from django.utils.safestring import mark_safe

admin.site.site_header = '🌏 REAL EARTH STUDIO'
admin.site.site_title = 'RealEarthStudio'
admin.site.index_title = '数据维护管理系统'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['model_type', 'name', 'parent', 'level', 'is_leaf_status', 'model_count']
    search_fields = ['name']
    ordering = ['model_type', 'level', 'name']
    list_display_links = ['name']
    readonly_fields = ['id', 'level']

    fieldsets = (
        ('标签类别', {
            'fields': ['id', 'model_type']
        }),
        ('标签信息', {
            'fields': ['name', 'parent']
        }),
    )

    def get_list_filter(self, request):
        # 动态设置list_filter
        parent_categories = Category.objects.filter(level__lte=1)

        class ParentCategoryFilter(admin.SimpleListFilter):
            title = '分类'
            parameter_name = 'parent'

            def lookups(self, _request, model_admin):
                return [(cat.id, str(cat)) for cat in parent_categories]

            def queryset(self, _request, queryset):
                if self.value():
                    return queryset.filter(parent_id=self.value()).distinct()
                return queryset

        return ['model_type', ParentCategoryFilter, 'level']

    @admin.display(description="叶子节点", boolean=True)
    def is_leaf_status(self, obj):
        return obj.is_leaf

    @admin.display(description="模型数量")
    def model_count(self, obj):
        # 计算关联到此分类的目标模型和场景模型数量
        target_count = TargetModel.objects.filter(category=obj).count()
        scene_count = SceneModelFile.objects.filter(category=obj).count()
        return target_count + scene_count


@admin.register(SceneModel)
class SceneModelAdmin(admin.ModelAdmin):
    list_display = ['scene_id', 'get_categories', 'points_display']
    search_fields = ['scene_id', 'scene_model__file']
    readonly_fields = ['scene_id']

    fieldsets = (
        ('基本信息', {
            'fields': ('scene_id', 'scene_model')
        }),
        ('控制点信息', {
            'fields': ('points',)
        }),
    )

    def get_list_filter(self, request):
        # 动态设置list_filter，使用缓存避免重复查询
        class ParentCategoryFilter(admin.SimpleListFilter):
            title = '分类'
            parameter_name = 'category'

            def lookups(self, _request, model_admin):
                return [(cat.id, str(cat)) for cat in
                        Category.objects.filter(model_type__in=['general', 'scene'], level=1)]

            def queryset(self, _request, queryset):
                if self.value():
                    return queryset.filter(scene_model__category=self.value()).distinct()
                return queryset

        return [ParentCategoryFilter]

    @admin.display(description="分类")
    def get_categories(self, obj):
        """获取关联分类"""
        categories = [cat.name for cat in obj.scene_model.category.all()]
        return ", ".join(categories) if categories else "-"

    @admin.display(description="控制点信息")
    def points_display(self, obj):
        """格式化显示控制点"""
        if obj.points:
            return mark_safe(f"起点: {obj.points[0]}<br>方向: {obj.points[1]}")
        return "-"


class BaseCategoryAdmin(admin.ModelAdmin):
    # 共有字段展示
    list_display = ['model_id', 'get_categories', 'uploaded_at', 'file_link']
    list_display_links = ['model_id']
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

    category_model_types = []

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # 限制Category只能选择叶子节点
        if db_field.name == "category" and self.category_model_types:
            # 只显示叶子节点（没有子分类的分类）
            kwargs["queryset"] = Category.objects.filter(
                model_type__in=self.category_model_types,
                children__isnull=True
            ).order_by("level", "parent", )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_list_filter(self, request):
        # 动态设置list_filter，使用缓存避免重复查询
        parent_categories = Category.objects.filter(
            model_type__in=self.category_model_types,
            level=1
        )

        class ParentCategoryFilter(admin.SimpleListFilter):
            title = '分类'
            parameter_name = 'category'

            def lookups(self, _request, model_admin):
                return [(cat.id, str(cat)) for cat in parent_categories]

            def queryset(self, _request, queryset):
                if self.value():
                    return queryset.filter(category__parent_id=self.value()).distinct()
                return queryset

        return [ParentCategoryFilter, 'uploaded_at']

    @admin.display(description="类别")
    def get_categories(self, obj):
        categories = []
        for category in obj.category.all():
            if not category.is_leaf:
                # 标记非叶子节点
                categories.append(f'<span style="color: orange;">{str(category)}</span>')
            else:
                categories.append(str(category))
        return mark_safe(r"<br>".join(categories))

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


@admin.register(SceneModelFile)
class SceneModelFileAdmin(BaseCategoryAdmin):
    list_display = ['model_id', 'get_categories', 'uploaded_at', 'point_count', 'file_link']
    category_model_types = ['general', 'scene']

    @admin.display(description="渲染点数量")
    def point_count(self, obj):
        # 计算关联到此分类的目标模型和场景模型数量
        return SceneModel.objects.filter(scene_model_id=obj.id).count()


@admin.register(TargetModel)
class TargetModelAdmin(BaseCategoryAdmin):
    category_model_types = ['general', 'target']
