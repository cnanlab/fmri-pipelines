import time
import os
from os.path import join as opj
import json
import re
from nipype.interfaces.spm import Level1Design, EstimateModel, EstimateContrast
from nipype.algorithms.modelgen import SpecifySPMModel
from nipype.interfaces.utility import Function, IdentityInterface
import nipype.interfaces.fsl as fsl
from nipype.interfaces.io import SelectFiles, DataSink
from nipype import Workflow, Node, MapNode
from nipype.pipeline.engine import JoinNode
import util

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

# list of subject identifiers
# subject_id_list = ['NDARINV00BD7VDC', 'NDARINV00CY2MDM', 'NDARINV00HEV6HB', 'NDARINV00LH735Y', 'NDARINV00R4TXET']
print("FEAT preprocessing pipeline")

PREPROCESS_DIR = os.path.dirname(os.path.realpath(__file__))

PIPELINE_BASE_DIR = os.path.dirname(PREPROCESS_DIR)

print("pipeline base dir:", PIPELINE_BASE_DIR)

# base_design_fsf = input("Please enter the full path to the desired base design.fsf file:")
# base_design_fsf = "/mnt/storage/SST/sub-NDARINVZT44Y065/ses-baselineYear1Arm1/func/test_based_off_ritesh.feat/design.fsf"

# base design fsf that is modified for each subject
base_design_fsf = opj(PREPROCESS_DIR, "base_design_ritesh.fsf")
    
# base_subjects_dir = input("Please enter the base directory containing all of the subjects:")
BASE_SUBJECTS_DIR = "/mnt/storage/SST/" 

# subject_directory_names = [name for name in os.listdir(base_subjects_dir) if name.startswith("sub-")]
# extract 'sub-' prefix from 'sub-{subj_id}'
# subject_id_list = [re.sub(r'^sub-', '', dir_name) for dir_name in subject_directory_names]
# Only for test subjects right now

# The subject ids that are used within the preprocessing pipeline
subject_id_list = []

original_fifty_subjects_path = opj(PIPELINE_BASE_DIR, "subjects", "subject_same_mri.txt")

with open(original_fifty_subjects_path, "r") as file:
    subject_id_list = [name.strip() for name in file.readlines()]
    print(f"loaded {len(subject_id_list)} subjects from {original_fifty_subjects_path}")

anx_test_subjects_path = opj(PIPELINE_BASE_DIR, "subjects", "pilot_anx_subjects.txt")

with open(anx_test_subjects_path, "r") as file:
    anx_subject_ids = [name.strip() for name in file.readlines()]        
    print(f"loaded {len(anx_subject_ids)} subjects from {anx_test_subjects_path}")
    
    # only append unique subjects
    for subj_id in anx_subject_ids:
        if subj_id not in subject_id_list:
            subject_id_list.append(subj_id)

all_subjects_path = opj(PIPELINE_BASE_DIR, "subjects", "all_subj_ids.txt")

# add 150 more random subjects not in previous 2 groups
n_added = 0
with open(all_subjects_path, "r") as file:
    all_subject_ids = [name.strip() for name in file.readlines()]
    print(f"loaded {len(all_subject_ids)} subjects from {all_subjects_path}")
    
    # only append unique subjects
    for subj_id in all_subject_ids:
        if subj_id not in subject_id_list:
            subject_id_list.append(subj_id)
            n_added += 1
            if n_added >= 150:
                break

# subject_id_list = subject_id_list[:2]

print("subject id list", subject_id_list)
print("total number of unique subjects:", len(subject_id_list))
# print(subject_id_list)

# subject_id_list = ['NDARINV00BD7VDC', 'NDARINV00CY2MDM']
# print(subject_id_list)

# TR of functional images
# task_json_path = '/mnt/Storage/temp1/sub-NDARINV00BD7VDC/ses-baselineYear1Arm1/func/sub-NDARINV00BD7VDC_ses-baselineYear1Arm1_task-sst_run-01_bold.json'
# with open(task_json_path, 'rt') as fp:
#     task_info = json.load(fp)
# TR = task_info['RepetitionTime']

# TODO: remove hardcoding
TR = 0.8
print("TR:", TR)

# Smoothing widths used during preprocessing
# fwhm_list = [5]
run_list = [1, 2]
print("run list", run_list)
task_list = ["sst"]
print("task list", task_list)
# session_list = ["baselineYear1Arm1", "2YearFollowUpYArm1", "4YearFollowUpYArm1"]
session_list = ["baselineYear1Arm1"]
print("session list", session_list)

