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
      
def get_all_filtered_func_paths_and_affine_files(base_feat_path: str, linear_feat=True, verbose=False):
    """
    Get all filtered_func paths and affine files from the FEAT directory.
    
    base_feat_path (str): Base FEAT directory path
    """
    import os    
    
    filtered_func_paths = []
    affine_files = []
    
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
 
        # pairs must be at same indices
        filtered_func_paths.append(filtered_func_path)
        affine_files.append(affine_file)
    
    return filtered_func_paths, affine_files

if __name__ == "__main__":
    import constants
    # test registration node function
    
    feat_path = constants.FEAT_BASE_DIR
    
    filtered_func_paths, affine_files = get_all_filtered_func_paths_and_affine_files(feat_path, verbose=False)
    
    filtered_func_path = filtered_func_paths[0]
    affine_file = affine_files[0]
    
    print(f"Filtered func path: {filtered_func_path}")
    print(f"Affine file: {affine_file}")
    
    out_path, nonlinear = registration_node_func(nonlinear=False, in_file=filtered_func_path, affine_file=affine_file, mni_template=constants.MNI_TEMPLATE, force_run=True, no_affine=False)