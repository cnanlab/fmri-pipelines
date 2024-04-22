import os
import nipype.interfaces.fsl as fsl
from nipype import Node, Workflow, MapNode, IdentityInterface, JoinNode
from nipype.interfaces.utility import Function
from nipype.interfaces.io import DataSink
import utils
import constants
from os.path import join as opj

zfstats_and_affines_itersource = Node(interface=IdentityInterface(fields=['zfstat_path', 'affine_file']),
                  name="zfstats_and_affines_itersource")
zfstats_and_affines_itersource.synchronize = True # To avoid all permutations of the two lists being run (zfstat_path and affine_file should be paired)

rois = range(1, 12) # 11 ROIs, numbered 1-11

rois_itersource = Node(interface=IdentityInterface(fields=['roi_num']), name="rois_itersource")
rois_itersource.iterables = [("roi_num", rois)]

fnirt_node = Node(fsl.FNIRT(ref_file=constants.MNI_TEMPLATE, output_type='NIFTI_GZ'), name="fnirt")

dummy_fnirt_node = Node(Function(input_names=['in_file', 'affine_file'], output_names=["warped_file"], function=utils.dummy_fnirt), name="dummy_fnirt")

# custom_fnirt_node = Node(Function(input_names=['in_file', 'affine_file'], output_names=["warped_file"], function=utils.custom_fnirt), name="custom_fnirt")

roi_extract_node = Node(Function(input_names=['input_nifti', 'roi_num', 'mask_file_path'], output_names=["roi_values", "zfstat_path", "roi_num"], function=utils.roi_extract_node_func), name="roi_extract")
roi_extract_node.inputs.mask_file_path = constants.MASK_FILE_PATH

avg_node = Node(Function(input_names=['roi_values', "zfstat_path", "roi_num"], output_names=["dict"], function=utils.average_roi_values_node_func), name="avg")

first_join_node = JoinNode(Function(input_names=["dict"], output_names=["dict"], function=utils.join), name="first_join", joinsource="rois_itersource", joinfield=["dict"])

join_all_node = JoinNode(Function(input_names=["joined_dicts"], output_names=["flattened"], function=utils.join_main), name="join_all", joinsource="zfstats_and_affines_itersource", joinfield=["joined_dicts"])

make_csv_node = Node(Function(input_names=["flattened"], output_names=["save_path"], function=utils.make_csv_node_func), name="make_csv")

datasink = Node(DataSink(base_directory=constants.ROI_BASE_DIR, container="datasink"), name="datasink")

if __name__ == "__main__":
    print(f"pipeline base dir: {constants.PIPELINE_BASE_DIR}")
    print(f"working dir: {constants.WORKING_DIR}")
    print(f"roi base dir: {constants.ROI_BASE_DIR}")
    
    print(f"Using MNI template: {constants.MNI_TEMPLATE}")
    
    
    roi_extract_workflow = Workflow(name="roi_extract_workflow", base_dir=constants.WORKING_DIR)
    
    # get zfstat paths and affine files
    zfstat_paths = utils.get_all_zfstat_paths_from_feat_datasink(constants.INPUT_FEAT_DATASINK)        
    affine_files = utils.get_all_affine_files_from_feat_datasink(constants.INPUT_FEAT_DATASINK)
    
    print(f"Found {len(zfstat_paths)} zfstat paths")    
    total_num_feat_dirs = len(os.listdir(constants.INPUT_FEAT_DATASINK))
    print(f"Total number of FEAT directories: {total_num_feat_dirs}")
    print(f"Missing zfstat paths: {total_num_feat_dirs * 6 - len(zfstat_paths)}")
    
    ##########################################
    # For testing, use only first few zfstat paths and affine files
    ##########################################
    if "--test" in os.sys.argv:
        test_n = 3
        zfstat_paths = zfstat_paths[:test_n]
        affine_files = affine_files[:test_n]
        print(f"Using only first {test_n} zfstat paths and affine files for testing")
        if test_n < 10:
            print(f"zfstat_paths: {zfstat_paths}")
    
    zfstats_and_affines_itersource.iterables = [("zfstat_path", zfstat_paths), ("affine_file", affine_files)]
    
    ###### Connect nodes
    
    # Use a 'dummy' fnirt node if the '--no-fnirt' argument is passed (for easier testing without fnirt)
    if not "--no-fnirt" in os.sys.argv: 
        roi_extract_workflow.connect([(zfstats_and_affines_itersource, fnirt_node, [("affine_file", "affine_file"),
                                                                                    ("zfstat_path", "in_file")]),
                                      (fnirt_node, roi_extract_node, [("warped_file", "input_nifti")]),
        ])
    else:
        roi_extract_workflow.connect([(zfstats_and_affines_itersource, dummy_fnirt_node, [("affine_file", "affine_file"),
                                                                                    ("zfstat_path", "in_file")]),
                                      (dummy_fnirt_node, roi_extract_node, [("warped_file", "input_nifti")]),
        ])
        
    # main connections
    roi_extract_workflow.connect([ (rois_itersource, roi_extract_node, [("roi_num", "roi_num")]),
                                    (roi_extract_node, avg_node, [("roi_values", "roi_values"),
                                                                  ("zfstat_path", "zfstat_path"),
                                                                  ("roi_num", "roi_num")]),
                                    (avg_node, first_join_node, [("dict", "dict")]), 
                                    (first_join_node, join_all_node, [("dict", "joined_dicts")]),
                                    (join_all_node, make_csv_node, [("flattened", "flattened")]),
                                    (make_csv_node, datasink, [("save_path", "roi_csv")])
                                    ])    
                                 
    
    # set crash directory
    roi_extract_workflow.config["execution"]["crashdump_dir"] = opj(roi_extract_workflow.config["execution"]["crashdump_dir"], constants.WORKING_DIR_NAME, "crash")

    # write graphs 
    if "--exec-graph" or "--test" in os.sys.argv:
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
        
    run = roi_extract_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 32})