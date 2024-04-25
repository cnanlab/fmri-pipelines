import nilearn.image
import constants

def get_latest_feat_dir(feat_datasink: str) -> str:
    """
    Returns the latest FEAT directory from the FEAT datasink. Finds
    the latest directory (where directory name is a datetime string) and returns it.
    """
    import os
    
    feat_dirs = os.listdir(feat_datasink)
    
    # ignore any directory with "feat"
    dirs = [dir for dir in feat_dirs if "feat" not in dir]
    
    pass   

def get_all_zfstat_paths_from_feat_datasink(feat_datasink: str, verbose: bool = False) -> list:
    """
    Returns all the zfstat paths from the feat datasink (directory with all FEAT runs).
    """
    import os
    
    zfstat_paths = []
    
    for feat_dir_name in os.listdir(feat_datasink):
        # skip linear FEAT runs (LN)
        if "LN" in feat_dir_name:                        
            continue
        
        for contrast_id in range(1, 7):
            zfstat_path = os.path.join(feat_datasink, feat_dir_name, "stats", f"zfstat{contrast_id}.nii.gz")
            if os.path.exists(zfstat_path):
                zfstat_paths.append(zfstat_path)                
                    
            else:
                if verbose:
                    print(f"WARN: zfstat path {zfstat_path} does not exist")
                pass
                
    return zfstat_paths

def get_all_affine_files_from_feat_datasink(feat_datasink: str) -> list:
    """
    Returns all the affine files from the feat datasink (directory with all FEAT runs).
    """
    import os
    
    affine_files = []
    
    for feat_dir_name in os.listdir(feat_datasink):
        affine_file = os.path.join(feat_datasink, feat_dir_name, "reg", "example_func2standard.mat")
        if os.path.exists(affine_file):
            affine_files.append(affine_file)
        else:
            # print(f"affine file {affine_file} does not exist")
            pass
            
    return affine_files


def roi_extract_all_node_func(input_nifti: str, mask_file_path: str, is_test_run=False):
    """
    Extracts all the ROIs from the input nifti file.
    """
    from nilearn.image import load_img
    import numpy as np
    import logging            
    
    # Load the nifti file
    data = load_img(input_nifti).get_fdata()
    
    # Load the mask file
    mask_data = load_img(mask_file_path).get_fdata()
    
    # roi_nums = np.unique(mask_data) <- ideal but slower
    roi_nums = range(1, 12) # 11 ROIs, numbered 1-11 
    
    roi_dicts = []
    
    for roi_num in roi_nums:
        # Get indices of the ROI
        roi_indices = np.argwhere(mask_data == roi_num)    
        
        # remove indices if they are out of bounds
        roi_indices = [index for index in roi_indices if all([i < data.shape[i] for i in range(3)])]        
        print(f"Found {len(roi_indices)} voxels in {input_nifti} for ROI number {roi_num}")                                

        roi_values = None

        if is_test_run:        
            # # temp 
            roi_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            print(f"TEST_MODE: Using dummy roi values: {roi_values} for ROI number {roi_num}")            
        else:
            # Get the values of the ROI at the indices
            roi_values = [data[tuple(index)] for index in roi_indices]                                
        
        roi_dict = {
            "roi_values": roi_values,
            "zfstat_path": input_nifti,
            "roi_num": roi_num,
        }
        
        # print(f"ROI {roi_num} dict: {roi_dict}")
        
        roi_dicts.append(roi_dict)
        
    return roi_dicts
                        
def average_each_roi_values_node_func(roi_dicts: list):
    """
    Averages the ROI values.
    """
    import numpy as np
    
    avg_dicts = []
    
    for dict in roi_dicts:
        roi_values = dict["roi_values"]
        zfstat_path = dict["zfstat_path"]
        roi_num = dict["roi_num"]
        
        avg = np.mean(roi_values)
        
        avg_dicts.append({
            "avg": avg,
            "zfstat_path": zfstat_path,
            "roi_num": roi_num                        
        })
        
    return avg_dicts

def roi_extract_node_func(input_nifti: str, roi_num: int, mask_file_path: str, is_test_run=False):
    """
    Extracts the ROI from the input nifti file.
    """
    from nilearn.image import load_img
    import numpy as np
    import logging
            
    # Load the nifti file
    data = load_img(input_nifti).get_fdata()
    
    # Load the mask file
    mask_data = load_img(mask_file_path).get_fdata()
    
    # Get indices of the ROI
    roi_indices = np.argwhere(mask_data == roi_num)    
    
    # remove indices if they are out of bounds
    roi_indices = [index for index in roi_indices if all([i < data.shape[i] for i in range(3)])]        
    print(f"Found {len(roi_indices)} voxels in {input_nifti} for ROI number {roi_num}")        
    
    # Get the values of the ROI at the indices
    roi_values = [data[tuple(index)] for index in roi_indices]                
    
    return roi_values, input_nifti, roi_num

def average_roi_values_node_func(roi_values: list, zfstat_path: str, roi_num: int):
    """
    Averages the ROI values.
    """
    import numpy as np
    
    avg = np.mean(roi_values)
        
    return {
        "avg": avg,
        "zfstat_path": zfstat_path,
        "roi_num": roi_num
    }
    

