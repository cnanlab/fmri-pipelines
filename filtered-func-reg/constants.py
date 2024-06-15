import os

##############
# Constants
##############
FEAT_BASE_DIR = "/mnt/storage/daniel/feat-preprocess-datasink/additional_150_subjs"

MNI_TEMPLATE = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz' # for FLIRT

MNI_TEMPLATE_SKULL = '/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz' # for FNIRT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKING_DIR = os.path.join(BASE_DIR, "workingdir")