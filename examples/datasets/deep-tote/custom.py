import blenderproc as bproc
import math
import bpy
import argparse
import os
import os.path as osp
import shutil
import cv2
import numpy as np
import json
from typing import List
from loguru import logger
from functools import partial
from omegaconf import OmegaConf

def load_object(object_cfg):
    object = bproc.loader.load_obj(object_cfg.FILE)[0]
    unit = object_cfg.UNIT
    if unit == 'auto':
        bound_box = object.get_bound_box(local_coords=True)
        diag_length = np.linalg.norm(np.max(bound_box, axis=0) - np.min(bound_box, axis=0))
        if diag_length < 2:
            unit = 'm'
        else:
            unit = 'mm'
        logger.info('Object diagonal length: {:.4f} {}', diag_length, unit)

    if unit == 'm':
        pass
    elif unit == 'mm':
        object.set_scale([0.001, 0.001, 0.001])
        logger.info('Scale the object by 0.001: mm to m')

    if object_cfg.DECIMATION > 0:
        num_polygons = len(object.get_mesh().polygons.values())
        logger.info('Number of polygons of the object: {}', num_polygons)
        if object_cfg.DECIMATION < num_polygons:
            object.edit_mode()
            ratio = object_cfg.DECIMATION / num_polygons
            bpy.ops.mesh.decimate(ratio=ratio)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            object.object_mode()
            num_polygons = len(object.get_mesh().polygons.values())
            logger.info('Decimate object to {} polygons', num_polygons)

    if object_cfg.MOVE_TO_MASS_CENTER:
        object.set_origin(mode='CENTER_OF_MASS')
        object.set_location([0,0,0])
        logger.info('Move the object to the center of mass')

    if object_cfg.SHADING_MODE in ['auto', 'flat', 'smooth']:
        object.set_shading_mode(object_cfg.SHADING_MODE)
        logger.info('Set shading mode: {}', object_cfg.SHADING_MODE)
    return object

def compute_tote_size(object: bproc.types.MeshObject, tote_cfg):
    object_bbox = object.get_bound_box()
    object_size = np.max(object_bbox, axis=0) - np.min(object_bbox, axis=0)
    object_length = float(np.linalg.norm(object_size))
    if tote_cfg.WIDTH == 'auto':
        tote_cfg.WIDTH = 4 * object_length
    if tote_cfg.LENGTH == 'auto':
        tote_cfg.LENGTH = 4 * object_length
    if tote_cfg.HEIGHT == 'auto':
        tote_cfg.HEIGHT = 4 * object_length
    tote_xy_size = np.array([tote_cfg.WIDTH, tote_cfg.LENGTH])
    if np.linalg.norm(tote_xy_size) < 2 * object_length:
        tote_xy_size *= 2 * object_length / np.linalg.norm(tote_xy_size)
        tote_cfg.WIDTH = float(tote_xy_size[0])
        tote_cfg.LENGTH = float(tote_xy_size[1])
        logger.warning('The given tote size is too small, has been enlarged to 2 x object length')
    logger.info('Tote size: width = {:.3f}m, length = {:.3f}m, height = {:.3f}m', tote_cfg.WIDTH, tote_cfg.LENGTH, tote_cfg.HEIGHT)

