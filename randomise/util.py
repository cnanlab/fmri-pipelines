import re
import os

def return_existing_files(files):    
    """
    Return a list of files that exist on the file system
    """
    existing_files = []
    for file in files:
        if os.path.exists(file):
            existing_files.append(file)
    return existing_files

def get_subject_from_feat_dirname(feat_dirname) -> str:
    # using regex
    expression = r"sub-([^_/]+)"
    search = re.search(expression, feat_dirname)
    # print(search)
    return search.group(1)

def get_session_from_feat_dirname(feat_dirname) -> str:
    # using regex
    expression = r"ses-([^_/]+)"
    return re.search(expression, feat_dirname).group(1)

def get_task_from_feat_dirname(feat_dirname) -> str:
    # using regex
    expression = r"task-([^_/]+)"
    return re.search(expression, feat_dirname).group(1)

def get_run_from_feat_dirname(feat_dirname) -> int:
    # using regex
    expression = r"run-(\d+)"
    return int(re.search(expression, feat_dirname).group(1))


if __name__ == "__main__":
    feat_dirname = "sub-NDARINVZMMCVRWG_ses-2YearFollowUpYArm1_task-sst_run-01LN.feat"
    print(feat_dirname)
    print(get_subject_from_feat_dirname(feat_dirname))
    print(get_session_from_feat_dirname(feat_dirname))
    print(get_task_from_feat_dirname(feat_dirname))
    print(get_run_from_feat_dirname(feat_dirname))