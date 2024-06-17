##############
# Helpers
##############
def registration_node_func(nonlinear: bool, in_file: str, affine_file: str, mni_template: str, force_run: bool = False, no_affine: bool = False):
    """
    Registration node function.
    
    nonlinear (bool): Whether to use FNIRT or FLIRT
    in_file (str): Input file path
    affine_file (str): Affine file path (transformation matrix)
    mni_template (str): MNI template file path
    force_run (bool): Whether to force run the node (ignore if the output file already exists)
    no_affine (bool): Whether to use affine file or not (FNIRT only)
    """
    import os
    import time
    import shutil
     
     # Ex: zfstat1.nii.gz
    in_file_name = os.path.basename(in_file)    
    
    tag = "NL" if nonlinear else "LN"
    
    node_name = "FNIRT" if nonlinear else "FLIRT"
    
    out_name = f"{in_file_name.replace('.nii.gz', f'_{tag}.nii.gz')}"
    
    out_feat_path = os.path.join(os.path.dirname(in_file), out_name)
    
    print(f"{node_name}_NODE: {in_file} -> {out_feat_path}")
    
    # check if the output file already exists
    if os.path.exists(out_feat_path) and not force_run:
            print(f"{node_name}_NODE: {in_file} -> {out_name} already exists. Skipping.")
            return out_feat_path, nonlinear
    
    def get_interface():
        if nonlinear:
            from nipype.interfaces.fsl import FNIRT
            # Run FNIRT    

            if no_affine:
                return FNIRT(ref_file=mni_template, in_file=in_file, output_type='NIFTI_GZ', warped_file=out_name, config_file="T1_2_MNI152_2mm")
            else:
                return FNIRT(ref_file=mni_template, in_file=in_file, affine_file=affine_file, output_type='NIFTI_GZ', warped_file=out_name, config_file="T1_2_MNI152_2mm")    
        else:
            from nipype.interfaces.fsl import FLIRT

            if not "brain" in mni_template:
                raise ValueError("MNI template must be a brain template for FLIRT.")                

            return FLIRT(in_file=in_file, out_file=out_name, reference=mni_template, apply_xfm=True, in_matrix_file=affine_file, save_log=True, out_log="flirt-log.txt", padding_size=0, interp="trilinear", output_type='NIFTI_GZ')
    
    interface = get_interface()
    
    start_time = time.time()
    
    result = interface.run()    
    
    stdout = result.runtime.stdout
    
    print(f"{node_name}_NODE: {in_file} -> {out_feat_path} stdout: {stdout}")
    
    end_time = time.time()                
    
    print(f"{node_name}_NODE: {in_file} -> {out_feat_path} took {end_time - start_time} seconds, {(end_time - start_time) / 60} minutes.")
    
    out_path = os.path.join(os.getcwd(), out_name)
    
    # copy the fnirt file to the location where the input file is (FEAT directory)
    dest = shutil.copy(out_path, out_feat_path)
    
    print(f"{node_name}_NODE: Copied {out_path} to {dest}")
    
    return out_feat_path, nonlinear            
      
def get_all_paths(base_feat_path: str, linear_feat=True, verbose=False):
    """
    Get all filtered_func paths, affine files, and ev files from the FEAT directory.
    
    base_feat_path (str): Base FEAT directory path
    
    Returns:
    
    filtered_func_paths (list): List of filtered_func paths
    affine_files (list): List of affine files
    ev_files (list): List of lists [ev1, ev2, ...] for each filtered_func path
    """
    import os    
    
    filtered_func_paths = []
    affine_files = []
    ev_file_groups = []
    
    for path in os.listdir(base_feat_path):
        # if not os.path.isdir(file):
        #     print(f"File {file} is not a directory")
        #     continue
        
        is_linear_feat_path = not "NL" in path
        
        if linear_feat and not is_linear_feat_path:
            continue
        elif not linear_feat and is_linear_feat_path:
            continue
        
        feat_path = os.path.join(base_feat_path, path)
        
        filtered_func_path = os.path.join(feat_path, "filtered_func_data.nii.gz")
        
        if not os.path.exists(filtered_func_path):
            if verbose:
                print(f"Filtered func path {filtered_func_path} does not exist")
            continue
                    
        affine_file = os.path.join(feat_path, "reg", "example_func2standard.mat")
 
        if not os.path.exists(affine_file):
            if verbose:
                print(f"Affine file {affine_file} does not exist")
            continue
        
        ev_files = []
        
        for i in range(1, 5):
            ev_file = os.path.join(feat_path, "custom_timing_files", f"ev{i}.txt")
            
            if not os.path.exists(ev_file):
                if verbose:
                    print(f"EV file {ev_file} does not exist")
                continue
            
            ev_files.append(ev_file)
            
 
        # pairs must be at same indices
        filtered_func_paths.append(filtered_func_path)
        affine_files.append(affine_file)
        ev_file_groups.append(ev_files)
        
    
    return filtered_func_paths, affine_files, ev_file_groups

