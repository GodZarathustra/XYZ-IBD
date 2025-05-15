# BlenderProc2

[![Documentation](https://img.shields.io/badge/documentation-passing-brightgreen.svg)](https://dlr-rm.github.io/BlenderProc/)
[![Open In Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DLR-RM/BlenderProc/blob/main/examples/basics/basic/basic_example.ipynb)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<p align="center">
<img src="https://user-images.githubusercontent.com/6104887/137109535-275a2aa3-f5fd-4173-9d16-a9a9b86f66e7.gif" alt="Front readme image" width=100%>
</p>

A procedural Blender pipeline for photorealistic rendering.

[Documentation](https://dlr-rm.github.io/BlenderProc) | [Tutorials](#tutorials) | [Examples](#examples) | [ArXiv paper](https://arxiv.org/abs/1911.01911) | [Workshop paper](https://sim2real.github.io/assets/papers/2020/denninger.pdf)

## Docker Usage
### Build Docker
 ```python
cd docker 
docker build -t "render_xyz_synthetic" .
```
### Run Docker
```python
docker run --gpus all render_xyz_synthetic
cd "examples\datasets\deep-tote"
### Modify the OUTPUT_DIR and OBJECT FILE in config.yaml to your custom path before run scripts!

### Generate the whole synthetic dataset for all objects
blenderproc run render.py --config=config.yaml
### Generate the synthetic dataset for specific object
blenderproc run custom.py --config=config_photoneo_qiuxiao1.yaml
### Post Process the synthetic dataset to BOP Format
blenderproc run gen_masks.py --config=config_photoneo_qiuxiao1.yaml
