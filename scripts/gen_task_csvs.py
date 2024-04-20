from os.path import join as opj
import pandas as pd

base_subjects_path = "/mnt/storage/SST/"

with open("../subjects/test_anxiety_subjects.txt", "r") as file:
    subject_directory_names = ["sub-" + name.strip() for name in file.readlines()]

print(subject_directory_names)

def create_custom_timing_files_sst(subject_id: str, session_name: str, run: int):
    subject_string = "sub-" + subject_id
    session_string = "ses-" + session_name
    run_string = f"run-{run:02d}"
    file_name = f"{subject_string}_{session_string}_task-sst_{run_string}_events.tsv"
    
    func_path = opj(base_subjects_path, subject_string, session_string, "func")
    
    events_tsv_path = opj(func_path, file_name)
    
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
    for df, stimulus_name in zip([corrGo, incorrGo, corrStop, incorrStop], ["corrGo", "incorrGo", "corrStop", "incorrStop"]):        
        df.to_csv(opj(func_path, f"{subject_string}_{session_string}_task-sst_{run_string}_{stimulus_name}.tsv"), sep="\t", index=False, header=False)
    
    print(f"Created custom timing files for {subject_string} {session_string} {run_string}")
    
    return


if __name__ == "__main__":
    
    first_subject = subject_directory_names[0]

    first_subject_id = first_subject[4:]

    print(f"First subject: {first_subject_id}")

    events_tsv = opj(base_subjects_path, first_subject, "ses-baselineYear1Arm1", "func", first_subject + "_ses-baselineYear1Arm1_task-sst_run-01_events.tsv")

    # create corrGo.tsv, incorrGo.tsv, corrStop.tsv, incorrStop.tsv from events.tsv

    # remove first row (dummy)
    events_tsv_df = pd.read_csv(events_tsv, sep="\t")

    print("original events.tsv:")
    print(events_tsv_df.head())
    print()
    print("Unique trial types:")
    print(events_tsv_df["trial_type"].unique())

    create_custom_timing_files_sst(first_subject[4:], "baselineYear1Arm1", 1)

# # remove first row (dummy)
# events_tsv_df = events_tsv_df.iloc[1:]

# # offset set all onsets by first onset time
# first_onset = events_tsv_df.iloc[0]["onset"]

# events_tsv_df["onset"] = events_tsv_df["onset"] - first_onset

# print()
# print("offset events.tsv:")
# print(events_tsv_df.head())

# print()

# # corrGo at correct_go or correctlate_go
# # corrGo = events_tsv_df[(events_tsv_df["trial_type"] == "correct_go") | (events_tsv_df["trial_type"] == "correctlate_go")]
# corrGo = events_tsv_df[events_tsv_df["trial_type"] == "correct_go"]



# print("corrGo:")
# print(corrGo.head())

# # incorrGo = events_tsv_df[(events_tsv_df["trial_type"] == "incorrect_go") | (events_tsv_df["trial_type"] == "incorrectlate_go")]
# incorrGo = events_tsv_df[events_tsv_df["trial_type"] == "incorrect_go"]

# print("incorrGo:")
# print(incorrGo.head())

# corrStop = events_tsv_df[(events_tsv_df["trial_type"] == "correct_stop")]

# incorrStop = events_tsv_df[(events_tsv_df["trial_type"] == "incorrect_stop")]

# # set all of third column to 1
# corrGo["trial_type"] = 1
# incorrGo["trial_type"] = 1
# corrStop["trial_type"] = 1
# incorrStop["trial_type"] = 1