# -*- coding: utf-8 -*-
# @Time : 2025/12/18 下午9:28
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : execute_external_python_script.py
# @Project : RealEarthStudio
# @Details : 运行外部python脚本

import subprocess


def main(external_python_path, script_path, *args):
    cmd = [
        external_python_path,
        script_path,
        *args
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(f"外部程序执行失败: {result.stderr}")
    print("导入FiftyOne完成")
