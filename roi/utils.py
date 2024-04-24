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

def get_all_zfstat_paths_from_feat_datasink(feat_datasink: str) -> list:
    """
    Returns all the zfstat paths from the feat datasink (directory with all FEAT runs).
    """
    import os
    
    zfstat_paths = []
    
    for feat_dir_name in os.listdir(feat_datasink):
        for contrast_id in range(1, 7):
            zfstat_path = os.path.join(feat_datasink, feat_dir_name, "stats", f"zfstat{contrast_id}.nii.gz")
            if os.path.exists(zfstat_path):
                zfstat_paths.append(zfstat_path)
            else:
                # print(f"zfstat path {zfstat_path} does not exist")
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


def roi_extract_all_node_func(input_nifti: str, mask_file_path: str, subject_id: str, run: int, image_name: str):
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
        
        # Get the values of the ROI at the indices
        roi_values = [data[tuple(index)] for index in roi_indices]        
        
        # temp
        # roi_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        # print(f"WARN: Using dummy roi values: {roi_values}")
        
        roi_dicts.append({
            "roi_values": roi_values,
            "zfstat_path": input_nifti,
            "roi_num": roi_num,
            "subject_id": subject_id,
            "run": run,
            "image_name": image_name
        })
        
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
            "subject_id": dict["subject_id"],
            "run": dict["run"],
            "image_name": dict["image_name"]
            
        })
        
    return avg_dicts

def roi_extract_node_func(input_nifti: str, roi_num: int, mask_file_path: str):
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
    
    # # temp 
    # roi_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # print(f"WARN: Using dummy roi values: {roi_values}")
    
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
        
    # create dataframe
    df = pd.DataFrame(flattened)
        
    # save dataframe to csv
    save_path = os.path.join(os.getcwd(), "roi_activations.csv")
    df.to_csv(save_path, index=False)
    
    return save_path           
        

def dummy_fnirt(in_file: str, affine_file: str, mni_template: str) -> str:
    """
    Dummy implementation of FNIRT.
    """
    import os
    
    zfstat_path = in_file
    
    new_name = f"warped_{os.path.basename(in_file)}"
    
    new_path = os.path.join(os.path.dirname(in_file), new_name)
    
    return new_path

def custom_fnirt(in_file: str, affine_file: str, mni_template: str) -> str:
    """
    Custom implementation of FNIRT.
    """
    import os    
    from nipype.interfaces import fsl        
        
    # Run FNIRT
    fnirt = fsl.FNIRT(ref_file=mni_template, in_file=in_file, affine_file=affine_file, output_type='NIFTI_GZ', warped_file=out_path)
    fnirt.run()
    
    return out_path

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