import os
import nipype.interfaces.fsl as fsl
from nipype import Node, Workflow, MapNode, IdentityInterface, JoinNode
from nipype.interfaces.utility import Function
from nipype.interfaces.io import DataSink
import utils
import constants
from os.path import join as opj

itersource = Node(interface=IdentityInterface(fields=['zfstat_path', 'affine_file', "subject_id", "run", "image_name"]),
                  name="itersource")
itersource.synchronize = True # To avoid all permutations of the lists being run

# rois = range(1, 12) # 11 ROIs, numbered 1-11

# rois_itersource = Node(interface=IdentityInterface(fields=['roi_num']), name="rois_itersource")
# rois_itersource.iterables = [("roi_num", rois)]

dummy_fnirt_node = Node(Function(input_names=['in_file', 'affine_file', 'mni_template'], output_names=["warped_file"], function=utils.dummy_fnirt), name="dummy_fnirt")

# fnirt_node = Node(fsl.FNIRT(ref_file=constants.MNI_TEMPLATE, output_type='NIFTI_GZ'), name="fnirt")

custom_fnirt_node = Node(Function(input_names=['in_file', 'affine_file', 'mni_template'], output_names=["warped_file"], function=utils.custom_fnirt), name="custom_fnirt")
custom_fnirt_node.inputs.mni_template = constants.MNI_TEMPLATE

# roi_extract_node = Node(Function(input_names=['input_nifti', 'roi_num', 'mask_file_path'], output_names=["roi_values", "zfstat_path", "roi_num"], function=utils.roi_extract_node_func), name="roi_extract", overwrite=True)
# roi_extract_node.inputs.mask_file_path = constants.MASK_FILE_PATH

# avg_node = Node(Function(input_names=['roi_values', "zfstat_path", 'roi_num'], output_names=["dict"], function=utils.average_roi_values_node_func), name="avg")

# first_join_node = JoinNode(Function(input_names=["dict"], output_names=["dict"], function=utils.join), name="first_join", joinsource="rois_itersource", joinfield=["dict"])

roi_extract_overwrite = False

# roi extract function that also creates dicts with all of the metadata needed
roi_extract_all_node = Node(Function(input_names=['input_nifti', 'mask_file_path', 'subject_id', 'run', 'image_name'], output_names=["roi_values_dicts"], function=utils.roi_extract_all_node_func), name="roi_extract_all", overwrite=roi_extract_overwrite)
roi_extract_all_node.inputs.mask_file_path = constants.MASK_FILE_PATH

avg_all_node = Node(Function(input_names=['roi_values_dicts'], output_names=["avg_dicts"], function=utils.average_each_roi_values_node_func), name="avg_all")

join_all_node = JoinNode(Function(input_names=["joined_dicts"], output_names=["flattened"], function=utils.join_main), name="join_all", joinsource="itersource", joinfield=["joined_dicts"])

make_csv_node = Node(Function(input_names=["flattened"], output_names=["save_path"], function=utils.make_csv_node_func), name="make_csv")

datasink = Node(DataSink(), name="datasink")

if __name__ == "__main__":
    print(f"pipeline base dir: {constants.PIPELINE_BASE_DIR}")    
    print(f"roi base dir: {constants.ROI_BASE_DIR}")    
    print(f"Using MNI template: {constants.MNI_TEMPLATE}")
    print(f"input feat datasink: {constants.INPUT_FEAT_DATASINK}")
    print(f"mask file path: {constants.MASK_FILE_PATH}")
    print(f"roi_extract_overwrite: {roi_extract_overwrite}")
    
    is_test_run = "--test" in os.sys.argv
    
    # set working dir and datasink base directory
    workingdir = constants.WORKING_DIR if not is_test_run else opj(constants.ROI_BASE_DIR, "testworkingdir")
    datasink.inputs.base_directory = constants.ROI_DATASINK if not is_test_run else opj(constants.ROI_BASE_DIR, "testdatasink")
    
    print(f"working dir: {workingdir}")
    print(f"datasink base directory: {datasink.inputs.base_directory}")
    
    roi_extract_workflow = Workflow(name="roi_extract_workflow", base_dir=workingdir)
    
    # get zfstat paths and affine files
    zfstat_paths = utils.get_all_zfstat_paths_from_feat_datasink(constants.INPUT_FEAT_DATASINK)        
    affine_files = utils.get_all_affine_files_from_feat_datasink(constants.INPUT_FEAT_DATASINK)
    subject_ids = [utils.get_subject_id_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    runs = [utils.get_run_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    image_names = [utils.get_image_name_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    
    print(f"Found {len(zfstat_paths)} zfstat paths")    
    total_num_feat_dirs = len(os.listdir(constants.INPUT_FEAT_DATASINK))
    print(f"Total number of FEAT directories: {total_num_feat_dirs}")
    print(f"Missing zfstat paths: {total_num_feat_dirs * 6 - len(zfstat_paths)}")
    
    ################################################################
    # For testing, use only first few zfstat paths and affine files
    ################################################################
    if is_test_run:
        test_n = 2
        zfstat_paths = zfstat_paths[:test_n]
        affine_files = affine_files[:test_n]
        print(f"Using only first {test_n} zfstat paths and affine files for testing")
        if test_n < 10:
            print(f"zfstat_paths: {zfstat_paths}")
    
    itersource.iterables = [("zfstat_path", zfstat_paths), ("affine_file", affine_files)]
    
    ###### Connect nodes
    
    # Use a 'dummy' fnirt node if the '--no-fnirt' argument is passed (for easier testing without fnirt)
    fnirt_node = dummy_fnirt_node if "--no-fnirt" in os.sys.argv else custom_fnirt_node 
    roi_extract_workflow.connect([(itersource, fnirt_node, [("affine_file", "affine_file"),
                                                                ("zfstat_path", "in_file")]),                                    
                                    (itersource, roi_extract_all_node, [("subject_id", "subject_id"),
                                                                        ("run", "run"),
                                                                        ("image_name", "image_name")])
                                    (fnirt_node, roi_extract_all_node, [("warped_file", "input_nifti")]),
                                    (fnirt_node, datasink, [("warped_file", "fnirt.@warped")]),
    ])                   
        
    # main connections
    roi_extract_workflow.connect([(roi_extract_all_node, avg_all_node, [("roi_dicts", "roi_dicts")]),
                                    (avg_all_node, join_all_node, [("avg_dicts", "joined_dicts")]),                                    
                                    (join_all_node, make_csv_node, [("flattened", "flattened")]),
                                    (make_csv_node, datasink, [("save_path", "roi_csv")]),                                    
                                    ])    
                                 
    
    # set crash directory
    roi_extract_workflow.config["execution"]["crashdump_dir"] = opj(roi_extract_workflow.config["execution"]["crashdump_dir"], constants.WORKING_DIR_NAME, "crash")

    # write graphs 
    if "--exec-graph" in os.sys.argv or is_test_run:
        roi_extract_workflow.write_graph(graph2use="exec", dotfilename="exec_graph.dot", format="png")    
        
    roi_extract_workflow.write_graph(graph2use="colored", format="png")
    

    # if '-y' argument is passed, run the workflow without asking for confirmation
    if "-y" in os.sys.argv:
        s = "yes"
    else:
        s = input("Would you like to run the workflow? (Y/n)")

    if not (s.lower() == "yes" or s.lower() == "y"):
        print("Exiting...")
        exit(0)
        
    run = roi_extract_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 64})