experiment_dir = BASE_SUBJECTS_DIR
# datasink_dir = opj(PREPROCESS_DIR, "datasink")

# output directory path
datasink_dir_base = "/mnt/storage/daniel/feat-preprocess-datasink"

if "--name" in os.sys.argv:
    name = os.sys.argv[os.sys.argv.index("--name") + 1]
    datasink_dir = f"{datasink_dir_base}/{name}"
else:
    date_string = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    datasink_dir = f"{datasink_dir_base}/{date_string}" 
# datasink_dir = f"/mnt/storage/daniel/feat-preprocess-datasink/{date_string}"


# make sure datasink directory exists
if not os.path.exists(datasink_dir):
    os.makedirs(datasink_dir)

print("datasink dir:", datasink_dir)

working_dir = opj(PREPROCESS_DIR,  "workingdir")

# preprocess base design.fsf file
with open(base_design_fsf, "r") as file:
    content = file.read()
    
    # make sure all subject paths have the correct prefix path (base_subjects_dir)    
    content = re.sub(f'"(.+?)sub', '"' + os.path.join(BASE_SUBJECTS_DIR, "sub"), content)   
    
    # set placeholder FEAT output directory path
    placeholder_feat_dir_path = os.path.join(datasink_dir, f'sub-PLACEHOLDER_ses-PLACEHOLDER_task-sst_run-00LN')                
    
    # set output directory to be in the working directory plus placeholder: subject id + session + task name + run number
    content = re.sub(r"set fmri\(outputdir\) \"(.+?)\"", # match everything between 'set fmri(outputdir) "' and '"'
                          f"set fmri(outputdir) \"{placeholder_feat_dir_path}\"", # replace with new output path
                          content)

new_base_design_fsf = os.path.join(os.getcwd(), working_dir, "base_design.fsf")
with open(new_base_design_fsf, "w+") as file:
    file.write(content)

print("new design.fsf file:", new_base_design_fsf)

# create a new design.fsf file for each subject, task, run, and session
def create_design_fsf(subject_id: str, task: str, session: str, run: int, base_design_fsf: str, is_nonlinear: bool, datasink_dir: bool):
    import os # dynamic imports required because nipype Function's execute in their own context
    import re
    
    with open(base_design_fsf, "r") as file:
        file_content = file.read()  
    
    subj_regex = r"sub-([^_/]+)" # match 'sub-' and any non-delimter characters ('_' or '/')
    run_regex = r"run-([\d]+)"    # 'run-' and any digits
    task_regex = r"task-([^_]+)" # 'task-' and any non-delimter characters ('_' or '/')
    session_regex = r"ses-([^_/]+)" # 'ses-' and any non-delimter characters ('_' or '/')
    
    # replace 'sub-' with actual subject id
    file_content = re.sub(subj_regex, f"sub-{subject_id}", file_content)            
    
    # replace 'run-' with actual run number
    file_content = re.sub(run_regex, f"run-{run:02d}", file_content)  
        
    # replace 'task-' with actual task name
    file_content = re.sub(task_regex, f"task-{task}", file_content)    
    
    # replace 'ses-' with actual session name
    file_content = re.sub(session_regex, f"ses-{session}", file_content)          
    
    highres_file_regex = r"set highres_files(.*)\"(.*)\""
    
    # there is only run-01 for T1w images, so we need to replace run-02 with run-01
    current_brain_path = re.search(highres_file_regex, file_content).group(2)
    
    if "run-02" in current_brain_path:
        file_content = re.sub(highres_file_regex, f"set highres_files(1) \"{current_brain_path.replace('run-02', 'run-01')}\"", file_content)            
        
    if is_nonlinear:        
        # set fmri(regstandard_nonlinear_yn) 0     <- set to 1
        nonlinear_regex = r"set fmri\(regstandard_nonlinear_yn\) (\d+)"
        file_content = re.sub(nonlinear_regex, "set fmri(regstandard_nonlinear_yn) 1", file_content)                
        
        # change output directory to include _NL
        new_output_feat_dir_path = os.path.join(datasink_dir, f'sub-{subject_id}_ses-{session}_task-{task}_run-{run:02d}NL')
        file_content = re.sub(r"set fmri\(outputdir\) \"(.+?)\"", # match everything between 'set fmri(outputdir) "' and '"'        
                              f"set fmri(outputdir) \"{new_output_feat_dir_path}\"", # replace with new output path
                              file_content)
        
    # create design FSF file for use by feat_node (NL = nonlinear if is_nonlinear is True)
    new_design_fsf = f"sub-{subject_id}_ses-{session}_task-{task}_run-{run:02d}_design{'_NL' if is_nonlinear else ''}.fsf"            
    
    with open(new_design_fsf, "w") as file:
        file.write(file_content)
        
    return os.path.join(os.getcwd(), new_design_fsf)

