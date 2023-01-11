import os
import os.path as osp
import json
import shutil
import imageio
import numpy as np
import cv2
from glob import glob
import argparse
from rich.progress import Progress
from omegaconf import OmegaConf
from bop_toolkit_lib import renderer, misc, visibility, inout

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def init_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)
    os.makedirs(directory, exist_ok=True)

def normalize(array):
    min_val = array.min()
    max_val = array.max()
    return (array - min_val) / (max_val - min_val)

parser = argparse.ArgumentParser()
parser.add_argument('config', type=str, help='path to the config.yaml file')
args = parser.parse_args()
cfg = OmegaConf.load(args.config)

output_dir = cfg.OUTPUT_DIR
model_file = osp.join(output_dir, 'model_mm.ply')
scene_dirs = sorted(glob(osp.join(output_dir, '*')))
scene_dirs = [x for x in scene_dirs if osp.isdir(x)]

image_width = cfg.CAMERA.INTRINSICS.WIDTH
image_height = cfg.CAMERA.INTRINSICS.HEIGHT
ren = renderer.create_renderer(image_width, image_height, renderer_type='vispy', mode='depth')
ren.add_object(0, model_file)
with Progress() as progress:
    scene_tqdm = progress.add_task('scene', total=len(scene_dirs))
    for scene_dir in scene_dirs:
        color_dir = osp.join(scene_dir, 'color')
        depth_dir = osp.join(scene_dir, 'depth')
        mask_dir = osp.join(scene_dir, 'mask')
        mask_visib_dir = osp.join(scene_dir, 'mask_visib')
        init_directory(mask_dir)
        init_directory(mask_visib_dir)
        cameras = load_json(osp.join(scene_dir, 'scene_cameras.json'))
        objects_info = load_json(osp.join(scene_dir, 'scene_objects.json'))
        camera_tqdm = progress.add_task('camera', total=len(cameras))
        for camera_id, camera_info in cameras.items():
            fx = camera_info['fx']
            fy = camera_info['fy']
            ppx = camera_info['ppx']
            ppy = camera_info['ppy']
            K = np.array([[fx, 0, ppx], [0, fy, ppy], [0,0,1]], dtype=float)
            depth_im = imageio.imread(osp.join(depth_dir, f'{camera_id}.png')).astype(float)
            depth_im *= (1 / cfg.DEPTH_SCALE)
            dist_im = misc.depth_im_to_dist_im_fast(depth_im, K)
            tf_world_cam = np.array(camera_info['hom_mat'] + [0,0,0,1.0]).astype(float).reshape(4,4)
            object_tqdm = progress.add_task('object', total=len(objects_info))
            for object_id, object_info in objects_info.items():
                tf_world_obj = np.array(object_info['hom_mat'] + [0,0,0,1.0]).astype(float).reshape(4,4)
                tf_cam_obj = np.dot(np.linalg.inv(tf_world_cam), tf_world_obj)
                depth_gt = ren.render_object(0, tf_cam_obj[:3, :3], tf_cam_obj[:3, 3], fx, fy, ppx, ppy)['depth']
                dist_gt = misc.depth_im_to_dist_im_fast(depth_gt, K)
                mask = dist_gt > 0
                mask_visib = visibility.estimate_visib_mask_gt(dist_im, dist_gt, 0.002, visib_mode='bop19')
                inout.save_im(osp.join(mask_dir, f'{camera_id}_{object_id}.png'), mask.astype(np.uint8) * 255)
                inout.save_im(osp.join(mask_visib_dir, f'{camera_id}_{object_id}.png'), mask_visib.astype(np.uint8) * 255)
                progress.advance(object_tqdm)
            progress.remove_task(object_tqdm)
            progress.advance(camera_tqdm)
        progress.advance(scene_tqdm)
        progress.remove_task(camera_tqdm)
    