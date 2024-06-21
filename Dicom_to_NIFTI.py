import os
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])


def copy_and_convert_folders(source_path, destination_path):
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
        logging.info(f"Created destination directory at {destination_path}")

    directories = sorted([d for d in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, d))])

    for dir_name in directories:
        src_path = os.path.join(source_path, dir_name)
        dst_path = os.path.join(destination_path, dir_name)
        if not os.path.exists(dst_path):
            shutil.copytree(src_path, dst_path)
            logging.info(f"Successfully copied {dir_name} from {src_path} to {dst_path}")
            convert_dicom_to_nifti(dst_path, dst_path)
        else:
            logging.info(f"Directory {dst_path} already exists, skipping copy.")


def convert_dicom_to_nifti(dicom_folder_path, output_folder_path):
    for root, dirs, files in os.walk(dicom_folder_path):
        dicom_files = [f for f in files if f.endswith('.dcm')]
        if dicom_files:
            nifti_filename = os.path.basename(root) + '.nii.gz'
            output_dir = os.path.join(output_folder_path, os.path.relpath(root, dicom_folder_path))
            os.makedirs(output_dir, exist_ok=True)
            nifti_path = os.path.join(output_dir, nifti_filename)

            if os.path.exists(nifti_path):
                logging.info(f"NIfTI file already exists at {nifti_path}, skipping conversion.")
                continue  # Skip conversion if NIfTI file already exists - if code pauses it can rerun from last unconverted file

            command = f'dcm2niix -z y -o {output_dir} -f {nifti_filename} {root}'
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.stderr:
                logging.error(f"Error converting directory {root}: {result.stderr}")
            else:
                logging.info(f"Converted DICOM directory {root} to NIfTI at {output_dir}/{nifti_filename}")
                # Delete DICOM files after conversion
                for dicom_file in dicom_files:
                    os.remove(os.path.join(root, dicom_file))
                logging.info(f"Deleted all DICOM files in {root}")


def main():
    source_directory = '/khayyam/projects/ADNI34_Proc_PET/combined_MRI_PET'
    destination_directory = '/khayyam/projects/ADNI34_Proc_PET/niftifiles'

    copy_and_convert_folders(source_directory, destination_directory)


if __name__ == "__main__":
    main()



