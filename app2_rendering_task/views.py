from rest_framework.views import APIView
from .tasks import execute_render_task
from django.shortcuts import redirect
from time import sleep


class StartRender(APIView):
    @staticmethod
    def get(request, render_id):
        # 开始渲染
        execute_render_task.delay(render_id)
        # return my_response.success(data=render_id, message="正在渲染")
        sleep(1)
        return redirect("http://localhost:8000/admin/app2_rendering_task/renderingtask/")


class ShowDataset(APIView):
    @staticmethod
    def get(request, render_id):
        # 查看数据集
        redirect_url = f"http://localhost:5151/datasets/{render_id}"
        # return my_response.success(data={"redirect_url": redirect_url}, message="正在渲染")
        return redirect(redirect_url)
