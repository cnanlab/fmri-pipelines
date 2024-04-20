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

infosource = Node(IdentityInterface(fields=['subject_id', 'task_name', 'run', 'contrast_id']),
                  name="infosource")
infosource.iterables = [('subject_id', subject_id_list),
                        ('task_name', task_list),
                        ('run', run_list),
                        ('contrast_id', contrast_list)]

contrast_info_source = Node(IdentityInterface(fields=['contrast_id']), name="contrast_info_source")
contrast_info_source.iterables = [('contrast_id', contrast_list)]

run_node = Node(IdentityInterface(fields=['run', 'contrast_id']), name="run_node")
run_node.iterables = [('run', run_list)]

task_node = Node(IdentityInterface(fields=['task_name', 'contrast_id', 'run']), name="task_node")
task_node.iterables = [('task_name', task_list)]

session_node = Node(IdentityInterface(fields=['session_name', 'task_name', 'contrast_id', 'run']), name="session_node")
session_node.iterables = [('session_name', session_list)]

subject_node = Node(IdentityInterface(fields=['subject_id', 'task_name', 'contrast_id', 'run', 'session_name']), name="subject_node")
subject_node.iterables = [('subject_id', subject_id_list)]

# subject_and_task_node = Node(IdentityInterface(fields=['subject_id', 'task_name', 'contrast_id', 'run']), name="subject_and_task_node")
# subject_and_task_node.iterables = [('subject_id', subject_id_list),
#                                    ('task_name', task_list)]

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
                    all_possible_files.append(templates['zfstat'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session))
                    all_possible_files.append(templates['xfm'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session))
                    all_possible_files.append(templates['zfstat_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session))
                    all_possible_files.append(templates['xfm_nonlinear'].format(subject_id=subject_id, run=run, task_name=task, contrast_id=contrast, session_name=session))

print(f"There are {len(all_possible_files)} possible files")

existing_files = util.return_existing_files(all_possible_files)

selectfiles = Node(SelectFiles(templates,
                               base_directory=base_feat_dir,
                               sort_filelist=True,
                               raise_on_empty=False),
                   name="selectfiles")

MNI_template = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

# in_file + in_matrix_file set in workflow.connect(), as they are determined at runtime from SelectFiles
flirt = MapNode(fsl.FLIRT(reference=MNI_template, apply_xfm=True, padding_size=0, interp="trilinear", output_type='NIFTI_GZ'), name="flirt", iterfield=['in_file'])

fnirt = MapNode(fsl.FNIRT(ref_file=MNI_template, output_type='NIFTI_GZ'), name="fnirt", iterfield=['in_file'])

# # outputs all files from flirt's to 'join' field
def flatten_and_sort(**kwargs):    
    import logging
    
    logger = logging.getLogger('nipype.workflow')  
    double_wrapped_file_names = list(kwargs.values()) # [[[file1], [file2]]]
    wrapped_file_names = double_wrapped_file_names[0] # each file name is 'wrapped' in array, ex: [['file1'], ['file2]]    
    logger.info(double_wrapped_file_names)
    logger.info(len(double_wrapped_file_names))
    logger.info(wrapped_file_names)
    logger.info(len(wrapped_file_names))
    
    sorted_file_names = sorted([wrapped_file_name[0] for wrapped_file_name in wrapped_file_names])    
    logger.info("SORTED FILE NAMES")
    logger.info(sorted_file_names)
    return sorted_file_names


join_flirt = JoinNode(Function(input_names=["join_in"], output_names="join_out", function=flatten_and_sort),
                joinsource="subject_node", # join on subject_id, as we want to group by subject
                joinfield="join_in",              
                name="join_flirt")

join_fnirt = JoinNode(Function(input_names=["join_in"], output_names="join_out", function=flatten_and_sort),
                joinsource="subject_node", # join on subject_id, as we want to group by subject
                joinfield="join_in",
                name="join_fnirt")

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
# randomise_workflow.connect([(infosource, selectfiles, [('subject_id', 'subject_id'),
#                                                        ('task_name', 'task_name'),
#                                                        ('run', 'run'),
#                                                        ('contrast_id', 'contrast_id')]),
#                             (selectfiles, flirt, [('zfstat', 'in_file'),
#                                                   ('xfm', 'in_matrix_file')]),
#                             (flirt, join, [('out_file', 'join_in')]),
#                             (join, merge, [('join_out', 'in_files')]),
#                             (merge, randomise, [('merged_file', 'in_file')]),
#                             (randomise, datasink, [("tstat_files", "randomise@tstat_files"),])])

# using contrast_id as initial source
# randomise_workflow.connect([(contrast_info_source, run_node, [('contrast_id', 'contrast_id')]),
#                             (run_node, task_node, [('run', 'run'), ('contrast_id', 'contrast_id')]),
#                             (task_node, session_node, [('task_name', 'task_name'), 
#                                                        ('contrast_id', 'contrast_id'), 
#                                                        ('run', 'run')]),
#                             (session_node, subject_node, [('session_name', 'session_name'), 
#                                                           ('task_name', 'task_name'), 
#                                                           ('contrast_id', 'contrast_id'), 
#                                                           ('run', 'run')]),                            
#                             (subject_node, selectfiles, [('subject_id', 'subject_id'), 
#                                                          ('session_name', 'session_name'),
#                                                          ('task_name', 'task_name'), 
#                                                          ('contrast_id', 'contrast_id'), 
#                                                          ('run', 'run')]),
#                             (selectfiles, flirt, [('zfstat', 'in_file'), ('xfm', 'in_matrix_file')]),
#                             (selectfiles, fnirt, [('zfstat_nonlinear', 'in_file'), ('xfm_nonlinear', 'affine_file')]),                            
#                             (flirt, join_flirt, [('out_file', 'join_in')]),   
#                             (flirt, datasink, [('out_file', 'flirt')]),                         
#                             (fnirt, join_fnirt, [('warped_file', 'join_in')]),
#                             (fnirt, datasink, [('warped_file', 'fnirt')]),
#                             (join_flirt, merge_flirt, [('join_out', 'in_files')]),
#                             (join_fnirt, merge_fnirt, [('join_out', 'in_files')]),
#                             (merge_flirt, randomise_flirt, [('merged_file', 'in_file')]),
#                             (merge_fnirt, randomise_fnirt, [('merged_file', 'in_file')]),
#                             (randomise_flirt, datasink, [("tstat_files", "randomise@flirt"),
#                                                          ("t_corrected_p_files", "randomise@flirt")
#                                                          ("t_p_files", "randomise@flirt")]),                                                    
#                             (randomise_fnirt, datasink, [("tstat_files", "randomise@fnirt")
#                                                          ("t_corrected_p_files", "randomise@fnirt")
#                                                          ("t_p_files", "randomise@fnirt")])
#                             ])

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