# RealEarthStudio 

> 一个用于构建真实地球场景、合成3D数据并渲染高质量图像的开源工具集。

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=Django)
![Blender](https://img.shields.io/badge/Blender-5.0-red?logo=blender)
![CodeStyle](https://img.shields.io/badge/Code%20Style-Black-black)

---

## 📦 一、简介

**RealEarthStudio** 是一个面向地理空间仿真与合成数据生成的 Python 工具库。它支持：

- 🧱 **多模型合并**：将建筑、道路、车辆等 `.fbx` 模型组合成完整城市场景
- ☀️ **太阳光照控制**：通过方位角、高度角精确设置自然光照
- 🖼️ **高质量渲染**：按照固定仰角旋转渲染输出 RGB 图像 + 目标标注
- 🗺️ **地理对齐**：支持 WGS84 坐标系与局部坐标转换

适用于特定目标检测数据集生成等场景。

![LOGO](LOGO/RealEarthStudio_LOGO.png)

---

## ⚙️ 二、安装

### 2.1 依赖要求

- Python = 3.11
- Blender = 5.0

### 2.2 安装步骤

```bash
# 克隆项目
git clone https://gitee.com/charlsewyq/RealEarthStudio.git
cd RealEarthStudio

# 创建虚拟环境 (Anaconda)
conda create -n RealEarthStudio python=3.11
conda activate RealEarthStudio

# 安装依赖
pip install -r requirements.txt
```