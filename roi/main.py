import os
import time
import nipype.interfaces.fsl as fsl
from nipype import Node, Workflow, MapNode, IdentityInterface, JoinNode
from nipype.interfaces.utility import Function
from nipype.interfaces.io import DataSink
import utils
import constants
from os.path import join as opj

itersource = Node(interface=IdentityInterface(fields=['zfstat_path', 'affine_file', "subject_id", "run", "image_name", "session"]),
                  name="itersource")
itersource.synchronize = True # To avoid all permutations of the lists being run

# rois = range(1, 12) # 11 ROIs, numbered 1-11

# rois_itersource = Node(interface=IdentityInterface(fields=['roi_num']), name="rois_itersource")
# rois_itersource.iterables = [("roi_num", rois)]

# custom_flirt_node = Node(Function(input_names=['in_file', 'in_matrix_file'], output_names=['out_file', ]), name="custom_flirt")

# dummy_fnirt_node = Node(Function(input_names=['in_file', 'affine_file', 'mni_template', 'subject_id', 'run', 'image_name'], output_names=["warped_file"], function=utils.dummy_fnirt), name="dummy_fnirt")
# dummy_fnirt_node.inputs.mni_template = constants.MNI_TEMPLATE_SKULL

# fnirt_node = Node(fsl.FNIRT(ref_file=constants.MNI_TEMPLATE, output_type='NIFTI_GZ'), name="fnirt")


# print("WARN: no affine file is being used for custom_fnirt_node for testing purposes")
# custom_fnirt_node = Node(Function(input_names=['in_file', 'affine_file', 'mni_template', 'force_run', 'no_affine'], output_names=["warped_file"], function=utils.custom_fnirt), name="custom_fnirt")
# custom_fnirt_node.inputs.mni_template = constants.MNI_TEMPLATE_SKULL

registration_node = Node(Function(input_names=['nonlinear', 'in_file', 'affine_file', 'mni_template', 'force_run', 'no_affine'], output_names=["out_file", "nonlinear"], function=utils.registration_node_func), name="registration")
registration_node.synchronize = True

# roi_extract_node = Node(Function(input_names=['input_nifti', 'roi_num', 'mask_file_path'], output_names=["roi_values", "zfstat_path", "roi_num"], function=utils.roi_extract_node_func), name="roi_extract", overwrite=True)
# roi_extract_node.inputs.mask_file_path = constants.MASK_FILE_PATH

# avg_node = Node(Function(input_names=['roi_values', "zfstat_path", 'roi_num'], output_names=["dict"], function=utils.average_roi_values_node_func), name="avg")

# first_join_node = JoinNode(Function(input_names=["dict"], output_names=["dict"], function=utils.join), name="first_join", joinsource="rois_itersource", joinfield=["dict"])

roi_extract_overwrite = False

# roi extract function that also creates dicts with all of the metadata needed
roi_extract_all_node = Node(Function(input_names=['input_nifti', 'mask_file_path', 'is_test_run', 'no_avg'], output_names=["roi_dicts"], function=utils.roi_extract_all_node_func), name="roi_extract_all", overwrite=roi_extract_overwrite)
roi_extract_all_node.inputs.mask_file_path = constants.MASK_FILE_PATH

avg_all_node = Node(Function(input_names=['roi_dicts'], output_names=["avg_dicts"], function=utils.average_each_roi_values_node_func), name="avg_all")

add_metadata_node = Node(Function(input_names=["dicts", "subject_id", "run", "image_name", "is_nonlinear", "session"], output_names=["dicts_with_metadata"], function=utils.add_metadata_node_func), name="add_metadata")

join_all_node = JoinNode(Function(input_names=["joined_dicts"], output_names=["flattened"], function=utils.join_main), name="join_all", joinsource="itersource", joinfield=["joined_dicts"])

make_csv_node = Node(Function(input_names=["flattened"], output_names=["save_path"], function=utils.make_csv_node_func), name="make_csv")

datasink = Node(DataSink(), name="datasink")

