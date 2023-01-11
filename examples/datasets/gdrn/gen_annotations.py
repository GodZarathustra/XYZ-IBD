import os
import os.path as osp
import json
import shutil
import imageio.v2 as imageio
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

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, help='path to the config.yaml file')
args = parser.parse_args()
if args.config is None:
    args.config = osp.join(osp.dirname(__file__), 'config.yaml')
cfg = OmegaConf.load(args.config)

output_dir = cfg.OUTPUT_DIR
model_file = osp.join(output_dir, 'model_mm.ply')
scene_dirs = sorted(glob(osp.join(output_dir, '*')))
scene_dirs = [x for x in scene_dirs if osp.isdir(x)]

image_width = cfg.CAMERA.INTRINSICS.WIDTH
image_height = cfg.CAMERA.INTRINSICS.HEIGHT
image_width_large = image_width * 3
image_height_large = image_height * 3
image_offset_x = image_width
image_offset_y = image_height

ren = renderer.create_renderer(image_width_large, image_height_large, renderer_type='vispy', mode='depth')
ren.add_object(0, model_file)
with Progress() as progress:
    scene_tqdm = progress.add_task('scene', total=len(scene_dirs))
    for scene_dir in scene_dirs:
        color_dir = osp.join(scene_dir, 'color')
        depth_dir = osp.join(scene_dir, 'depth')
        mask_dir = osp.join(scene_dir, 'mask')
        mask_visib_dir = osp.join(scene_dir, 'mask_visib')
        cameras = load_json(osp.join(scene_dir, 'scene_cameras.json'))
        objects_info = load_json(osp.join(scene_dir, 'scene_objects.json'))
        annotations = dict()
        camera_tqdm = progress.add_task('camera', total=len(cameras))
        for camera_id, camera_info in cameras.items():
            annotations[camera_id] = []
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
                depth_gt_large = ren.render_object(0, tf_cam_obj[:3, :3], tf_cam_obj[:3, 3], fx, fy, ppx + image_offset_x, ppy + image_offset_y)['depth']
                depth_gt = depth_gt_large[image_offset_y:image_offset_y+image_height,
                                        image_offset_x:image_offset_x+image_width]
                dist_gt = misc.depth_im_to_dist_im_fast(depth_gt, K)
                visib_gt = visibility.estimate_visib_mask_gt(dist_im, dist_gt, 0.005, visib_mode='bop19')
                
                obj_mask_gt_large = depth_gt_large > 0
                obj_mask_gt = dist_gt > 0
        
                px_count_all = int(np.sum(obj_mask_gt_large))
                px_count_valid = int(np.sum(dist_gt[obj_mask_gt] > 0))
                px_count_visib = int(visib_gt.sum())
                
                if px_count_all > 0:
                    visib_fract = px_count_visib / float(px_count_all)
                else:
                    visib_fract = 0.0
                
                # Bounding box of the whole object silhouette
                # (including the truncated part).
                bbox = [-1, -1, -1, -1]
                if px_count_visib > 0:
                    ys, xs = obj_mask_gt_large.nonzero()
                    ys -= image_offset_y
                    xs -= image_offset_x
                    bbox = misc.calc_2d_bbox(xs, ys, (image_width, image_height))

                # Bounding box of the visible surface part.
                bbox_visib = [-1, -1, -1, -1]
                if px_count_visib > 0:
                    ys, xs = visib_gt.nonzero()
                    bbox_visib = misc.calc_2d_bbox(xs, ys, (image_width, image_height))
                
                anno = dict(
                    px_count_all=px_count_all,
                    px_count_valid=px_count_valid,
                    px_count_visib=px_count_visib,
                    visib_frac=visib_fract,
                    bbox_obj=[int(e) for e in bbox],
                    bbox_visib=[int(e) for e in bbox_visib],
                )
                annotations[camera_id].append(anno)
                progress.advance(object_tqdm)
            progress.remove_task(object_tqdm)
            progress.advance(camera_tqdm)
        progress.remove_task(camera_tqdm)
        progress.advance(scene_tqdm)
        with open(osp.join(scene_dir, 'annotations.json'), 'w') as f:
            json.dump(annotations, f, indent=2)
        
