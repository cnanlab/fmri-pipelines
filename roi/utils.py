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
    # roi_values = [data[tuple(index)] for index in roi_indices]        
    
    # temp 
    roi_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"WARN: Using dummy roi values: {roi_values}")
    
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
    Joins and flattens the dictionaries (each dict has "avg" and "zfstat_path" keys)
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
        flattened (list): list of { "avg": float, "zfstat_path": str, "roi_num": int }
    """
    import regex as re
    import pandas as pd
    import os
    
    # init dataframe with columns
    rows = []
    
    for dict in flattened:
        zfstat_path = dict["zfstat_path"]
        roi_num = dict["roi_num"]
        avg = dict["avg"]
        
        zfstat_num_to_image_name = {
            1: "corGo",
            2: "incGo",
            3: "corStop",
            4: "incStop",
            5: "corStopvcorGo",
            6: "incStopvcorGo"
        }
        
        # use regex to extract subid, image, run from zfstat_path
        subid_match = re.search(r"sub-(\w+)_", zfstat_path)
        zfstat_num_match = re.search(r"zfstat(\d+).nii.gz", zfstat_path)
        run_match = re.search(r"run-(\d+)", zfstat_path)
        
        subid = subid_match.group(1)
        zfstat_num = int(zfstat_num_match.group(1))
        image = zfstat_num_to_image_name[zfstat_num]
        run = int(run_match.group(1))
        
        # add to rows
        rows.append({
            "roi": roi_num,
            "subid": subid,
            "image": image,
            "run": run,
            "activation": avg
        })
        
    # create dataframe
    df = pd.DataFrame(rows)
        
    # save dataframe to csv
    save_path = os.path.join(os.getcwd(), "roi_activations.csv")
    df.to_csv(save_path, index=False)
    
    return save_path           
        
    

def dummy_fnirt(in_file: str, affine_file: str) -> str:
    """
    Dummy implementation of FNIRT.
    """
    return in_file

# def custom_fnirt(in_file: str, affine_file: str) -> str:
#     """
#     Custom implementation of FNIRT.
#     """
#     import os
#     import fsl
    
#     # Create the output file name
#     out_file = os.path.join(os.path.dirname(in_file), f"warped_{os.path.basename(in_file)}")
    
#     # Run the FNIRT
#     fnirt = fsl.FNIRT(ref_file=in_file, in_file=in_file, affine_file=affine_file, output_type='NIFTI_GZ', warp_resolution=10)
#     fnirt.run()
    
#     return out_file