def create_BET_paths(base_subjects_dir: str, subject_id: str, session: str, run: int):
    # dynamic imports because nipype executes functions in separate context
    from os.path import join as opj        
    
    paths_dict = {
        "in_file": opj(base_subjects_dir, f"sub-{subject_id}", f"ses-{session}", "anat", f"sub-{subject_id}_ses-{session}_run-{run:02d}_T1w.nii"),
        "out_file": opj(base_subjects_dir, f"sub-{subject_id}", f"ses-{session}", "anat", f"sub-{subject_id}_ses-{session}_run-{run:02d}_T1w_brain.nii")
    }
    return paths_dict["in_file"], paths_dict["out_file"]

# # test create_design_fsf function    
# print()
# print("Testing create_design_fsf function...")
# print("with: subject_id=NDARINV00BD7VDC, task=sst, session=baselineYear1Arm1, run=1, base_design_fsf=", base_design_fsf)
# print(create_design_fsf("NDARINV00BD7VDC", "sst", "baselineYear1Arm1", 1, base_design_fsf))
# print()

infosource = Node(IdentityInterface(fields=['subject_id', 'task', 'run', 'session']),
                  name="infosource")
infosource.iterables = [("subject_id", subject_id_list),
                        ('task', task_list),
                        ('run', run_list),
                        ('session', session_list)]

create_BET_paths_node = Node(Function(input_names=["base_subjects_dir", "subject_id", "session", "run"], output_names=["in_file", "out_file"], function=create_BET_paths), name="create_BET_paths_node")
create_BET_paths_node.inputs.base_subjects_dir = BASE_SUBJECTS_DIR
create_BET_paths_node.inputs.run = 1 # only run-01 for T1w images

# bet_node = Node(fsl.BET(frac=0.5, vertical_gradient=0), name="bet_node")

def wrapped_bet_node_func(in_file, out_file):
    import nipype.interfaces.fsl as fsl
    import os
    
    # # TODO: make more permanent fix
    # # replace run number with 01 in in_file
    # in_file = in_file.replace("run-02", "run-01")
    
    if not os.path.exists(in_file):
        print(f"File {in_file} does not exist")
        raise FileNotFoundError(f"File {in_file} does not exist")
    
    if os.path.exists(out_file):
        print(f"File {out_file} already exists")
        return "success"
    
    bet = fsl.BET(frac=0.5, vertical_gradient=0)
    bet.inputs.in_file = in_file
    bet.inputs.out_file = out_file
    
    bet.run()    
    
    return "success"

wrapped_bet_node = Node(Function(input_names=["in_file", "out_file"], output_names="out", function=wrapped_bet_node_func), name="wrapped_bet_node")

# bet <anat> <output> -f <fractional intensity threshold> -g <vertical gradient>

if "--offset-timing-files" in os.sys.argv:
    custom_timing_files_node = Node(Function(input_names=["base_subjects_path", "subject_id", "session", "run"], output_names="out_files", function=util.create_custom_timing_files_sst_offset), name="custom_timing_files_node")
    custom_timing_files_node.inputs.base_subjects_path = BASE_SUBJECTS_DIR
    print("INFO: Using offset timing files")
else: 
    custom_timing_files_node = Node(Function(input_names=["base_subjects_path", "subject_id", "session", "run"], output_names="out_files", function=util.create_custom_timing_files_sst), name="custom_timing_files_node")
    custom_timing_files_node.inputs.base_subjects_path = BASE_SUBJECTS_DIR

def wait_node_func(subject_id, task, run, session, custom_timing_files_node_out, bet_node_out):
    return subject_id, task, run, session

# wait_node = Node(IdentityInterface(fields=["subject_id", "task", "session", "run", "custom_timing_files_node_out", "bet_node_out"]), name="wait_node")
wait_node = Node(Function(input_names=["subject_id", "task", "run", "session", "custom_timing_files_node_out", "bet_node_out"], output_names=["subject_id", "task", "run", "session"], function=wait_node_func), name="wait_node")