def join(dict: dict):  
    """
    First join function.
    """    
    # import logging
    
    # logger = logging.getLogger('nipype.workflow') 
    
    # print(kwargs)    
    # for key, value in kwargs.items():
    #     logger.info(f"{key}: {value}")
    
    return dict

def add_metadata_node_func(avg_dicts: list, subject_id: str, run: int, image_name: str):
    """
    Adds metadata to the average ROI activations.
    """
    joined_dicts = []
    
    for dict in avg_dicts:        
        dict["subject_id"] = subject_id
        dict["run"] = run
        dict["image_name"] = image_name
        
        joined_dicts.append(dict)
        
    return joined_dicts    

def join_main(joined_dicts: list):  
    """
    Joins and flattens the dictionaries (each dict has "avg" and "zfstat_path" and "roi_num" keys)
    """    
    
    flattened = []
    
    for array in joined_dicts:
        for dict in array:
            flattened.append(dict)                
    
    return flattened

def make_csv_node_func(flattened: list):
    """ Make a CSV file for the average ROI activations.
    
    Format of CSV:
        roi, subid, image, run, activation
        
    Example Row:
        1, NDARINV00CY2MDM, corGo, 1, 0.38347


    Args:
        flattened (list): list of { "avg": float, "zfstat_path": str, "roi_num": int, "subject_id": str, "run": int, "image_name": str }
    """
    import regex as re
    import pandas as pd
    import os
        
    # omit zfstat path
    for dict in flattened:
        del dict["zfstat_path"]
        
    # create dataframe
    df = pd.DataFrame(flattened)
        
    # save dataframe to csv
    save_path = os.path.join(os.getcwd(), "roi_activations.csv")
    df.to_csv(save_path, index=False)
    
    return save_path           
        

def dummy_fnirt(in_file: str, affine_file: str, mni_template: str, subject_id: str, run:int, image_name: str) -> str:
    """
    Dummy implementation of FNIRT.
    """    
    import os
    
    in_file_name = os.path.basename(in_file)
    
    out_warped_name = f"sub-{subject_id}_run-{run}_{image_name}_NL_{in_file_name}"
    
    print(f"Dummy FNIRT: {in_file} -> {out_warped_name}")
    
    return in_file

def custom_fnirt(in_file: str, affine_file: str, mni_template: str, subject_id: str, run: int, image_name:str) -> str:
    """
    Custom implementation of FNIRT.
    """
    import os    
    from nipype.interfaces.fsl import FNIRT 
    import time   
    import shutil       
    
    # Ex: zfstat1.nii.gz
    in_file_name = os.path.basename(in_file)    
    
    # Add "_NL" to the filename
    # Ex: zfstat1_NL.nii.gz
    out_warped_name = in_file_name.replace(".nii.gz", "_NL.nii.gz")
    
    out_feat_path = os.path.join(os.path.dirname(in_file), out_warped_name)
    
    if os.path.exists(out_feat_path):
        print(f"FNIRT_NODE: {in_file} -> {out_warped_name} already exists. Skipping.")
        return out_feat_path
    
    start_time = time.time()
    
    # Run FNIRT
    fnirt = FNIRT(ref_file=mni_template, in_file=in_file, affine_file=affine_file, output_type='NIFTI_GZ', warped_file=out_warped_name)
    fnirt.run()
    
    end_time = time.time()
    
    print(f"FNIRT_NODE: {in_file} -> {out_warped_name} took {end_time - start_time} seconds, {(end_time - start_time) / 60} minutes.")
    
    out_fnirt_path = os.path.join(os.getcwd(), out_warped_name)
    
    # copy the fnirt file to the location where the input file is (FEAT directory)
    shutil.copy(out_fnirt_path, out_feat_path)
    
    print(f"FNIRT_NODE: Copied {out_fnirt_path} to {out_feat_path}")
    
    return out_feat_path
    

def get_subject_id_from_zfstat_path(zfstat_path: str) -> str:
    """
    Returns the subject ID from the zfstat path.
    """
    import regex as re
    
    subid_match = re.search(r"sub-([^_/]+)", zfstat_path)
    subid = subid_match.group(1)
    
    return subid

def get_run_from_zfstat_path(zfstat_path: str) -> int:
    """
    Returns the run number from the zfstat path.
    """
    import regex as re
    
    run_match = re.search(r"run-(\d+)", zfstat_path)
    run = int(run_match.group(1))
    
    return run

def get_image_name_from_zfstat_path(zfstat_path: str) -> str:
    """
    Returns the image name from the zfstat path.
    """
    import regex as re
    
    zfstat_num_match = re.search(r"zfstat(\d+).nii.gz", zfstat_path)
    zfstat_num = int(zfstat_num_match.group(1))
    
    zfstat_num_to_image_name = {
        1: "corGo",
        2: "incGo",
        3: "corStop",
        4: "incStop",
        5: "corStopvcorGo",
        6: "incStopvcorGo"
    }
    
    return zfstat_num_to_image_name[zfstat_num]