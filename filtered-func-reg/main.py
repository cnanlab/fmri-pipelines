import argparse
from logging import log
from nipype import Node, Workflow, Function, IdentityInterface, DataSink, JoinNode, MapNode
import os
import time
import utils
import constants

##############
# Nodes
##############
itersource = Node(interface=IdentityInterface(fields=["filtered_func", "affine_file", "ev_files"]), name="itersource")
itersource.synchronize = True # do not do all permutations

registration_node = Node(interface=Function(input_names=["nonlinear", "in_file", "affine_file", "mni_template", "force_run", "no_affine"], output_names=["out_file", "nonlinear"], function=utils.registration_node_func), name="registration_node")                  

# join_node = JoinNode(interface=Function(input_names=["in_reg_files"], function=utils.registration_node_func), name="join_node", joinsource="itersource", joinfield=["in_reg_files"])

roi_extract_timeseries = Node(interface=Function(input_names=["input_nifti_path", "mask_file_path"], output_names=["roi_dicts"], function=utils.roi_extract_all_timeseries_node_func), name="roi_extract_timeseries")
roi_extract_timeseries.inputs.mask_file_path = constants.MASK_PATH

join_node = JoinNode(interface=Function(input_names=["joined_dicts"], output_names=["flattened"], function=utils.join_main), name="join_node", joinsource="itersource", joinfield=["joined_dicts"])

csv_node = Node(interface=Function(input_names=["flattened"], output_names=["save_path"], function=utils.make_csv_node_func), name="csv_node")

datasink = Node(interface=DataSink(), name="datasink")   
datasink.inputs.base_directory = os.path.join(constants.BASE_DIR, "filtered_func_reg_datasink")

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
parser.add_argument("--linear_feat", action="store_true", help="Whether to use linear feat paths only")

if __name__ == "__main__":
    
    args = parser.parse_args()    
    
    feat_base_dir = args.base_feat_path if args.base_feat_path else constants.FEAT_BASE_DIR
    
    print("Feat base dir:", feat_base_dir)
    
    filtered_func_paths, affine_files, ev_groups = utils.get_all_paths(feat_base_dir)            
    
    print()
    print(f"Filtered func paths sample (5): {filtered_func_paths[:5]}\n")
    print(f"Affine files sample (2): {affine_files[:2]}\n")
    print(f"Ev groups sample (1): {ev_groups[:1]}\n")
    
    print(f"There are {len(filtered_func_paths)} filtered_func paths and {len(affine_files)} affine files")
    assert(len(filtered_func_paths) == len(affine_files))
    
        
    filtered_func_paths = filtered_func_paths[:args.num_subjects] if args.num_subjects else filtered_func_paths
    affine_files = affine_files[:args.num_subjects] if args.num_subjects else affine_files
    
    print(f"Using {len(filtered_func_paths)} subjects")
    
    itersource.iterables = [("filtered_func", filtered_func_paths), ("affine_file", affine_files)]           
        
    print(f"Nonlinear registration: {False}")
    
    registration_node.inputs.nonlinear = False
    registration_node.inputs.mni_template = constants.MNI_TEMPLATE
    registration_node.inputs.force_run = args.force_run or False        
    registration_node.inputs.no_affine = args.no_affine or False    
    
    print()
    print(f"Registration node base inputs:\n{"-" * 20}")    
    print(f"Nonlinear: {registration_node.inputs.nonlinear}")
    print(f"MNI template: {registration_node.inputs.mni_template}")
    print(f"Force run: {registration_node.inputs.force_run}")
    print(f"No affine: {registration_node.inputs.no_affine}")     
    print(f"Mask path: {roi_extract_timeseries.inputs.mask_file_path}")
    print()
    
    workflow = Workflow(name="filtered_func_reg_workflow", base_dir=constants.WORKING_DIR)
    
    # connect the nodes
    workflow.connect(itersource, "filtered_func", registration_node, "in_file")
    workflow.connect(itersource, "affine_file", registration_node, "affine_file")
    # workflow.connect(registration_node, "out_file", datasink, "reg.@out_file")
    # workflow.connect(registration_node, "nonlinear", datasink, "reg.@nonlinear")
    workflow.connect(registration_node, "out_file", roi_extract_timeseries, "input_nifti_path")
    workflow.connect(roi_extract_timeseries, "roi_dicts", join_node, "joined_dicts")
    workflow.connect(join_node, "flattened", csv_node, "flattened")
    workflow.connect(csv_node, "save_path", datasink, "csv.@save_path")
        
    crash_dir = os.path.join(constants.WORKING_DIR, "crash")
    
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