nonlinear_iter_node = Node(IdentityInterface(fields=["is_nonlinear"]), name="nonlinear_iter_node")
nonlinear_iter_node.iterables = [("is_nonlinear", [False, True])]

create_design_fsf_node = Node(Function(input_names=["subject_id", "task", "run", "session", "base_design_fsf", "is_nonlinear", "datasink_dir"], output_names="out_design_fsf", function=create_design_fsf, name="test"), name="create_design_fsf_node")
# these inputs are here because function doesn't see global context
create_design_fsf_node.inputs.base_design_fsf = new_base_design_fsf
create_design_fsf_node.inputs.datasink_dir = datasink_dir
    
feat_node = Node(fsl.FEAT(), name="feat_node")

preproc = Workflow("preproc_FEAT_workflow", working_dir)

datasink = Node(DataSink(base_directory=datasink_dir), name="sinker")

join_node = JoinNode(Function(input_names=["in_files"], output_names="out_files", function=lambda in_files: in_files), name="join_node", joinsource="infosource")

# note, datasink is manually set as output_dir in OG base_design_fsf file, so no
# need to connect feat_node to datasink for now
preproc.connect([(infosource, create_BET_paths_node, [('subject_id', 'subject_id'),
                                            # ('run', 'run'), # only run-01 for T1w images
                                            ('session', 'session')]),                 
                 (infosource, custom_timing_files_node, [('subject_id', 'subject_id'),
                                                        ('session', 'session'),
                                                        ('run', 'run')]),
                 (infosource, wait_node, [('subject_id', 'subject_id'),                                                        
                                                        ('run', 'run'),
                                                        ('session', 'session'),
                                                        ('task', 'task')]),
                 (create_BET_paths_node, wrapped_bet_node, [('in_file', 'in_file'),
                                                    ('out_file', 'out_file')]),
                 (wrapped_bet_node, wait_node, [('out', 'bet_node_out')]),                                  
                 (custom_timing_files_node, wait_node, [('out_files', 'custom_timing_files_node_out')]),                 
                 (wait_node, create_design_fsf_node, [('subject_id', 'subject_id'),
                                                        ('session', 'session'),
                                                        ('run', 'run'),
                                                        ('task', 'task')]),        
                 (nonlinear_iter_node, create_design_fsf_node, [('is_nonlinear', 'is_nonlinear')]),         
                 (create_design_fsf_node, feat_node, [('out_design_fsf', 'fsf_file')]),
                #  (feat_node, join_node, [('feat_dir', 'in_files')]),
                #  (feat_node, datasink, [('feat_dir', 'preproc')]),
                #  (feat_node, datasink, [('feat_dir', 'preproc.')]
                 ])

# set crash directory
preproc.config["execution"]["crashdump_dir"] = opj(preproc.config["execution"]["crashdump_dir"], working_dir, "crash")

if "--exec-graph" in os.sys.argv:
    preproc.write_graph(graph2use="exec", dotfilename="exec_graph.dot", format="png")
preproc.write_graph(graph2use="colored", format="png")


# if '-y' argument is passed, run the workflow without asking for confirmation
if "-y" in os.sys.argv:
    s = "yes"
else:
    s = input("Would you like to run the workflow? (Y/n)")

if not (s.lower() == "yes" or s.lower() == "y"):
    print("Exiting...")
    exit(0)

# Record the start time
start_time = time.time()

# CPU(s):                  64
#   On-line CPU(s) list:   0-63
# Vendor ID:               AuthenticAMD
#   Model name:            AMD Ryzen Threadripper PRO 5975WX 32-Cores
#     CPU family:          25
#     Model:               8
#     Thread(s) per core:  2
#     Core(s) per socket:  32
#     Socket(s):           1
run = preproc.run(plugin="MultiProc", plugin_args={"n_procs": 60})

## testing
# run = preproc.run(plugin="MultiProc", plugin_args={"n_procs": 1})

# Record the end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time

print(f"The workflow took {execution_time} seconds to complete.")

# dg = nio.DataGrabber()

# df = nio.DataFinder()
# df.inputs.root_paths = '.'
# df.inputs.match_regex = r'.+/(?P<series_dir>.+(qT1|ep2d_fid_T1).+)/(?P<basename>.+)\.nii.gz'
# result = df.run() 
# result.outputs.out_paths  

