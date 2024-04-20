import os
from os.path import join as opj
import re
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.interfaces.io import SelectFiles, DataFinder, DataSink
from nipype.interfaces import fsl
from nipype import Workflow, Node, MapNode, JoinNode

import util

# base_feat_dir = '/mnt/Storage/temp1/' # where the input fMRI experiment data is held

BASE_PREPROCESS_DIR = "/home/011/d/ds/dss210005/pipeline/preprocess"
BASE_RANDOMISE_DIR = "/home/011/d/ds/dss210005/pipeline/randomise"

# base_feat_dir = input("Enter the path to (absolute path preferred) base feat directory: ")
base_feat_dir = opj(BASE_PREPROCESS_DIR, "datasink")
# feat_dir = "/home/danielsuh/Downloads/preprocess/preproc_FEAT_datasink"
working_dir = opj(BASE_RANDOMISE_DIR, "workingdir") # cache + report + exec graph output
datasink_dir = opj(BASE_RANDOMISE_DIR, "datasink") # where output is store

feat_dirs = os.listdir(base_feat_dir)

# list of subject identifiers
# subject_id_list = ['NDARINV00BD7VDC', 'NDARINV00CY2MDM', 'NDARINV00HEV6HB', 'NDARINV00LH735Y', 'NDARINV00R4TXET']

import logging
logger = logging.getLogger('nipype.workflow')

subjects_ids_regex = re.compile(r'sub-([\w]+)')

subject_id_list = []
run_list = []
task_list = []
session_list = []
contrast_list = [1, 2, 3, 4, 5, 6]
# nonlinear_list = [False, True]

unique_subjects = set()
unique_runs = set()
unique_tasks = set()
unique_sessions = set()

print("base feat directory contents: "+ str(feat_dirs))

for feat_dir_name in feat_dirs:    
    subject_id = util.get_subject_from_feat_dirname(feat_dir_name)            
    run = util.get_run_from_feat_dirname(feat_dir_name)
    task = util.get_task_from_feat_dirname(feat_dir_name)
    session = util.get_session_from_feat_dirname(feat_dir_name)    
    
    if subject_id not in unique_subjects:
        unique_subjects.add(subject_id)
        subject_id_list.append(subject_id)
    
    if run not in unique_runs:
        unique_runs.add(run)
        run_list.append(run)
    
    if task not in unique_tasks:
        unique_tasks.add(task)
        task_list.append(task)
    
    if session not in unique_sessions:
        unique_sessions.add(session)
        session_list.append(session)
        
# FOR TESTING
# subject_id_list = subject_id_list[:2]

print("SUBJECT ID LIST", subject_id_list)
print("RUN LIST", run_list)
print("TASK LIST", task_list)
print("CONTRAST LIST", contrast_list)
print("SESSION LIST", session_list)

print("Total iterables: ", len(subject_id_list) * len(run_list) * len(task_list) * len(contrast_list) * len(session_list))


templates = {'zfstat': opj(
                        # 'sub-{subject_id}', 
                        #  'ses-{session_name}', 
                        #  'func',
                         'sub-{subject_id}_ses-{session_name}_task-{task_name}_run-{run:02d}LN.feat',
                         'stats',
                         'zfstat{contrast_id}.nii.gz'
                         ),
             'xfm': opj(
                        # 'sub-{subject_id}', 
                        #  'ses-{session_name}', 
                        #  'func',
                         'sub-{subject_id}_ses-{session_name}_task-{task_name}_run-{run:02d}LN.feat',
                         'reg',
                         'example_func2standard.mat'
                         ),
             'zfstat_nonlinear': opj(
                        # 'sub-{subject_id}', 
                        #  'ses-{session_name}', 
                        #  'func',
                         'sub-{subject_id}_ses-{session_name}_task-{task_name}_run-{run:02d}NL.feat',
                         'stats',
                         'zfstat{contrast_id}.nii.gz'
                         ),
             'xfm_nonlinear': opj(
                        # 'sub-{subject_id}', 
                        #  'ses-{session_name}', 
                        #  'func',
                         'sub-{subject_id}_ses-{session_name}_task-{task_name}_run-{run:02d}NL.feat',
                         'reg',
                         'example_func2standard.mat'
                         ),
            }