def create_tote_planes(tote_cfg):
    width = tote_cfg.WIDTH
    length = tote_cfg.LENGTH
    height = tote_cfg.HEIGHT
    tote_planes = [
        bproc.object.create_primitive('PLANE', scale=[width*2, length*2, 1]),
        bproc.object.create_primitive('PLANE', scale=[width/2, height/2, 1], location=[0, -length/2, height/2], rotation=[-math.pi/2, 0, 0]),
        bproc.object.create_primitive('PLANE', scale=[width/2, height/2, 1], location=[0, length/2, height/2], rotation=[math.pi/2, 0, 0]),
        bproc.object.create_primitive('PLANE', scale=[height/2, length/2, 1], location=[-width/2, 0, height/2], rotation=[0, math.pi/2, 0]),
        bproc.object.create_primitive('PLANE', scale=[height/2, length/2, 1], location=[width/2, 0, height/2], rotation=[0, -math.pi/2, 0]),
        ]
    for i, tote_plane in enumerate(tote_planes):
        if i == 0:
            tote_plane.enable_rigidbody(False, collision_shape='BOX', mass=1.0, friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)
        else:
            tote_plane.enable_rigidbody(False, collision_shape='BOX', mass=1.0, friction = 0.0, linear_damping = 0.99, angular_damping = 0.99)
            if not tote_cfg.WALL_VISIBLE:
                tote_plane.hide()
    funnel_angle = math.pi/4
    funnel_plane_coords = [
        [0, -length/2, height],
        [0,  length/2, height],
        [-width/2,  0, height],
        [ width/2,  0, height],
    ]
    funnel_plane_rotation = [
        [-funnel_angle, 0, 0],
        [ funnel_angle, 0, 0],
        [0, funnel_angle, 0],
        [0, -funnel_angle, 0],
    ]
    funnel_planes = [
        bproc.object.create_primitive('PLANE', scale=[10, 10, 1], location=coord, rotation=rotation)
        for coord, rotation in zip(funnel_plane_coords, funnel_plane_rotation)
    ]
    for i, funnel_plane in enumerate(funnel_planes):
        funnel_plane.edit_mode()
        bpy.ops.mesh.bisect(plane_co=funnel_plane_coords[i], plane_no=[0,0,1], clear_inner=True)
        funnel_plane.object_mode()
        funnel_plane.enable_rigidbody(False, collision_shape='BOX', mass=1.0, friction = 0.0, linear_damping = 1.0, angular_damping = 1.0)
        funnel_plane.hide()
    return tote_planes, funnel_planes

def sample_objects(base_obj: bproc.types.MeshObject, 
                   objects_to_check_collisions: List[bproc.types.MeshObject],
                   sampler_cfg,
                   tote_cfg) -> List[bproc.types.MeshObject]:
    def sample_pose(obj: bproc.types.MeshObject, cube_min, cube_max):
        obj.set_location(np.random.uniform(cube_min, cube_max))
        obj.set_rotation_euler(bproc.sampler.uniformSO3())
    if sampler_cfg.MIN_HEIGHT < tote_cfg.HEIGHT:
        sampler_cfg.MIN_HEIGHT = tote_cfg.HEIGHT
        logger.warning("Object sampler's min height is smaller than tote height")
    if sampler_cfg.MAX_HEIGHT < sampler_cfg.MIN_HEIGHT + 0.1:
        sampler_cfg.MAX_HEIGHT = sampler_cfg.MIN_HEIGHT + 0.1
    objects = []
    num_objects = np.random.randint(sampler_cfg.MIN_NUM, sampler_cfg.MAX_NUM + 1)
    friction = np.random.choice([0.0, 100.0])
    for _ in range(num_objects):
        obj = base_obj.duplicate()
        obj.hide(False)
        obj.enable_rigidbody(True, mass=1.0, friction = friction, linear_damping = 0.99, angular_damping = 0.99, collision_margin=0.0005)
        objects.append(obj)
    padding = sampler_cfg.MIN_HEIGHT - tote_cfg.HEIGHT
    cube_min = [-tote_cfg.WIDTH - padding, -tote_cfg.LENGTH - padding, sampler_cfg.MIN_HEIGHT]
    cube_max = [tote_cfg.WIDTH + padding, tote_cfg.LENGTH  + padding, sampler_cfg.MAX_HEIGHT]
    sample_pose_partial = partial(sample_pose, cube_min=cube_min, cube_max=cube_max)
    bproc.object.sample_poses(objects, sample_pose_partial, objects_to_check_collisions)
    if sampler_cfg.PHYSICS.ENABLE:
        bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=sampler_cfg.PHYSICS.MIN_SIMULATION_TIME,
                                                          max_simulation_time=sampler_cfg.PHYSICS.MAX_SIMULATION_TIME,
                                                          substeps_per_frame=sampler_cfg.PHYSICS.SUBSTEPS_PER_FRAME,
                                                          solver_iters=sampler_cfg.PHYSICS.SOLVER_ITERS,
                                                          check_object_interval=1)
    return objects

