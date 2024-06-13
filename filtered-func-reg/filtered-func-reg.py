import argparse
from logging import log
from nipype import Node, Workflow, Function, IdentityInterface, DataSink
import os
import time

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
    
    out_feat_path = os.path.join(os.path.dirname(in_file), in_file_name)
    
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
    
    print(f"{node_name}_NODE: {in_file} -> {out_name} stdout: {stdout}")
    
    end_time = time.time()                
    
    print(f"{node_name}_NODE: {in_file} -> {out_name} took {end_time - start_time} seconds, {(end_time - start_time) / 60} minutes.")
    
    out_path = os.path.join(os.getcwd(), out_name)
    
    # copy the fnirt file to the location where the input file is (FEAT directory)
    dest = shutil.copy(out_path, out_feat_path)
    
    print(f"{node_name}_NODE: Copied {out_path} to {dest}")
    
    return out_feat_path, nonlinear            
      
def get_all_filtered_func_paths_and_affine_files(base_feat_path: str, verbose=False):
    """
    Get all filtered_func paths and affine files from the FEAT directory.
    
    base_feat_path (str): Base FEAT directory path
    """
    import os    
    
    filtered_func_paths = []
    affine_files = []
    
    for file in os.listdir(base_feat_path):
        # if not os.path.isdir(file):
        #     print(f"File {file} is not a directory")
        #     continue
        
        feat_path = os.path.join(base_feat_path, file)
        
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
        affine_files.append(affine_file[0])
    
    return filtered_func_paths, affine_files
      
##############
# Constants
##############
FEAT_BASE_DIR = "/mnt/storage/daniel/feat-preprocess-datasink/additional_150_subjs"

MNI_TEMPLATE = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz' # for FLIRT

MNI_TEMPLATE_SKULL = '/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz' # for FNIRT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKING_DIR = os.path.join(BASE_DIR, "workingdir")

##############
# Nodes
##############
itersource = Node(interface=IdentityInterface(fields=["filtered_func", "affine_file"]), name="itersource")
itersource.synchronize = True # do not do all permutations

registration_node = Node(interface=Function(input_names=["nonlinear", "in_file", "affine_file", "mni_template", "force_run", "no_affine"], output_names=["out_file", "nonlinear"], function=registration_node_func), name="registration_node")                  

datasink = Node(interface=DataSink(), name="datasink")   
datasink.inputs.base_directory = os.path.join(BASE_DIR, "4d-registration-datasink")

##############
# Parser
##############
parser = argparse.ArgumentParser(description="Register filtered_func's to MNI template")
parser.add_argument("--force_run", action="store_true", help="Whether to force run the registration node (ignore if the output file already exists)")
parser.add_argument("--no_affine", action="store_true", help="Whether to use affine file (transfromation matrix) or not (FNIRT only)")
parser.add_argument("--base_feat_path", type=str, help="Base FEAT directory path")
parser.add_argument("--exec_graph", action="store_true", help="Whether to write the execution graph")
parser.add_argument("--n_procs", type=int, help="Number of processes to run the workflow")
parser.add_argument("-n", "--num_subjects", type=int, help="Number of subjects to run the workflow")
parser.add_argument("-y", "--yes", action="store_true", help="Whether to run the workflow without asking for confirmation")

if __name__ == "__main__":
    
    args = parser.parse_args()    
    
    feat_base_dir = args.base_feat_path if args.base_feat_path else FEAT_BASE_DIR
    
    print("Feat base dir:", feat_base_dir)
    
    filtered_func_paths, affine_files = get_all_filtered_func_paths_and_affine_files(feat_base_dir)    
    
    nonlinear_iterable = [False] * len(filtered_func_paths)
    
    itersource.iterables = [("filtered_func", filtered_func_paths), ("affine_file", affine_files), ("nonlinear_reg", [False])]        
    
    print(f"There are {len(filtered_func_paths)} filtered_func paths and {len(affine_files)} affine files")
    assert(len(filtered_func_paths) == len(affine_files))
    
    filtered_func_paths = filtered_func_paths[:args.num_subjects] if args.num_subjects else filtered_func_paths
    affine_files = affine_files[:args.num_subjects] if args.num_subjects else affine_files
    
    print(f"Using {len(filtered_func_paths)} subjects")
    
    print(f"Nonlinear registration: {False}")
    
    registration_node.inputs.nonlinear = False
    registration_node.inputs.mni_template = MNI_TEMPLATE
    registration_node.inputs.force_run = args.force_run or False        
    registration_node.inputs.no_affine = args.no_affine or False    
    
    print(f"Registration node base inputs:\n{"-" * 20}")    
    print(f"Nonlinear: {registration_node.inputs.nonlinear}")
    print(f"MNI template: {registration_node.inputs.mni_template}")
    print(f"Force run: {registration_node.inputs.force_run}")
    print(f"No affine: {registration_node.inputs.no_affine}") 
    
    workflow = Workflow(name="filtered_func_reg_workflow")
    
    # connect the nodes
    workflow.connect(itersource, "filtered_func", registration_node, "in_file")
    workflow.connect(itersource, "affine_file", registration_node, "affine_file")
    workflow.connect(registration_node, "out_file", datasink, "registered_files")
    workflow.connect(registration_node, "nonlinear", datasink, "nonlinear")
        
    crash_dir = os.path.join(WORKING_DIR, "crash")
    
    # set crash directory
    workflow.config["execution"]["crashdump_dir"] = crash_dir

    # write graphs 
    if args.exec_graph:
        workflow.write_graph(graph2use="exec", dotfilename="exec_graph.dot", format="png")    
        
    workflow.write_graph(graph2use="colored", format="png")
    
    # if '-y' argument is passed, run the workflow without asking for confirmation
    if args.yes:
        s = "yes"
    else:
        s = input("Would you like to run the workflow? (Y/n)")

    if not (s.lower() == "yes" or s.lower() == "y"):
        print("Exiting...")
        exit(0)
        
    start_time = time.time()    
    
    n_procs = args.n_procs if args.n_procs else 56
    
    run = workflow.run(plugin="MultiProc", plugin_args={"n_procs": n_procs})
    
    end_time = time.time()
    
    print(f"Time taken: {end_time - start_time} seconds, or {(end_time - start_time) / 60} minutes, or {(end_time - start_time) / 3600} hours")