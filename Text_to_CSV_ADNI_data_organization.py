import pandas as pd
import re
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
    except IOError as e:
        logging.error(f"Error opening file: {e}")
        sys.exit(1)

    patient_sections = content.split('----------------------------------------\n')
    data = []

    for section in patient_sections:
        if section.strip():
            file_path = extract("File Path", section)
            parsed_data = parse_section(section, file_path)
            if parsed_data:
                logging.info(f"Processed patient ID: {parsed_data['Patient ID']}")
                data.append(parsed_data)

    return pd.DataFrame(data)


def extract(keyword, section):
    """
    Extracts information based on a keyword from a given section of text.

    Parameters:
    - keyword: The prefix that identifies the information to extract.
    - section: The text block from which to extract information.

    Returns:
    - The extracted information as a string, or an empty string if not found.
    """
    pattern = f"{keyword}: (.*)"
    match = re.search(pattern, section, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_radiopharmaceutical(section):

    unwanted_phrases = ["unspecified", "solution", "other", "neuraceq", "liquid solution", "neuroceq"]

    radiopharm_pattern = re.compile(r'Radiopharmaceutical \(\(0018, 0031\)\): (.+)', re.IGNORECASE)
    code_meaning_pattern = re.compile(r'\(0008, 0104\) Code Meaning\s+LO:\s+(.+)', re.IGNORECASE)

    # Search for Radiopharm pattern
    radiopharm_match = radiopharm_pattern.search(section)
    if radiopharm_match:
        radiopharm_name = radiopharm_match.group(1).strip(', ').lower()
        if all(phrase not in radiopharm_name for phrase in unwanted_phrases):
            return radiopharm_name.capitalize()

    code_meaning_match = code_meaning_pattern.search(section)
    if code_meaning_match:
        code_meaning = code_meaning_match.group(1).strip()
        return code_meaning.capitalize()

    return "No Radiopharm Data Extracted"


def determine_scan_type(section):
    if "non-pet file" in section.lower():
        return "MRI"
    else:
        return "PET"

def categorize_radiopharmaceutical(extracted_radiopharm):
    categories = {
        'Tau': ["tau", "18f-flortaucipir", "av1451", "t807", "thk", "pbb3 (18f)", "mk-6240", "ro948 (18f)", "pi-2620", "bc-pib", "av-1451", "1451", "av 1451"],
        'AB': ["amyloid", "amyvid", "florbetaben", "florbetapir", "flutemetamol", "pittsburgh compound-b", "nav4694", "gantenerumab", "av-45", "fbb", "av45", "flourbetaben", "F-18 florabetapir"],
        'FDG': ["fluorodeoxyglucose", "fdg", "2-deoxy-2-[18f]fluoro-d-glucose", "glucose analog", "radioglucose", "f-18 labeled glucose"]
    }

    categories = {category: [keyword.lower() for keyword in keywords] for category, keywords in categories.items()}

    extracted_radiopharm_lower = extracted_radiopharm.lower()
    for category, keywords in categories.items():
        if any(keyword in extracted_radiopharm_lower for keyword in keywords):
            return category

    return "Unknown"


def parse_section(section, file_path):
    scan_type = determine_scan_type(section)
    extracted_radiopharm = extract_radiopharmaceutical(section)
    radiopharm_category = categorize_radiopharmaceutical(extracted_radiopharm)

    # Initialize with default values
    mri_contrast_category = "--"

    if scan_type == "MRI":
        mri_contrast_category = categorize_mri_contrast(file_path)

    data = {
        "File Path": file_path,
        "Patient Subfolder": extract("Patient Subfolder", section),
        "Patient ID": extract("Patient ID", section),
        "Date Folder Index": extract("Date Folder Index", section),
        "Number of Scan Folders": extract("Number of Scan Folders", section),
        "Patient Age": extract("Patient Age", section),
        "Patient Sex": extract("Patient Sex", section),
        "Manufacturer": extract("Manufacturer", section),
        "Model Name": extract("Model Name", section),
        "Institution Name": extract("Institution Name", section),
        "Study Description": extract("Study Description", section),
        "Scan Type": scan_type,
        "Radiopharmaceutical": extracted_radiopharm if scan_type == "PET" else "--",
        "Radiopharm Category": radiopharm_category if scan_type == "PET" else "--",
        "MRI Contrast Category": mri_contrast_category
    }
    return data


def categorize_mri_contrast(file_path):
    patterns = {
        'T1': [r"_MPR_Collection_", r"AAHead_Scout_MPR", r"Accelerated_.*MPRAGE", r".*FSPGR.*", r".*MPRAGE.*",
               r".*T1.*", r"cor_mpr"],
        'T2_star': [r"Axial_3TE_T2_STAR", r"T2_STAR", r"Axial_T2_0_angle_Star", r".*T2_STAR.*"],
        'ASL': [r"\bASL\b"],
        '2D_ASL': [r"Axial_2D_PASL"],
        '3D_ASL': [r"Axial_3D_PASL", r".*pcasl.*"],
        'DTI': [r"\bDTI\b"],
        'rsfMRI': [r".*fcMRI.*", r".*MB_rsfMRI.*", r"rsfMRI", r"fMRI"],
        'FLAIR': [r"Axial_3D_FLAIR", r".*FLAIR.*"],
        'CBF': [r"Cerebral_Blood_Flow"],
        'HighResHippo': [r".*HighResHippo.*"],
        'PW': [r".*Perfusion_Weighted.*", r"sPWI", r"PerfusionWeighted"],
        'CBF_rel': [r".*relCBF.*"],
        'FM': [r"field_mapping", r"fieldmapping"],
        'DTI': [r"DTI"],
        'CAL': [r"cal", r"send", r"MoCo", r"localizer", r"loc"]
    }

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            regex_pattern = re.compile(pattern, re.IGNORECASE)
            if regex_pattern.search(file_path):
                return category
    return "--"  # Default if no match found


def main():
    base_path = r"/mnt/c/Users/hanna/Downloads/MAB NeuroRad AI Project"
    input_filename = "output02052024.txt"
    output_filename = "organized_ADNI_data.xlsx"

    input_filepath = f"{base_path}/{input_filename}"
    output_filepath = f"{base_path}/{output_filename}"

    df = parse_text_file(input_filepath)

    try:
        df.to_excel(output_filepath, index=False)
        logging.info(f"Excel file has been saved to {output_filepath}")
    except Exception as e:
        logging.error(f"Error saving Excel file: {e}")


if __name__ == "__main__":
    main()