def sample_lights(light_cfg) -> List[bproc.types.Light]:
    lights = []
    num_lights = np.random.randint(light_cfg.MIN_NUM, light_cfg.MAX_NUM + 1)
    for _ in range(num_lights):
        light = bproc.types.Light(light_type="POINT")
        light.set_energy(np.random.uniform(light_cfg.MIN_ENERGY, light_cfg.MAX_ENERGY))
        location = bproc.sampler.shell(center=[0,0,0],
                                       radius_min=light_cfg.MIN_HEIGHT,
                                       radius_max=light_cfg.MAX_HEIGHT,
                                       elevation_min=light_cfg.MIN_ELEVATION,
                                       elevation_max=light_cfg.MAX_ELEVATION)
        light.set_color(np.random.uniform([0.5, 0.5, 0.5], [1.0, 1.0, 1.0]))
        light.set_location(location)
        lights.append(light)
    return lights

def set_camera_intrinsics(camera_cfg):
    random_percent = 0.01 * camera_cfg.RANDOM_PERCENT
    min_ratio = 1 - random_percent
    max_ratio = 1 + random_percent
    fx = np.random.uniform(camera_cfg.FX * min_ratio, camera_cfg.FX * max_ratio)
    fy = np.random.uniform(camera_cfg.FY * min_ratio, camera_cfg.FY * max_ratio)
    ppx = np.random.uniform(camera_cfg.PPX * min_ratio, camera_cfg.PPX * max_ratio)
    ppy = np.random.uniform(camera_cfg.PPY * min_ratio, camera_cfg.PPY * max_ratio)
    width = camera_cfg.WIDTH
    height = camera_cfg.HEIGHT
    bproc.camera.set_intrinsics_from_K_matrix([[fx, 0, ppx], [0, fy, ppy], [0, 0, 1]], width, height, 0.05, 10)
    return [[fx, 0, ppx], [0, fy, ppy], [0, 0, 1]]
    
def sample_camera(objects, sampler_cfg):
    location = bproc.sampler.shell(center=[0, 0, 0],
                                    radius_min=sampler_cfg.MIN_HEIGHT,
                                    radius_max=sampler_cfg.MAX_HEIGHT,
                                    elevation_min=sampler_cfg.MIN_ELEVATION,
                                    elevation_max=sampler_cfg.MAX_ELEVATION)
    poi = bproc.object.compute_poi(np.random.choice(objects, size=min(10, len(objects)), replace=False))
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-3.14159, 3.14159))
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix, frame=0)
    return cam2world_matrix

def sample_objects_material(objects, sampler_cfg):
    for obj in objects:        
        mat = obj.get_materials()[0]
        grey = np.random.uniform(sampler_cfg.MIN_GRAY, sampler_cfg.MAX_GRAY)
        mat.set_principled_shader_value("Base Color", [grey, grey, grey, 1])      
        mat.set_principled_shader_value("Roughness", np.random.uniform(sampler_cfg.MIN_ROUGHNESS, sampler_cfg.MAX_ROUGHNESS))
        mat.set_principled_shader_value("Specular", np.random.uniform(sampler_cfg.MIN_SPECULAR, sampler_cfg.MAX_SPECULAR))
        mat.set_principled_shader_value("Metallic", np.random.uniform(sampler_cfg.MIN_METALLIC, sampler_cfg.MAX_METALLIC))

def delete_objects(objects):
    for obj in objects:
        bpy.data.meshes.remove(obj.blender_obj.data)
        obj.delete()

def delete_lights(lights):
    for light in lights:
        bpy.data.lights.remove(light.blender_obj.data)
        light.delete()

def camera_pose_blender2common(pose):
    flip_yz = np.array([[1, 0, 0, 0],
                        [0,-1, 0 ,0],
                        [0, 0,-1, 0],
                        [0 ,0, 0, 1]], dtype=float)
    return np.dot(pose, flip_yz)

def write_data(data, cam_K, cam2world_mat, cfg, scene_dir, camera_id):
    if 'colors' in data:
        color = data['colors'][0]
        color_dir = osp.join(scene_dir, 'color')
        os.makedirs(color_dir, exist_ok=True)
        color_path = f'{color_dir}/{camera_id:06}.png'
        cv2.imwrite(color_path, color)
        image_height, image_width = color.shape[:2]
    if 'depth' in data:
        depth = data['depth'][0]
        depth = (depth / cfg.DEPTH_SCALE).astype(np.uint16)
        depth_dir = osp.join(scene_dir, 'depth')
        os.makedirs(depth_dir, exist_ok=True)
        depth_path = f'{depth_dir}/{camera_id:06}.png'
        cv2.imwrite(depth_path, depth)
    cam_infos_path = osp.join(scene_dir, 'scene_cameras.json')
    if osp.exists(cam_infos_path):
        with open(cam_infos_path, 'r') as f:
            cam_infos = json.load(f)
    else:
        cam_infos = dict()
    cam2world_mat = camera_pose_blender2common(cam2world_mat)
    cam_infos[f'{camera_id:06}'] = {
            "fx": cam_K[0][0],
            "fy": cam_K[1][1],
            "ppx": cam_K[0][2],
            "ppy": cam_K[1][2],
            "width": image_width,
            "height": image_height,
            "hom_mat": cam2world_mat[:3].flatten().tolist(),
            "depth_scale": cfg.DEPTH_SCALE,
            }
    with open(cam_infos_path, 'w') as f:
        json.dump(cam_infos, f, indent=2)

