import os
from os.path import join as opj

ROI_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PIPELINE_BASE_DIR = os.path.dirname(ROI_BASE_DIR)

WORKING_DIR_NAME = "workingdir"

WORKING_DIR = opj(ROI_BASE_DIR, WORKING_DIR_NAME)

MNI_TEMPLATE = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

INPUT_FEAT_DATASINK = "/mnt/storage/daniel/feat-preprocess-datasink/"

MASK_FILE_PATH = opj(ROI_BASE_DIR, "grantmask_labeled.nii")
