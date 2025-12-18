import os
from rest_framework.views import APIView
from .tasks import execute_render_task
from utils.status import response as my_response
from .models import RenderingTask


class StartRender(APIView):
    @staticmethod
    def get(request, render_id):
        # 开始渲染
        execute_render_task.delay(render_id)
        return my_response.success(data=render_id, message="正在渲染")


class ShowDataset(APIView):
    @staticmethod
    def get(request, render_id):
        # 开始渲染
        return my_response.success(data=render_id, message="正在渲染")
