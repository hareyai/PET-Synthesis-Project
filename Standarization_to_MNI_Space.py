import os
import subprocess


# NEED TO ADD ADDITIONAL PROCESSING TO ASL DATA
# ASL IS STILL IN 4D, USE FSL BASIL TOOL
# Raw ASL to be converted to CBF maps by subtracting control and labeled images

def get_fsldir():
    return os.getenv('FSLDIR')

def run_command(command, log_file):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            output_str = output.decode('utf-8')
            print(output_str, end='')  # Print to console
            log_file.write(output_str)  # To log file - use for analysis on conversion
    rc = process.poll()
    return rc


def process_t1(t1_path, output_dir, log_file):
    if os.path.exists(f"{output_dir}/T1_MNI.nii.gz"):
        log_file.write("T1_MNI.nii.gz already exists, skipping T1 processing.\n")
        print("T1_MNI.nii.gz already exists, skipping T1 processing.")
        return

    print(f"Starting T1 processing from {t1_path}")
    log_file.write(f"Starting T1 processing from {t1_path}\n")

    t1_anat_dir = f"{output_dir}/T1.anat"
    t1_biascorr_brain = f"{t1_anat_dir}/T1_biascorr_brain.nii.gz"

    if not os.path.exists(t1_anat_dir):
        print("Running fsl_anat for T1")
        log_file.write("Running fsl_anat for T1\n")
        run_command(f"fsl_anat -i {t1_path} -o {output_dir}/T1 --strongbias --nocrop --noseg --nosubcortseg --clobber", log_file)
    else:
        print("T1.anat directory already exists, skipping fsl_anat")
        log_file.write("T1.anat directory already exists, skipping fsl_anat\n")

    if not os.path.exists(t1_biascorr_brain):
        print("Missing T1_biascorr_brain.nii.gz, skipping T1 processing.")
        log_file.write("Missing T1_biascorr_brain.nii.gz, skipping T1 processing.\n")
        return

    if not os.path.exists(f"{output_dir}/T1_to_MNI.nii.gz"):
        print("Running flirt for T1 to MNI")
        log_file.write("Running flirt for T1 to MNI\n")
        run_command(f"flirt -in {t1_biascorr_brain} -ref {get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz -out {output_dir}/T1_to_MNI.nii.gz -omat {output_dir}/T1_to_MNI.mat -dof 12 -cost mutualinfo -v", log_file)

    if not os.path.exists(f"{output_dir}/T1_to_MNI.mat"):
        print("Missing T1_to_MNI.mat, skipping T1 processing.")
        log_file.write("Missing T1_to_MNI.mat, skipping T1 processing.\n")
        return

    if not os.path.exists(f"{output_dir}/T1_to_MNI_nonlin_field.nii.gz"):
        print("Running fnirt for T1 to MNI")
        log_file.write("Running fnirt for T1 to MNI\n")
        run_command(f"fnirt --in={t1_biascorr_brain} --ref={get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz --aff={output_dir}/T1_to_MNI.mat --cout={output_dir}/T1_to_MNI_nonlin_field -v", log_file)

    if not os.path.exists(f"{output_dir}/T1_to_MNI_nonlin_field.nii.gz"):
        print("Missing T1_to_MNI_nonlin_field.nii.gz, skipping T1 processing.")
        log_file.write("Missing T1_to_MNI_nonlin_field.nii.gz, skipping T1 processing.\n")
        return

    print("Running applywarp for T1 to MNI")
    log_file.write("Running applywarp for T1 to MNI\n")
    run_command(f"applywarp --ref={get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz --in={t1_biascorr_brain} --warp={output_dir}/T1_to_MNI_nonlin_field --out={output_dir}/T1_MNI -v", log_file)

    print("Finished T1 processing")
    log_file.write("Finished T1 processing\n")


