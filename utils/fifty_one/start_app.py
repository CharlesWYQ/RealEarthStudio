# -*- coding: utf-8 -*-
# @Time : 2025/12/18 下午5:15
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : start_app.py
# @Project : fiftyOne
# @Details : 启动App

import fiftyone as fo
import time, os


def start_fiftyone_app():
    host = os.getenv("FIFTYONE_HOST", "0.0.0.0")
    port = int(os.getenv("FIFTYONE_PORT", "5151"))

    while True:
        try:
            session = fo.launch_app(
                dataset=None,
                auto=False,  # 不自动打开浏览器
                port=port,  # 指定端口
                address=host,  # 绑定到所有网络接口
                remote=True  # 允许远程访问
            )

            print(f"FiftyOne 应用程序已在 http://{host}:{port} 启动")
            print(f"可通过外部终端访问: http://<your_server_ip>:{port}")

            session.wait()
        except KeyboardInterrupt:
            print("\n应用程序已退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            time.sleep(1)


if __name__ == '__main__':
    start_fiftyone_app()
