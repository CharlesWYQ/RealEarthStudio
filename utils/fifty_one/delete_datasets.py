# -*- coding: utf-8 -*-
# @Time : 2025/12/18 下午5:18
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : delete_datasets.py
# @Project : fiftyOne
# @Details : 删除数据集

import fiftyone as fo
import sys


def main(dataset_name=None):
    if dataset_name:
        fo.delete_dataset(dataset_name, verbose=True)
        return None

    # 获取所有数据集名称
    dataset_names = fo.list_datasets()

    print("即将删除以下数据集:")
    for name in dataset_names:
        print(f" - {name}")

    # 确认删除（可选）
    confirm = input("确定删除所有数据集吗? (y/N): ")
    if confirm.lower() == 'y':
        for name in dataset_names:
            fo.delete_dataset(name, verbose=True)
        print("✅ 所有数据集已删除！")
    else:
        print("❌ 取消删除。")


if __name__ == '__main__':
    DATASET_NAME = sys.argv[2]
    main(DATASET_NAME)
    # main()
