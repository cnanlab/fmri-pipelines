def get_all_zfstat_paths_from_feat_dir(feat_dir: str) -> list:
    """
    Returns all the zfstat paths from the feat directory.
    """
    import os
    zfstat_paths = []
    for root, dirs, files in os.walk(feat_dir):
        for file in files:
            if file.endswith("zfstat1.nii.gz"):
                zfstat_paths.append(os.path.join(root, file))
    return zfstat_paths

def roi_extract(input_nifti: str, roi_num: int) -> list:
    """
    Extracts the ROI from the input nifti file.
    """
    import nilearn
    import numpy as np
    # Load the nifti file
    data = nilearn.image.load_img(input_nifti).get_data()
    
    # Get indices of the ROI
    roi_indices = np.argwhere(data == roi_num)
    
    print(f"Found {len(roi_indices)} voxels in the ROI")
    
    # Get the values of the ROI at the indices
    roi_values = [data[tuple(index)] for index in roi_indices]        
    
    return roi_values

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