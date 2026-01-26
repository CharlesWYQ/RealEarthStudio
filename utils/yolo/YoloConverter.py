# -*- coding: utf-8 -*-
# @Time : 2026/1/26 15:50
# @Author : CharlesWYQ
# @Email : charleswyq@foxmail.com
# @File : YoloConverter.py
# @Project : yolo
# @Details : 


import json
import os
from pathlib import Path
import shutil
from typing import Dict, List


class YoloConverter:
    def __init__(self):
        """初始化转换器"""
        self.class_mapping = {}
        self.dataset_dir = None
        self.target_class_index = 1

    def create_classes_file(self, data: dict, dataset_dir: Path):
        """创建classes.txt文件"""
        classes_set = set()
        for image_data in data.values():
            for obj in image_data:
                if obj['target_class']:
                    classes_set.add(obj['target_class'][self.target_class_index])

        classes_list = sorted(list(classes_set))
        self.class_mapping = {cls: idx for idx, cls in enumerate(classes_list)}

        with open(dataset_dir / 'classes.txt', 'w', encoding='utf-8') as f:
            for cls in classes_list:
                f.write(f"{cls}\n")

        print(f"类别映射: {self.class_mapping}")
        print(f"类别文件保存至: {dataset_dir / 'classes.txt'}")

    def get_class_index(self, class_name: str) -> int:
        """
        获取类别索引
        """
        if class_name not in self.class_mapping:
            raise ValueError(f"类别 '{class_name}' 不在类别映射中。可用类别: {list(self.class_mapping.keys())}")
        return self.class_mapping[class_name]

    def process_split(self, data: dict, image_list: List[str], source_dir: Path, dataset_dir: Path, split_name: str):
        """处理特定分割的数据集"""
        for image_filename in image_list:
            # 复制图像文件
            src_image_path = source_dir / image_filename
            dst_image_path = dataset_dir / "images" / split_name / image_filename

            if src_image_path.exists():
                shutil.copy2(src_image_path, dst_image_path)

            # 生成对应的标注文件
            annotations = data[image_filename]
            yolo_annotations = []

            for annotation in annotations:
                main_class = annotation['target_class'][self.target_class_index]
                # 使用实例的类别映射
                class_idx = self.get_class_index(main_class)

                bbox = annotation['bbox']
                yolo_line = f"{class_idx} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}"
                yolo_annotations.append(yolo_line)

            # 创建标注文件
            txt_filename = image_filename.replace('.png', '.txt')
            txt_path = dataset_dir / "labels" / split_name / txt_filename

            with open(txt_path, 'w', encoding='utf-8') as f:
                for line in yolo_annotations:
                    f.write(line + '\n')

    def create_yolo_structure(self, dataset_dir: Path):
        """创建标准YOLO数据集目录结构"""
        directories = [
            dataset_dir / "images" / "train",
            dataset_dir / "images" / "val",
            dataset_dir / "images" / "test",
            dataset_dir / "labels" / "train",
            dataset_dir / "labels" / "val",
            dataset_dir / "labels" / "test"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        print(f"创建目录结构于: {dataset_dir}")
        self.dataset_dir = dataset_dir

    @staticmethod
    def split_data(image_filenames: List[str], split_ratio: Dict[str, float]) -> Dict[str, List[str]]:
        """按比例划分数据集"""
        from sklearn.model_selection import train_test_split
        import random

        # 确保随机种子一致
        random.seed(42)
        shuffled_images = image_filenames.copy()
        random.shuffle(shuffled_images)

        total_count = len(shuffled_images)
        train_end = int(total_count * split_ratio['train'])
        val_end = int(total_count * (split_ratio['train'] + split_ratio['val']))

        splits = {
            'train': shuffled_images[:train_end],
            'val': shuffled_images[train_end:val_end],
            'test': shuffled_images[val_end:]
        }

        print(f"数据集划分: 训练集{len(splits['train'])}, 验证集{len(splits['val'])}, 测试集{len(splits['test'])}")
        return splits

    def organize_yolo_dataset(self, json_path: str, split_ratio: Dict[str, float] = None):
        """
        将自定义JSON格式转换为标准YOLO格式并组织目录结构

        Args:
            json_path: JSON元数据文件路径
            split_ratio: 数据集划分比例，默认为 {'train': 0.8, 'val': 0.1, 'test': 0.1}
        """
        if split_ratio is None:
            split_ratio = {'train': 0.8, 'val': 0.1, 'test': 0.1}

        # 读取JSON文件
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 获取JSON文件所在目录作为根目录
        base_dir = Path(json_path).parent
        dataset_dir = base_dir / "yolo_dataset"

        # 创建目录结构
        self.create_yolo_structure(dataset_dir)

        # 获取所有图像文件名列表
        all_images = list(data.keys())

        # 划分数据集
        splits = self.split_data(all_images, split_ratio)

        # 创建classes.txt文件
        self.create_classes_file(data, dataset_dir)

        # 处理每个分割的数据集
        for split_name, image_list in splits.items():
            self.process_split(data, image_list, base_dir, dataset_dir, split_name)

    @staticmethod
    def create_data_yaml(dataset_dir: Path):
        """创建YOLO训练所需的data.yaml文件"""
        import yaml

        # 读取类别数量
        classes_file = dataset_dir / 'classes.txt'
        with open(classes_file, 'r', encoding='utf-8') as f:
            num_classes = len(f.readlines())

        # 重新读取类别列表
        with open(classes_file, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f.readlines()]

        data_config = {
            'path': str(dataset_dir.absolute()),  # 数据集根目录
            'train': 'images/train',  # 训练图像目录
            'val': 'images/val',  # 验证图像目录
            'test': 'images/test',  # 测试图像目录
            'nc': num_classes,  # 类别数量
            'names': names  # 类别名称列表
        }

        yaml_path = dataset_dir / 'data.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_config, f, default_flow_style=False, allow_unicode=True)

        print(f"data.yaml 已创建: {yaml_path}")

    def convert_with_directory_structure(self, json_path: str):
        """
        主函数：转换数据集并创建标准目录结构
        """
        print("开始转换为标准YOLO数据集格式...")

        # 默认8:1:1划分
        split_ratio = {'train': 0.8, 'val': 0.1, 'test': 0.1}

        self.organize_yolo_dataset(json_path, split_ratio)

        # 创建data.yaml配置文件
        self.create_data_yaml(Path(json_path).parent / "yolo_dataset")

        print("转换完成！标准YOLO数据集结构已创建。")


if __name__ == "__main__":
    # 修改JSON路径为实际路径
    JSON_PATH = r"Datasets/1a374db5-64e9-4dbd-aec0-23ba3ce8e1ac/Dataset/metadata.json"

    converter = YoloConverter()
    if os.path.exists(JSON_PATH):
        converter.convert_with_directory_structure(JSON_PATH)
    else:
        print(f"错误: 找不到文件 {JSON_PATH}")
