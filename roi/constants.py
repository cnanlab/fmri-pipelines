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

MASK_FILE_PATH = opj(ROI_BASE_DIR, "grantmask_labeled.nii")

BASE_DATASINKS_DIR = "/mnt/storage/daniel/" if not IS_LAB_SERVER else "/home/danielsuh/mountdir/storage/daniel/"

# hardcoded timestamp for the input feat datasink
INPUT_FEAT_DATASINK = opj(BASE_DATASINKS_DIR, "feat-preprocess-datasink/2024-04-21_23-16-00")

ROI_DATASINK = opj(BASE_DATASINKS_DIR, "roi-datasink")
