# -*- coding: utf-8 -*-
# @Time : 2025/11/24 下午7:44
# @Author : CharlesWYQ
# @Email : 1578973516@qq.com
# @File : read_real_world_studio_dataset.py
# @Project : fiftyOne
# @Details : 导入数据集


import os
import sys
import json
import fiftyone as fo


def show_in_fiftyone(image_dir, dataset_name="dataset"):
    # 配置路径
    annotation_file = os.path.join(image_dir, "metadata.json")

    # 读取标注
    with open(annotation_file, 'r') as f:
        annotations = json.load(f)

    # 创建数据集
    if dataset_name in fo.list_datasets():
        fo.delete_dataset(dataset_name)
    dataset = fo.Dataset(dataset_name)

    samples = []
    for img_name, anns in annotations.items():
        img_path = os.path.join(image_dir, img_name)

        detections = []
        for ann in anns:
            x, y, w, h = ann["bbox"]
            rel_bbox = [x - w / 2, y - h / 2, w, h]

            label_tags = ann["target_class"]
            occlusion = ann["occlusion"]
            if occlusion <= 0.05:
                label_tags.append("未遮挡")
            elif occlusion <= 0.3:
                label_tags.append("轻度遮挡")
            elif occlusion <= 0.5:
                label_tags.append("中度遮挡")
            else:
                label_tags.append("重度遮挡")

            detection = fo.Detection(
                label=ann["target_class"][0],
                bounding_box=rel_bbox,
                confidence=1,
                occlusion=occlusion,
                tags=label_tags,
            )
            detections.append(detection)

        # 创建样本
        sample = fo.Sample(filepath=img_path)
        sample["RealEarthStudio标注"] = fo.Detections(detections=detections)
        sample["背景类别"] = anns[0]["scene_class"]
        sample["光照强度"] = anns[0]["sun_energy"]
        sample["光照角度"] = anns[0]["sun_azimuth_deg"]
        sample["光照仰角"] = anns[0]["sun_elevation_deg"]
        sample["拍摄距离"] = anns[0]["distance"]
        sample["拍摄角度"] = anns[0]["azimuth_deg"]
        elevation_deg = anns[0]["elevation_deg"]
        sample["拍摄仰角"] = elevation_deg
        sample["渲染器类型"] = anns[0]["renderer"]

        # 写入标签
        if elevation_deg > 80:
            sample.tags.append("顶视角")
        elif elevation_deg > 30:
            sample.tags.append("斜视角")
        else:
            sample.tags.append("大斜视角")

        samples.append(sample)

    # 批量添加
    dataset.add_samples(samples)
    dataset.compute_metadata()
    dataset.sort_by("拍摄角度", reverse=True)

    # session = fo.launch_app(dataset)
    # session.wait()


if __name__ == '__main__':
    DATASET_DIR = sys.argv[1]
    DATASET_NAME = sys.argv[2]
    show_in_fiftyone(DATASET_DIR, DATASET_NAME)
