import subprocess
import os
import os.path as osp
from typing import List
from omegaconf import OmegaConf
from pathlib import Path
import shutil
import json

def validate_output(base_path: str, expected_count: int = 25) -> bool:
    """
    Validate that:
    1. 'color' and 'depth' folders have exactly expected_count files
    2. 'mask_visib' folder has (expected_count * number of objects) files
    3. All required directories and JSON file exist
    
    Args:
        base_path (str): Base path containing required folders and scene_objects.json
        expected_count (int): Expected number of images per object (default: 25)
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    # Convert base path to Path object and create paths
    base_dir = Path(base_path)
    color_dir = base_dir / 'color'
    depth_dir = base_dir / 'depth'
    mask_dir = base_dir / 'mask_visib'
    scene_objects_json = base_dir / 'scene_objects.json'
    scene_cameras_json = base_dir / 'scene_cameras.json'
    scene_gt_json = base_dir / 'scene_gt.json'
    scene_camera_json = base_dir / 'scene_camera.json'
    
    # Check if all required paths exist
    if not all([color_dir.exists(), depth_dir.exists(), 
                mask_dir.exists(), scene_objects_json.exists(), 
                scene_cameras_json.exists(), scene_gt_json.exists(),
                scene_camera_json.exists(),]):
        return False
    
    # Get list of files
    color_images = {f.name for f in color_dir.iterdir() if f.is_file()}
    depth_images = {f.name for f in depth_dir.iterdir() if f.is_file()}
    mask_images = {f.name for f in mask_dir.iterdir() if f.is_file()}
    
    # Load scene objects
    try:
        with open(scene_objects_json) as f:
            scene_objects = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False
    
    # Validate counts
    if len(color_images) != expected_count:
        return False
    if len(depth_images) != expected_count:
        return False
    if len(mask_images) != len(scene_objects) * expected_count:
        return False
    
    return True

def run_blenderproc_with_configs(config_files: List[str], base_command: str = "blenderproc run custom.py") -> None:
    """
    Run BlenderProc with multiple configuration files sequentially.
    
    Args:
        config_files: List of paths to YAML configuration files
        base_command: The base BlenderProc command to run (default: "blenderproc run custom.py")
    """
    number_of_scene = 10 # the total number of scene of each object you want to generate
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"Warning: Config file {config_file} not found. Skipping...")
            continue
            
        command = f"{base_command} --config={config_file}"
        print(f"\nExecuting: {command}")

        cfg = OmegaConf.load(config_file)
        # shutil.rmtree(cfg.OUTPUT_DIR, ignore_errors=True)
        os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
        
        # Count existing valid folders
        valid_count = 0
        for idx in range(number_of_scene):
            cur_folder = osp.join(cfg.OUTPUT_DIR, f'{idx:06d}')
            if os.path.exists(cur_folder) and validate_output(cur_folder):
                valid_count += 1
                
        print(f"Found {valid_count} valid folders, resuming from index {valid_count}")
        i = valid_count
        
        while i < number_of_scene:
            # Check if previous run was valid before proceeding
            cur_folder = osp.join(cfg.OUTPUT_DIR, f'{i:06d}')
            if os.path.exists(cur_folder):
                if validate_output(cur_folder):
                    print(f"Valid data already exists for index {i}")
                    i += 1
                    continue
                else:
                    print(f"Invalid data found for index {i}, cleaning up...")
                    shutil.rmtree(cur_folder, ignore_errors=True)
                
            try:
                subprocess.run(command, shell=True)
                        
            except Exception as e:
                print(f"Unexpected error occurred with config {config_file}: {str(e)}")
                shutil.rmtree(cur_folder, ignore_errors=True)
                

if __name__ == "__main__":
    config_files = [
        "config_photoneo_qiuxiao1.yaml",
        "config_photoneo_neixinlun2.yaml", 
        "config_photoneo_zhouchengquan3.yaml",
        "config_photoneo_hudiejian4.yaml",
        "config_photoneo_daoliuzhao5.yaml",
        "config_photoneo_banjinjian6.yaml",
        "config_photoneo_liangan7.yaml",
        "config_photoneo_diaohuan8.yaml",
        "config_photoneo_yuanguan9.yaml",
        "config_photoneo_lianjiejian10.yaml",
        "config_photoneo_hudiebanjin11.yaml",
        "config_photoneo_changbanjin12.yaml",
        "config_photoneo_zhijiaobanjin13.yaml",
        "config_photoneo_jingjiagongjian14.yaml",
        "config_photoneo_jiaojieyuanguan15.yaml",
        "config_photoneo_ganqiuxiao16.yaml",
        "config_photoneo_fanguangzhao17.yaml",
        "config_photoneo_lungufalan18.yaml",
    ]
    
    # Run the automation
    run_blenderproc_with_configs(config_files)