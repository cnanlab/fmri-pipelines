import nilearn.image
import constants

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
                print(f"zfstat path {zfstat_path} does not exist")
                
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
            print(f"affine file {affine_file} does not exist")
            
    return affine_files

def roi_extract_node_func(input_nifti: str, roi_num: int, mask_file_path: str) -> list:
    roi_values = roi_extract(input_nifti, roi_num, mask_file_path)
    
    return roi_values, input_nifti

def roi_extract(input_nifti: str, roi_num: int, mask_file_path: str) -> list:
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
    
    return roi_values

def average_roi_values_node_func(roi_values: list, zfstat_path: str):
    avg = average_roi_values(roi_values)
        
    return {
        "avg": avg,
        "zfstat_path": zfstat_path
    }

def average_roi_values(roi_values: list) -> float:
    """
    Averages the ROI values.
    """
    import numpy as np
    
    return np.mean(roi_values)

def join_and_format(**kwargs):  
    """
    Joins the results and formats them.
    """
    print(kwargs)
    import logging
    
    logger = logging.getLogger('nipype.workflow') 
    return "placeholder"

def dummy_fnirt(in_file: str, affine_file: str) -> str:
    """
    Dummy implementation of FNIRT.
    """
    return in_file

def custom_fnirt(in_file: str, affine_file: str) -> str:
    """
    Custom implementation of FNIRT.
    """
    import os
    import fsl
    
    # Create the output file name
    out_file = os.path.join(os.path.dirname(in_file), f"warped_{os.path.basename(in_file)}")
    
    # Run the FNIRT
    fnirt = fsl.FNIRT(ref_file=in_file, in_file=in_file, affine_file=affine_file, output_type='NIFTI_GZ', warp_resolution=10)
    fnirt.run()
    
    return out_file