def process_flair(flair_path, t1_output_dir, output_dir, log_file):
    if os.path.exists(f"{output_dir}/FLAIR_MNI.nii.gz"):
        log_file.write("FLAIR_MNI.nii.gz already exists, skipping FLAIR processing.\n")
        print("FLAIR_MNI.nii.gz already exists, skipping FLAIR processing.")
        return

    print(f"Starting FLAIR processing from {flair_path}")
    log_file.write(f"Starting FLAIR processing from {flair_path}\n")

    flair_anat_dir = f"{output_dir}/FLAIR.anat"
    flair_biascorr_brain = f"{flair_anat_dir}/T1_biascorr_brain.nii.gz"

    if not os.path.exists(flair_anat_dir):
        print("Running fsl_anat for FLAIR")
        log_file.write("Running fsl_anat for FLAIR\n")
        run_command(f"fsl_anat -i {flair_path} -o {output_dir}/FLAIR --strongbias --nocrop --noseg --nosubcortseg --clobber", log_file)
    else:
        print("FLAIR.anat directory already exists, skipping fsl_anat")
        log_file.write("FLAIR.anat directory already exists, skipping fsl_anat\n")

    if not os.path.exists(flair_biascorr_brain):
        print("Missing T1_biascorr_brain.nii.gz in FLAIR.anat directory, skipping FLAIR processing.")
        log_file.write("Missing T1_biascorr_brain.nii.gz in FLAIR.anat directory, skipping FLAIR processing.\n")
        return

    if not os.path.exists(f"{output_dir}/FLAIR_to_T1.mat"):
        print("Running flirt for FLAIR to T1")
        log_file.write("Running flirt for FLAIR to T1\n")
        run_command(f"flirt -ref {t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz -in {flair_biascorr_brain} -dof 6 -omat {output_dir}/FLAIR_to_T1.mat -v", log_file)

    if not os.path.exists(f"{output_dir}/FLAIR_to_T1.mat"):
        print("Missing FLAIR_to_T1.mat, skipping FLAIR processing.")
        log_file.write("Missing FLAIR_to_T1.mat, skipping FLAIR processing.\n")
        return

    if not os.path.exists(f"{output_dir}/FLAIR_T1.nii.gz"):
        print("Running applywarp for FLAIR to T1")
        log_file.write("Running applywarp for FLAIR to T1\n")
        run_command(f"applywarp --ref={t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz --in={flair_biascorr_brain} --premat={output_dir}/FLAIR_to_T1.mat --out={output_dir}/FLAIR_T1 -v", log_file)

    if not os.path.exists(f"{output_dir}/FLAIR_T1.nii.gz"):
        print("Missing FLAIR_T1.nii.gz, skipping FLAIR processing.")
        log_file.write("Missing FLAIR_T1.nii.gz, skipping FLAIR processing.\n")
        return

    print("Running applywarp for FLAIR to MNI")
    log_file.write("Running applywarp for FLAIR to MNI\n")
    run_command(f"applywarp --ref={get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz --in={output_dir}/FLAIR_T1 --warp={t1_output_dir}/T1_to_MNI_nonlin_field --out={output_dir}/FLAIR_MNI -v", log_file)

    if not os.path.exists(f"{output_dir}/FLAIR_MNI.nii.gz"):
        print("FLAIR_MNI.nii.gz was not created, there might be an issue.")
        log_file.write("FLAIR_MNI.nii.gz was not created, there might be an issue.\n")
        return

    print("Finished FLAIR processing")
    log_file.write("Finished FLAIR processing\n")

# Needs complete revision or separate script to redo/correct ASL conversion
def process_asl(asl_path, t1_output_dir, output_dir, log_file):
    if os.path.exists(f"{output_dir}/ASL_MNI.nii.gz"):
        log_file.write("ASL_MNI.nii.gz already exists, skipping ASL processing.\n")
        print("ASL_MNI.nii.gz already exists, skipping ASL processing.")
        return

    print(f"Starting ASL processing from {asl_path}")
    log_file.write(f"Starting ASL processing from {asl_path}\n")

    asl_to_t1_mat = f"{output_dir}/ASL_to_T1.mat"
    asl_t1 = f"{output_dir}/ASL_T1.nii.gz"

    if not os.path.exists(asl_to_t1_mat):
        print("Running flirt for ASL to T1")
        log_file.write("Running flirt for ASL to T1\n")
        run_command(f"flirt -ref {t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz -in {asl_path} -dof 6 -omat {asl_to_t1_mat} -v", log_file)

    if not os.path.exists(asl_to_t1_mat):
        print("Missing ASL_to_T1.mat, skipping ASL processing.")
        log_file.write("Missing ASL_to_T1.mat, skipping ASL processing.\n")
        return

    if not os.path.exists(asl_t1):
        print("Running applywarp for ASL to T1")
        log_file.write("Running applywarp for ASL to T1\n")
        run_command(f"applywarp --ref={t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz --in={asl_path} --premat={asl_to_t1_mat} --out={asl_t1} -v", log_file)

    if not os.path.exists(asl_t1):
        print("Missing ASL_T1.nii.gz, skipping ASL processing.")
        log_file.write("Missing ASL_T1.nii.gz, skipping ASL processing.\n")
        return

    print("Running applywarp for ASL to MNI")
    log_file.write("Running applywarp for ASL to MNI\n")
    run_command(f"applywarp --ref={get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz --in={asl_t1} --warp={t1_output_dir}/T1_to_MNI_nonlin_field --out={output_dir}/ASL_MNI -v", log_file)

    if not os.path.exists(f"{output_dir}/ASL_MNI.nii.gz"):
        print("ASL_MNI.nii.gz was not created, there might be an issue.")
        log_file.write("ASL_MNI.nii.gz was not created, there might be an issue.\n")
        return

    print("Finished ASL processing")
    log_file.write("Finished ASL processing\n")


