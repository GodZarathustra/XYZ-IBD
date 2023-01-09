import blenderproc as bproc
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('model')
args = parser.parse_args()


bproc.init()

light_point = bproc.types.Light()
light_point.set_energy(10)
light_point.set_location([0,0,2])

cc_mats = bproc.loader.load_ccmaterials('/home/shq/Datasets/cc_textures')

cached_objects = dict()
objects = bproc.loader.load_obj(args.model, cached_objects)
objects[0].set_scale([0.005, 0.005, 0.005])
for _ in range(9):
    objects.append(objects[0].duplicate())
for obj in objects:
    obj.enable_rigidbody(True, mass=1.0, friction = 100.0, linear_damping = 0.99, angular_damping = 0.99, collision_margin=0.0005)

room_planes = [bproc.object.create_primitive('PLANE', scale=[1, 1, 1]),
               bproc.object.create_primitive('PLANE', scale=[1, 1, 1], location=[0, -1, 1], rotation=[-1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[1, 1, 1], location=[0, 1, 1], rotation=[1.570796, 0, 0]),
               bproc.object.create_primitive('PLANE', scale=[1, 1, 1], location=[1, 0, 1], rotation=[0, -1.570796, 0]),
               bproc.object.create_primitive('PLANE', scale=[1, 1, 1], location=[-1, 0, 1], rotation=[0, 1.570796, 0])]
for plane in room_planes:
    plane.enable_rigidbody(False, collision_shape='BOX', mass=1.0, friction = 100.0, linear_damping = 0.99, angular_damping = 0.99)
    plane.replace_materials(np.random.choice(cc_mats))


# Define a function that samples the pose of a given sphere
def sample_pose(obj: bproc.types.MeshObject):
    obj.set_location(np.random.uniform([-1, -1, 1], [1, 1, 5]))
    obj.set_rotation_euler(bproc.sampler.uniformSO3())

# Sample the poses of all spheres above the ground without any collisions in-between
bproc.object.sample_poses(
    objects,
    sample_pose_func=sample_pose
)

bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=3,
                                                  max_simulation_time=10,
                                                  check_object_interval=1,
                                                  substeps_per_frame = 50,
                                                  solver_iters=25)

bproc.camera.set_intrinsics_from_K_matrix([[1000, 0, 512], [0, 1000, 512], [0, 0, 1]], 1024, 1024, 0.1, 100)
mat = bproc.math.build_transformation_mat([0,0,1], [0,0,0])
bproc.camera.add_camera_pose(mat)
mat = bproc.math.build_transformation_mat([0,0,2], [0,0,0])
bproc.camera.add_camera_pose(mat)

data = bproc.renderer.render()
bproc.writer.write_hdf5('/home/shq/Projects/mycode/BlenderProc/output/custom', data)
