from pandas import DataFrame
import pandas as pd

def create_custom_timing_files_sst(base_subjects_path: str, subject_id: str, session: str, run: int):
    # dynamic imports because nipype executes functions in separate context
    
    from os.path import join as opj
    import pandas as pd
    import os
    
    subject_string = "sub-" + subject_id
    session_string = "ses-" + session
    run_string = f"run-{run:02d}"
    file_name = f"{subject_string}_{session_string}_task-sst_{run_string}_events.tsv"        
    
    func_path = opj(base_subjects_path, subject_string, session_string, "func")
    
    stimulus_names = ["corrGo", "incorrGo", "corrStop", "incorrStop"]
    trial_types = ["correct_go", "incorrect_go", "correct_stop", "incorrect_stop"]
    
    output_paths = [opj(func_path, f"{subject_string}_{session_string}_task-sst_{run_string}_{stimulus_name}.tsv") for stimulus_name in stimulus_names]        
    
    if all([os.path.exists(path) for path in output_paths]):
        print(f"Custom timing files for {subject_string} {session_string} {run_string} already exist")
        return output_paths
        
    events_tsv_path = opj(func_path, file_name)    
        
    if not os.path.exists(events_tsv_path):
        print(f"File {events_tsv_path} does not exist")
        raise FileNotFoundError(f"File {events_tsv_path} does not exist")
    
    events_tsv_df = pd.read_csv(events_tsv_path, sep="\t")
    
    # remove first row (dummy)
    events_tsv_df = events_tsv_df.iloc[1:]
    
    print(events_tsv_df.head())
    
    # set first onset to 0
    events_tsv_df.iat[0, 0] = 0            
        
    for i, (name, trial_type) in enumerate(zip(stimulus_names, trial_types)):        
        df = events_tsv_df[events_tsv_df["trial_type"] == trial_type]        
        
        # set all of third column to 1
        df.loc[:, "trial_type"] = 1        
        
        output_path = output_paths[i]
        
        df.to_csv(output_path, sep="\t", index=False, header=False)
        
    
    print(f"Created custom timing files (not normalized by first offset) for {subject_string} {session_string} {run_string}")
    return output_paths

def create_custom_timing_files_sst_offset(base_subjects_path: str, subject_id: str, session: str, run: int):
    # dynamic imports because nipype executes functions in separate context
    
    from os.path import join as opj
    import pandas as pd
    import os
    
    subject_string = "sub-" + subject_id
    session_string = "ses-" + session
    run_string = f"run-{run:02d}"
    file_name = f"{subject_string}_{session_string}_task-sst_{run_string}_events.tsv"        
    
    func_path = opj(base_subjects_path, subject_string, session_string, "func")
    
    stimulus_names = ["corrGo", "incorrGo", "corrStop", "incorrStop"]
    
    output_paths = [opj(func_path, f"{subject_string}_{session_string}_task-sst_{run_string}_{stimulus_name}.tsv") for stimulus_name in stimulus_names]        
    
    if all([os.path.exists(path) for path in output_paths]):
        print(f"Custom timing files for {subject_string} {session_string} {run_string} already exist")
        return output_paths
        
    events_tsv_path = opj(func_path, file_name)
    
        
    if not os.path.exists(events_tsv_path):
        print(f"File {events_tsv_path} does not exist")
        raise FileNotFoundError(f"File {events_tsv_path} does not exist")
    
    events_tsv_df = pd.read_csv(events_tsv_path, sep="\t")
    
    # remove first row (dummy)
    events_tsv_df = events_tsv_df.iloc[1:]
    
    # offset set all onsets by first onset time
    first_onset = events_tsv_df.iloc[0]["onset"]
    events_tsv_df["onset"] = round(events_tsv_df["onset"] - first_onset, 2)
    
    # corrGo at correct_go
    corrGo = events_tsv_df[events_tsv_df["trial_type"] == "correct_go"]
    
    # incorrGo at incorrect_go
    incorrGo = events_tsv_df[events_tsv_df["trial_type"] == "incorrect_go"]
    
    # corrStop at correct_stop
    corrStop = events_tsv_df[(events_tsv_df["trial_type"] == "correct_stop")]
    
    # incorrStop at incorrect_stop
    incorrStop = events_tsv_df[(events_tsv_df["trial_type"] == "incorrect_stop")]
    
    # set all of third column to 1
    corrGo.loc[:, "trial_type"] = 1
    incorrGo.loc[:, "trial_type"] = 1
    corrStop.loc[:, "trial_type"] = 1
    incorrStop.loc[:, "trial_type"] = 1        
    
    # save all to respective csvs
    for i, df in enumerate([corrGo, incorrGo, corrStop, incorrStop]):
        df.to_csv(output_paths[i], sep="\t", index=False, header=False)
    
    print(f"Created custom timing files for {subject_string} {session_string} {run_string}")
    
    return output_paths

if __name__ == "__main__":
    import os
    base_subjects_path = "/mnt/storage/SST"
    test_subject_id = "NDARINV003RTV85"
    test_session = "baselineYear1Arm1"  
    test_runs = [1, 2]
    
    # remove previous custom timing files
    for stimulus_name in ["corrGo", "incorrGo", "corrStop", "incorrStop"]:
        for run in test_runs:
            path = f"{base_subjects_path}/sub-{test_subject_id}/ses-{test_session}/func/sub-{test_subject_id}_ses-{test_session}_task-sst_run-{run:02d}_{stimulus_name}.tsv"
            if os.path.exists(path):
                os.remove(path)
    print("Removed previous custom timing files")
    
    print("Original events.tsv run 1")
    df = pd.read_csv(f"{base_subjects_path}/sub-{test_subject_id}/ses-{test_session}/func/sub-{test_subject_id}_ses-{test_session}_task-sst_run-01_events.tsv", sep="\t")
    print(df.head())
    print()
    
    print("Original events.tsv run 2")
    df = pd.read_csv(f"{base_subjects_path}/sub-{test_subject_id}/ses-{test_session}/func/sub-{test_subject_id}_ses-{test_session}_task-sst_run-02_events.tsv", sep="\t")
    print(df.head())
    print()
    
    print("Testing create_custom_timing_files_sst")
    output_paths = create_custom_timing_files_sst(base_subjects_path, test_subject_id, test_session, test_runs[0])
    df = pd.read_csv(output_paths[0], sep="\t", header=None)
    print("corrGo")
    print(df.head())
    print()
    
    print("Testing create_custom_timing_files_sst_offset")
    output_paths = create_custom_timing_files_sst_offset(base_subjects_path, test_subject_id, test_session, test_runs[1])
    df = pd.read_csv(output_paths[0], sep="\t", header=None)
    print("corrGo")
    print(df.head())
    print()