if __name__ == "__main__":
    print(f"pipeline base dir: {constants.PIPELINE_BASE_DIR}")    
    print(f"roi base dir: {constants.ROI_BASE_DIR}")        
    print(f"input feat datasink: {constants.INPUT_FEAT_DATASINK}")
    print(f"mask file path: {constants.MASK_FILE_PATH}")
    print(f"roi_extract_overwrite: {roi_extract_overwrite}")    
    
    # run with only a few paths
    is_test_run = "--test" in os.sys.argv        
    
    # force running FNIRT registration
    is_force_run_fnirt = "--force-run-fnirt" in os.sys.argv     
    
    # force running FLIRT registration
    is_force_run = "--force-run" in os.sys.argv   
    
    # do not average the ROIs, keep x,y,z values for each voxel
    is_no_avg = "--no-avg" in os.sys.argv      
    roi_extract_all_node.inputs.no_avg = is_no_avg        
    print(f"is_no_avg: {is_no_avg}")
    
    nonlinear_iterables = []
    force_run_iterables = []
    mni_template_iterables = []
    
    # "--flirt" required for FLIRT registration
    if "--flirt" in os.sys.argv:
        nonlinear_iterables = [False]
        force_run_iterables = [is_force_run]
        mni_template_iterables = [constants.MNI_TEMPLATE]    
    
    registration_node.iterables = [("nonlinear", nonlinear_iterables), 
                                   ("force_run", force_run_iterables), 
                                   ("mni_template", mni_template_iterables)]
    
    if "--fnirt" in os.sys.argv:
        nonlinear_iterables.append(True)
        force_run_iterables.append(is_force_run_fnirt)
        mni_template_iterables.append(constants.MNI_TEMPLATE_SKULL)
    
    for i, is_nonlinear in enumerate(nonlinear_iterables):
        name = "FNIRT" if is_nonlinear else "FLIRT"
        
        print(f"{name}:")
        print("--------------------")
        print(f"force_run: {force_run_iterables[i]}")
        print(f"mni_template: {mni_template_iterables[i]}")
        print()
    
    # set working dir and datasink base directory, pulled from constants.py for non-tests
    workingdir = constants.WORKING_DIR if not is_test_run else opj(constants.ROI_BASE_DIR, "testworkingdir")
    datasink.inputs.base_directory = constants.ROI_DATASINK if not is_test_run else opj(constants.ROI_BASE_DIR, "testdatasink")
        
    print(f"working dir: {workingdir}")
    print(f"datasink base directory: {datasink.inputs.base_directory}")    
    
    roi_extract_all_node.inputs.is_test_run = is_test_run
    
    roi_extract_workflow = Workflow(name="roi_extract_workflow", base_dir=workingdir)
    
    feat_reg_type = "both"
    
    print(f"feat_reg_type: {feat_reg_type}")
    
    # get zfstat paths and affine files
    zfstat_paths, affine_files = utils.get_all_zfstat_paths_and_affine_files_from_feat_datasink(constants.INPUT_FEAT_DATASINK, feat_reg_type=feat_reg_type)
            
    # check how many zfstat paths were found
    print()
    print(f"Found {len(affine_files)} affine files")
    print(f"Found {len(zfstat_paths)} zfstat paths")     
    print(f"Sample zfstat paths: {zfstat_paths[:2]}")
    print(f"Sample affine files: {affine_files[:2]}")
    total_num_feat_dirs = len(os.listdir(constants.INPUT_FEAT_DATASINK))
    print(f"Total number of NL FEAT directories: {total_num_feat_dirs}")
    print(f"Missing zfstat paths: {total_num_feat_dirs * 6 - len(zfstat_paths)}/{total_num_feat_dirs * 6} ({(total_num_feat_dirs * 6 - len(zfstat_paths)) / (total_num_feat_dirs * 6) * 100}%)")
    
    ################################################################
    # For testing, use only first few zfstat paths and affine files
    ################################################################
    if is_test_run:
        test_n = 4
        zfstat_paths = zfstat_paths[:test_n]
        affine_files = affine_files[:test_n]
        print(f"Using only first {test_n} zfstat paths and affine files for testing")
        print()
        if test_n < 10:
            print(f"zfstat_paths: {zfstat_paths}")  
    
    subject_ids = [utils.get_subject_id_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    runs = [utils.get_run_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    image_names = [utils.get_image_name_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    sessions = [utils.get_session_from_zfstat_path(zfstat_path) for zfstat_path in zfstat_paths]
    
    # set iterables
    itersource.iterables = [("zfstat_path", zfstat_paths), ("affine_file", affine_files), ("subject_id", subject_ids), ("run", runs), ("image_name", image_names), ("session", sessions)]        
    
    ###### Connect nodes
    
    # Use a 'dummy' fnirt node if the '--no-fnirt' argument is passed (for easier testing without fnirt)
    # if "--no-fnirt" in os.sys.argv:
    #     roi_extract_workflow.connect([(itersource, dummy_fnirt_node, [("affine_file", "affine_file"),
    #                                                                 ("zfstat_path", "in_file"),
    #                                                                 ("subject_id", "subject_id"),
    #                                                                 ("run", "run"),
    #                                                                 ("image_name", "image_name")]),                                                                        
    #                                     (dummy_fnirt_node, roi_extract_all_node, [("warped_file", "input_nifti")]),
    #                                     # (dummy_fnirt_node, datasink, [("warped_file", "fnirt.@warped")]),
    #     ])
    # else:
    #     roi_extract_workflow.connect([(itersource, custom_fnirt_node, [("affine_file", "affine_file"),
    #                                                                 ("zfstat_path", "in_file"),
    #                                                                 ("subject_id", "subject_id"),
    #                                                                 ("run", "run"),
    #                                                                 ("image_name", "image_name")]),                                                                        
    #                                     (custom_fnirt_node, roi_extract_all_node, [("warped_file", "input_nifti")]),
    #                                     # (custom_fnirt_node, datasink, [("warped_file", "fnirt.@warped")]),
    #     ])                   
    
    
    if is_no_avg:
        roi_extract_workflow.connect([
            (roi_extract_all_node, add_metadata_node, [("roi_dicts", "dicts")])
            ])
    else:
        roi_extract_workflow.connect([
            (roi_extract_all_node, avg_all_node, [("roi_dicts", "roi_dicts")]),
            (avg_all_node, add_metadata_node, [("avg_dicts", "avg_dicts")])
            ])
    
    save_dirname = "roi_csv"
    
    if "--save-dirname" in os.sys.argv:
        save_dirname = os.sys.argv[os.sys.argv.index("--save-dirname") + 1]
        print(f"save_dirname: {save_dirname}")                
    
    # connect all nodes
    roi_extract_workflow.connect([(itersource, registration_node, [("affine_file", "affine_file"),
                                                                    ("zfstat_path", "in_file"),]),                                                                        
                                        (registration_node, roi_extract_all_node, [("out_file", "input_nifti")]),
                                        (registration_node, add_metadata_node, [("nonlinear", "is_nonlinear")]),                                        
                                    (itersource, add_metadata_node, [("subject_id", "subject_id"),
                                                                    ("run", "run"),
                                                                    ("image_name", "image_name"),
                                                                    ("session", "session")]),
                                    (add_metadata_node, join_all_node, [("dicts_with_metadata", "joined_dicts")]),
                                    (join_all_node, make_csv_node, [("flattened", "flattened")]),
                                    (make_csv_node, datasink, [("save_path", save_dirname)]), 
        ])              
                                 
    
    crash_dir = opj(workingdir, "crash")
    
    # set crash directory
    roi_extract_workflow.config["execution"]["crashdump_dir"] = crash_dir

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
        
    start_time = time.time()    
    
    run = roi_extract_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 56})
    
    end_time = time.time()
    
    print(f"Time taken: {end_time - start_time} seconds, or {(end_time - start_time) / 60} minutes, or {(end_time - start_time) / 3600} hours")