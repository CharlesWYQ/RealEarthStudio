"""
URL configuration for RealEarthStudio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # 根路径重定向到admin
    path('', RedirectView.as_view(url='/admin/', permanent=False)),

    # 管理员
    path("admin/", admin.site.urls),

    # app1: 目标及场景模型管理模块
    path("api/app1/", include("app1_model_management.urls")),

    # app2: 数据集渲染任务管理模块
    path("api/app2/", include("app2_rendering_task.urls")),
]

# 只在DEBUG模式下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
