# -*- coding: utf-8 -*-
# @Time : 2025/12/18 下午5:15
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : start_app.py
# @Project : fiftyOne
# @Details : 启动App

import fiftyone as fo
import time


def start_fiftyone_app():
    while True:
        try:
            session = fo.launch_app(dataset=None, auto=False, port=5151)
            session.wait()
        except KeyboardInterrupt:
            print("\n应用程序已退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            time.sleep(1)


if __name__ == '__main__':
    start_fiftyone_app()
