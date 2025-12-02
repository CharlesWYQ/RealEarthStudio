from django.apps import AppConfig


class App1ModelManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app1_model_management"

    verbose_name = "🏷️ 应用1：目标及场景模型管理模块"