def process_fdg_pet(fdg_pet_path, t1_output_dir, output_dir, log_file):
    if os.path.exists(f"{output_dir}/FDG_MNI.nii.gz"):
        log_file.write("FDG_MNI.nii.gz already exists, skipping FDG PET processing.\n")
        print("FDG_MNI.nii.gz already exists, skipping FDG PET processing.")
        return

    print(f"Starting FDG PET processing from {fdg_pet_path}")
    log_file.write(f"Starting FDG PET processing from {fdg_pet_path}\n")

    fdg_to_t1_mat = f"{output_dir}/FDG_to_T1.mat"
    fdg_t1 = f"{output_dir}/FDG_T1.nii.gz"

    if not os.path.exists(fdg_to_t1_mat):
        print("Running flirt for FDG PET to T1")
        log_file.write("Running flirt for FDG PET to T1\n")
        run_command(f"flirt -ref {t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz -in {fdg_pet_path} -dof 6 -omat {fdg_to_t1_mat} -v", log_file)

    if not os.path.exists(fdg_to_t1_mat):
        print("Missing FDG_to_T1.mat, skipping FDG PET processing.")
        log_file.write("Missing FDG_to_T1.mat, skipping FDG PET processing.\n")
        return

    if not os.path.exists(fdg_t1):
        print("Running applywarp for FDG PET to T1")
        log_file.write("Running applywarp for FDG PET to T1\n")
        run_command(f"applywarp --ref={t1_output_dir}/T1.anat/T1_biascorr_brain.nii.gz --in={fdg_pet_path} --premat={fdg_to_t1_mat} --out={fdg_t1} -v", log_file)

    if not os.path.exists(fdg_t1):
        print("Missing FDG_T1.nii.gz, skipping FDG PET processing.")
        log_file.write("Missing FDG_T1.nii.gz, skipping FDG PET processing.\n")
        return

    print("Running applywarp for FDG PET to MNI")
    log_file.write("Running applywarp for FDG PET to MNI\n")
    run_command(f"applywarp --ref={get_fsldir()}/data/standard/MNI152_T1_2mm_brain.nii.gz --in={fdg_t1} --warp={t1_output_dir}/T1_to_MNI_nonlin_field --out={output_dir}/FDG_MNI -v", log_file)

    if not os.path.exists(f"{output_dir}/FDG_MNI.nii.gz"):
        print("FDG_MNI.nii.gz was not created, there might be an issue.")
        log_file.write("FDG_MNI.nii.gz was not created, there might be an issue.\n")
        return

    print("Finished FDG PET processing")
    log_file.write("Finished FDG PET processing\n")


def find_file(folder, keywords, file_type):
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.nii.gz'):
                if any(keyword.lower() in root.lower() for keyword in keywords):
                    file_path = os.path.join(root, file)
                    print(f"Found {file_type} file: {file_path}")
                    return file_path
    print(f"No matching {file_type} file found in {folder}")
    return None


def main():
    # Base directory with organized patient folders
    base_dir = "/khayyam/projects/ADNI34_Proc_PET/testdatechecker2"

    # directory for final MNI Normalized images
    output_base_dir = "/khayyam/projects/ADNI34_Proc_PET/MNI_Normalization"

    # Check MNI_Normalization directory exists & recognized in server
    os.makedirs(output_base_dir, exist_ok=True)
    os.chmod(output_base_dir, 0o775)

    patient_folders = sorted(os.listdir(base_dir))

    # keywords for each file type
    t1_keywords = ["mprage", "t1", "IR-FSPGR"]
    flair_keywords = ["flair", "t2"]
    asl_keywords = ["asl", "pasl"]
    fdg_pet_keywords = ["coreg"]

    for patient_folder in patient_folders:
        patient_path = os.path.join(base_dir, patient_folder)

        t1_path = find_file(patient_path, t1_keywords, "T1")
        flair_path = find_file(patient_path, flair_keywords, "FLAIR")
        asl_path = find_file(patient_path, asl_keywords, "ASL")
        fdg_pet_path = find_file(patient_path, fdg_pet_keywords, "FDG PET")

        if not all([t1_path, flair_path, asl_path, fdg_pet_path]):
            print(f"Missing files for patient {patient_folder}, skipping.")
            continue

        # Output for normalized files
        output_dir = os.path.join(output_base_dir, patient_folder)
        os.makedirs(output_dir, exist_ok=True)

        # Log file for processing output, for further analysis on preprocessing
        log_file_path = os.path.join(output_dir, "processing_output.txt")
        with open(log_file_path, "a") as log_file:
            # Add a separator for each patient for ease of later analysis
            log_file.write(f"\n{'=' * 40}\nStarting processing for patient {patient_folder}\n{'=' * 40}\n")
            print(f"Starting processing for patient {patient_folder}")

            process_t1(t1_path, output_dir, log_file)
            process_flair(flair_path, output_dir, output_dir, log_file)
            process_asl(asl_path, output_dir, output_dir, log_file)
            process_fdg_pet(fdg_pet_path, output_dir, output_dir, log_file)

        # Print after finishing processing for each folder for confirmation
        print(f"Finished converting {patient_folder}")


if __name__ == "__main__":
    main()


