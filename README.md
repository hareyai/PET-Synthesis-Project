# PET-Synthesis-Project
Masters project containing data pre-processing for the GAN synthesis of PET images from MRI scans for the purposes of Alzheimer's diagnostic, as an alternative to standard costly FDG-PET imaging.
Contains final most important files in the organizing and pre-processing of data for training, as well as additional presentation and report files.

Script included:
Text_to_CSV_ADNI_data_organization compiles all patient info from ADNI database, used to filter out data with missing labels, track distribution of patient data diversity.

Dicom_to_NIFTI used to convert organized ADNI data from individual Dicom files to zip NIFTI files.

Standardization_to_MNI_Space converts raw MRI data and partially preprocessed PET data to standard MNI space. Final output contains set of patient images oriented, normalized, and downsampled to same MNI space.

Next steps to be completed in project:
-Further process ASL images with FSL BASIL tool: subtractions and motion correction

-Incorporate additional UW Medical Center MRI and PET data into organizational and pre-processing pipeline

-Train GAN with final compilation of pre-processed data, tune hyperparameters of existing model architecture

-Explore trade-offs between dataset size and scan diversity