def write_object_poses(objects, scene_dir):
    poses = [obj.get_local2world_mat() for obj in objects]
    data = { f'{i:06}':{"hom_mat": pose[:3].flatten().tolist()} for i, pose in enumerate(poses) }
    with open(osp.join(scene_dir, 'scene_objects.json'), 'w') as f:
        json.dump(data, f, indent=2)

def export_mesh(filepath: str):
    ext = os.path.splitext(filepath)[-1]
    if ext not in ['.ply', '.stl']:
        raise Exception('export_mesh only support ply and stl format')
    if ext == '.ply':
        bpy.ops.export_mesh.ply(filepath=filepath)
    elif ext == '.stl':
        bpy.ops.export_mesh.stl(filepath=filepath)
    print('Export CAD Model: {}'.format(filepath))


parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default='path/to/config.yaml' ,help='path to the config.yaml file')
args = parser.parse_args()
if not osp.exists(args.config):
    logger.warning('given config file not found, use default configuration.')
    args.config = osp.join(osp.dirname(__file__), 'config.yaml')
cfg = OmegaConf.load(args.config)

shutil.rmtree(cfg.OUTPUT_DIR, ignore_errors=True)
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

bproc.init()
bproc.renderer.set_max_amount_of_samples(50)
if cfg.ENABLE_DEPTH:
    bproc.renderer.enable_depth_output(activate_antialiasing=False)

materials = None
base_obj = load_object(cfg.OBJECT)

# export mm & m unit model
export_mesh(osp.join(cfg.OUTPUT_DIR, 'model_m.ply'))
scale = base_obj.get_scale()
base_obj.set_scale(scale * 1000)
export_mesh(osp.join(cfg.OUTPUT_DIR, 'model_mm.ply'))
base_obj.set_scale(scale)

# reload m unit model
delete_objects([base_obj])
cfg.OBJECT.FILE = osp.join(cfg.OUTPUT_DIR, 'model_m.ply')
base_obj = load_object(cfg.OBJECT)
base_obj.hide()

compute_tote_size(base_obj, cfg.TOTE)
tote_planes, funnel_planes = create_tote_planes(cfg.TOTE)
for scene_id in range(cfg.NUM_SCENES):
    logger.info('Scene {}:', scene_id)
    scene_dir = osp.join(cfg.OUTPUT_DIR, f'{scene_id:06}')
    os.makedirs(scene_dir, exist_ok=True)
    objects = sample_objects(base_obj, tote_planes + funnel_planes, cfg.OBJECT.POSE_SAMPLER, cfg.TOTE)
    write_object_poses(objects, scene_dir)
    for camera_id in range(cfg.NUM_CAMERAS_PER_SCENE):
        logger.info('Scene {} / Cemera {}', scene_id, camera_id)
        cam_K = set_camera_intrinsics(cfg.CAMERA.INTRINSICS)
        lights = sample_lights(cfg.LIGHT)
        if cfg.TOTE.RANDOM_TEXTURE and osp.exists(cfg.CC_TEXTURES_DIR):
            if materials is None:
                materials = bproc.loader.load_ccmaterials(cfg.CC_TEXTURES_DIR)
            mat = np.random.choice(materials)
            for plane in tote_planes:
                plane.replace_materials(mat)
        cam2world_mat = sample_camera(objects, cfg.CAMERA.POSE_SAMPLER)
        sample_objects_material(objects, cfg.OBJECT.MATERIAL_SAMPLER)

        data = bproc.renderer.render()
        write_data(data, cam_K, cam2world_mat, cfg, scene_dir, camera_id)

        delete_lights(lights)

    delete_objects(objects)
    