def roi_extract_all_timeseries_node_func(input_nifti_path: str, mask_file_path: str):
    """
    Extracts all the ROIs from the input nifti file, must be 4D
    """
    from nilearn.image import load_img
    import numpy as np
    import logging     
    import regex as re       
    
    subj_regex = r"sub-([^_/]+)" # match 'sub-' and any non-delimter characters ('_' or '/')
    run_regex = r"run-([\d]+)"    # 'run-' and any digits    
    session_regex = r"ses-([^_/]+)" # 'ses-' and any non-delimter characters ('_' or '/')
    
    # Extract the subject, run, and session from the input nifti path
    subj_match = re.search(subj_regex, input_nifti_path)
    run_match = re.search(run_regex, input_nifti_path)    
    session_match = re.search(session_regex, input_nifti_path)
    
    subject_id = subj_match.group(1) if subj_match else None
    run = int(run_match.group(1)) if run_match else None
    session = session_match.group(1) if session_match else None
    
    # Load the nifti file
    data = load_img(input_nifti_path).get_fdata()
    
    if (len(data.shape) != 4):
        raise ValueError("roi_extract_all_timeseries_node_func: Input nifti file must be 4D")
    
    # Load the mask file
    mask_data = load_img(mask_file_path).get_fdata()
    
    # roi_nums = np.unique(mask_data) <- ideal but slower
    roi_nums = range(1, 12) # 11 ROIs, numbered 1-11 
    
    roi_dicts = []
    
    for roi_num in roi_nums:
        roi_mask_indices = np.argwhere(mask_data == roi_num)

        print(f"ROI {roi_num} has {len(roi_mask_indices)} voxels")

        for time_index in range(data.shape[3]):
            for (xi, yi, zi) in roi_mask_indices:
                value = data[xi, yi, zi, time_index]
                roi_dicts.append({
                    'x': xi, 
                    'y': yi, 
                    'z': zi, 
                    'raw_value': value, 
                    'roi_num': roi_num, 
                    'time_index': time_index,
                    'subject_id': subject_id,
                    'run': run,
                    'session': session
                })                                     
                        
    return roi_dicts


def join_main(joined_dicts: list):  
    """
    Joins and flattens the dictionaries
    """    
    
    flattened = []
    
    for array in joined_dicts:
        for dict in array:
            flattened.append(dict)                
    
    return flattened

def make_csv_node_func(flattened: list):
    """ 
    Make a CSV file from dicts        
    """    
    import pandas as pd
    import os        
        
    # create dataframe
    df = pd.DataFrame(flattened)
        
    # save dataframe to csv
    save_path = os.path.join(os.getcwd(), "roi_timeseries.csv")
    df.to_csv(save_path, index=False)
    
    return save_path    

if __name__ == "__main__":
    import constants
    # test registration node function
    
    feat_path = constants.FEAT_BASE_DIR
    
    filtered_func_paths, affine_files, ev_file_groups = get_all_paths(feat_path, verbose=False)
    
    filtered_func_path = filtered_func_paths[0]
    affine_file = affine_files[0]    
    
    print(f"Filtered func path: {filtered_func_path}")
    print(f"Affine file: {affine_file}")
    
    print("Ev file groups sample", ev_file_groups[0])
    
    # out_path, nonlinear = registration_node_func(nonlinear=False, in_file=filtered_func_path, affine_file=affine_file, mni_template=constants.MNI_TEMPLATE, force_run=True, no_affine=False)