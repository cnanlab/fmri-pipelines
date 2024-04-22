import os
from os.path import join as opj
from dotenv import load_dotenv

load_dotenv()

# check if the server is the lab server, we have to use different paths
IS_LAB_SERVER = os.getenv("IS_LAB_SERVER") == "True"

# absolute path to the roi directory (this file's directory)
ROI_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# absolute path to the pipeline base directory (root directory of git repository)
PIPELINE_BASE_DIR = os.path.dirname(ROI_BASE_DIR)

WORKING_DIR_NAME = "workingdir"

WORKING_DIR = opj(ROI_BASE_DIR, WORKING_DIR_NAME)

MNI_TEMPLATE = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

INPUT_FEAT_DATASINK = "/mnt/storage/daniel/feat-preprocess-datasink/" if not IS_LAB_SERVER else "/home/danielsuh/mountdir/daniel/feat-preprocess-datasink"

MASK_FILE_PATH = opj(ROI_BASE_DIR, "grantmask_labeled.nii")