all_possible_files = []
for subject_id in subject_id_list:
    for run in run_list:
        for task in task_list:
            for contrast in contrast_list:
                for session in session_list:
                    zfstat_file = templates['zfstat'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    xfm_file = templates['xfm'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    zfstat_nonlinear_file = templates['zfstat_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    xfm_nonlinear_file = templates['xfm_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    
                    all_possible_files.append(opj(base_feat_dir, zfstat_file))                    
                    all_possible_files.append(opj(base_feat_dir, xfm_file))
                    all_possible_files.append(opj(base_feat_dir, zfstat_nonlinear_file))
                    all_possible_files.append(opj(base_feat_dir, xfm_nonlinear_file))
                    

print(f"There are {len(all_possible_files)} possible files")

existing_files = util.return_existing_files(all_possible_files)

print(f"There are {len(existing_files)} existing files")

def get_subject_groups_dict_key(contrast, task, session, run):
    return f"{contrast}_{task}_{session}_{run}"

# key is contrast, task, session, run
# value is list of subjects
subject_groups_dict = {}

for file in existing_files:
    subject_id = util.get_subject_from_feat_dirname(file)
    run = util.get_run_from_feat_dirname(file)
    task = util.get_task_from_feat_dirname(file)
    session = util.get_session_from_feat_dirname(file)
    
    for contrast in contrast_list:
        key = get_subject_groups_dict_key(contrast, task, session, run)
        if key not in subject_groups_dict:
            subject_groups_dict[key] = []
        
        subject_groups_dict[key].append(subject_id)

print(f"Subject groups dict: {subject_groups_dict}")

def get_unique_key(subject_id, run, task, contrast, session):
    return f"{subject_id}_{run}_{task}_{contrast}_{session}"

# store zfstat + xfm files in dict based on unique key
flirt_file_paths_dict = {}
fnirt_file_paths_dict = {}

for contrast in contrast_list:
    for task in task_list:
        for session in session_list:
            for run in run_list:
                key = get_subject_groups_dict_key(contrast, task, session, run)
                if key in subject_groups_dict:
                    subject_ids = subject_groups_dict[key]
                    flirt_files = []
                    fnirt_files = []
                    for subject_id in subject_ids:
                        zfstat_file = templates['zfstat'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                        xfm_file = templates['xfm'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                        zfstat_nonlinear_file = templates['zfstat_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                        xfm_nonlinear_file = templates['xfm_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                        
                        
                        zfstat_path = opj(base_feat_dir, zfstat_file)
                        xfm_path = opj(base_feat_dir, xfm_file)
                        zfstat_nonlinear_path = opj(base_feat_dir, zfstat_nonlinear_file)
                        xfm_nonlinear_path = opj(base_feat_dir, xfm_nonlinear_file)
                        
                        unique_key = get_unique_key(subject_id, run, task, contrast, session)
                        
                        flirt_file_paths_dict[unique_key] = {
                            'zfstat': zfstat_path,
                            'xfm': xfm_path                            
                        }
                        
                        fnirt_file_paths_dict[unique_key] = {
                            'zfstat_nonlinear': zfstat_nonlinear_path,
                            'xfm_nonlinear': xfm_nonlinear_path
                        }
                        
                        

# selectfiles = Node(SelectFiles(templates,
#                                base_directory=base_feat_dir,
#                                sort_filelist=True,
#                                raise_on_empty=False),
#                    name="selectfiles")

MNI_template = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

# in_file + in_matrix_file set in workflow.connect(), as they are determined at runtime from SelectFiles
flirt = Node(fsl.FLIRT(reference=MNI_template, apply_xfm=True, padding_size=0, interp="trilinear", output_type='NIFTI_GZ'), name="flirt")

fnirt = Node(fsl.FNIRT(ref_file=MNI_template, output_type='NIFTI_GZ'), name="fnirt")

# # outputs all files from flirt's to 'join' field
# def flatten_and_sort(**kwargs):    
#     import logging
    
#     logger = logging.getLogger('nipype.workflow')  
#     double_wrapped_file_names = list(kwargs.values()) # [[[file1], [file2]]]
#     wrapped_file_names = double_wrapped_file_names[0] # each file name is 'wrapped' in array, ex: [['file1'], ['file2]]    
#     logger.info(double_wrapped_file_names)
#     logger.info(len(double_wrapped_file_names))
#     logger.info(wrapped_file_names)
#     logger.info(len(wrapped_file_names))
    
#     sorted_file_names = sorted([wrapped_file_name[0] for wrapped_file_name in wrapped_file_names])    
#     logger.info("SORTED FILE NAMES")
#     logger.info(sorted_file_names)
#     return sorted_file_names


# join_flirt = JoinNode(Function(input_names=["join_in"], output_names="join_out", function=flatten_and_sort),
#                 joinsource="subject_node", # join on subject_id, as we want to group by subject
#                 joinfield="join_in",              
#                 name="join_flirt")

# join_fnirt = JoinNode(Function(input_names=["join_in"], output_names="join_out", function=flatten_and_sort),
#                 joinsource="subject_node", # join on subject_id, as we want to group by subject
#                 joinfield="join_in",
#                 name="join_fnirt")

# Input: All files from 'join', which should be all copes registered to MNI space
# 
# We need to group files by contrast id, order by subject id, 
# grouped_cope_names = [f'zfstats{contrast_id}_files' for contrast_id in contrast_list]
# def group_copes_func(in_files_array):
#     flattened = [in_files_array[0] for arr in in_files_array] # each path is wrapped in array for some reason    
    
#     print(flattened)
    
#     print(sorted(flattened))    
#     # for contrast_id in contrast_list:
#     #     if f"zfstat{contrast_id}" in   
    
#     return flattened, flattened, flattened, flattened, flattened, flattened
       

# group_copes = Node(Function(input_names=['in_files_array'], output_names=grouped_cope_names, function=group_copes_func), name='group_copes')
# def merge_copes(in_files, contrast_id):
#     from nipype.interfaces import fsl
#     from pathlib import Path
#     grouped_copes = list(filter(lambda file_name: f"zfstat{contrast_id}" in file_name, in_files))
#     print(grouped_copes)
    
#     merge = fsl.Merge(dimension='t')        
#     merge.inputs.in_files = grouped_copes
#     res = merge.run()    
    
    

# merge_copes = Node(Function(input_names=["in_files", "contrast_id"], output_names=["merged", "contrast_id"]), name='merge_copes')
# merge_copes.iterables = [('contrast_id', contrast_list)]

merge_flirt = Node(fsl.Merge(dimension='t'), name="merge_flirt")
merge_fnirt = Node(fsl.Merge(dimension='t'), name="merge_fnirt")

# randomise_fsl = fsl.Randomise(one_sample_group_mean=True, tfce=True, mask=MNI_template, output_type='NIFTI_GZ')

# randomise_fsl.inputs.in_file = "/home/011/d/ds/dss210005/pipeline/randomise/workingdir/randomise/_contrast_id_1/_run_1/_task_name_sst/_session_name_baselineYear1Arm1/merge_flirt/zfstat1_flirt_merged.nii.gz"
# print(f"randomise fsl command: {randomise_fsl.cmdline}")

randomise_flirt = Node(fsl.Randomise(one_sample_group_mean=True, tfce=True, mask=MNI_template, output_type='NIFTI_GZ'), name="randomise_flirt")
randomise_fnirt = Node(fsl.Randomise(one_sample_group_mean=True, tfce=True, mask=MNI_template, output_type='NIFTI_GZ'), name="randomise_fnirt")

datasink = Node(DataSink(base_directory=datasink_dir), name="sinker")

# datafinder = DataFinder()
# datafinder.inputs.root_paths = feat_dir
# datafinder.inputs.match_regex = r'.+/(?P<series_dir>.+(qT1|ep2d_fid_T1).+)/(?P<basename>.+)\.nii.gz'
# result = datafinder.run() 
# result.outputs.out_paths  

# SelectFiles (like DataGrabber++) OR DataFinder (Python regex)
# - SelectFiles: define paths beforehand and format variables into the path where things change
# - DataFinder: more flexible
# Iterate through subjects, runs, zfstats
# for each zfstat, register (flirt) to MNI space
# For randomise:
#   - 2nd-level analysis (across runs within subject), 
#   make 4D fMRI image for each cope across runs
#   - Higher-level analysis (across subjects), 
#   make 4D fMRI image for each cope across subjects
randomise_workflow = Workflow("randomise", working_dir)

"""
Instead of using iterables, setup connections manually and precompute all existing files
Each file must run through FLIRT and FNIRT respectively (using the `templates` variable)

Then, merge all FLIRT and FNIRT files respectively for each contrast, run, and session, grouped by subject
Example: For contrast 1, run 1, session baselineYear1Arm1, group all FLIRT files for each subject
        and merge them into a 4D image, sorted by subject id. Do the same for FNIRT files.
        
Then, run randomise on the merged FLIRT and FNIRT files respectively.
"""

# Create flirt and fnirt nodes
flirt_node_dict = {}
fnirt_node_dict = {}

for task in task_list:
    for contrast in contrast_list:
        for session in session_list:
            for subject_id in subject_id_list:
                for run in run_list:
                    zfstat_file = templates['zfstat'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    xfm_file = templates['xfm'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    zfstat_nonlinear_file = templates['zfstat_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)
                    xfm_nonlinear_file = templates['xfm_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session)                                        
                    
                    if zfstat_file in existing_files:
                        zfstat_path = opj(base_feat_dir, zfstat_file)
                        xfm_path = opj(base_feat_dir, xfm_file)
                        zfstat_nonlinear_path = opj(base_feat_dir, zfstat_nonlinear_file)
                        xfm_nonlinear_path = opj(base_feat_dir, xfm_nonlinear_file)
                        
                        key = get_unique_key(subject_id, run, task, contrast, session)
                        
                        flirt_name = f"flirt_{key}"
                        flirt = Node(fsl.FLIRT(reference=MNI_template, apply_xfm=True, padding_size=0, interp="trilinear", output_type='NIFTI_GZ'), name=flirt_name)

                        fnirt_name = f"fnirt_{key}"
                        fnirt = Node(fsl.FNIRT(ref_file=MNI_template, output_type='NIFTI_GZ'), name=fnirt_name)
                        
                        # FLIRT
                        flirt.inputs.in_file = zfstat_path
                        flirt.inputs.in_matrix_file = xfm_path                                                
                        
                        # FNIRT
                        fnirt.inputs.in_file = zfstat_nonlinear_path
                        fnirt.inputs.affine_file = xfm_nonlinear_path                                       
                        
                        flirt_node_dict[key] = flirt
                        fnirt_node_dict[key] = fnirt

subject_groups_dict = {}


# Create + connect to merge nodes
merge_flirt_dict = {}
merge_fnirt_dict = {}

for contrast in contrast_list:
    for session in session_list:
        for subject_id in subject_id_list:
            flirt_files = []
            fnirt_files = []
            for run in run_list:
                for task in task_list:
                    key = get_key(subject_id, run, task, contrast, session)
                    if key in flirt_node_dict:
                        flirt_files.append(flirt_node_dict[key].outputs.out_file)
                        fnirt_files.append(fnirt_node_dict[key].outputs.out_file)
            
            merge_flirt_name = f"merge_flirt_{subject_id}_{contrast}_{session}"
            merge_flirt = Node(fsl.Merge(dimension='t'), name=merge_flirt_name)
            merge_flirt.inputs.in_files = flirt_files
            
            merge_fnirt_name = f"merge_fnirt_{subject_id}_{contrast}_{session}"
            merge_fnirt = Node(fsl.Merge(dimension='t'), name=merge_fnirt_name)
            merge_fnirt.inputs.in_files = fnirt_files
            
            merge_flirt_dict[f"{subject_id}_{contrast}_{session}"] = merge_flirt
            merge_fnirt_dict[f"{subject_id}_{contrast}_{session}"] = merge_fnirt
                        
                        
                        

randomise_workflow.write_graph(graph2use="colored", format="png", simple_form=True)
# randomise_workflow.write_graph(graph2use="exec", dotfilename="exec_graph.dot", format="png")

randomise_workflow.config["execution"]["crashdump_dir"] = opj(randomise_workflow.config["execution"]["crashdump_dir"], working_dir, "crash")

# print(randomise_workflow.config["execution"])

logger.info("Workflow graph written to %s" % randomise_workflow.base_dir)

answer = input("Run workflow? (y/n)")
if not (answer == 'y' or answer == 'Y'):
    print("Exiting")
    exit()


# run = randomise_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 4})
run = randomise_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 32})