# Main module for pdf processing
import os
import re
import glob
import json
from .submodule import proc_pdf, call_to_ocr, proc_json

# Credentials for OCR
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# verificate process of the data

def format_check(file):
    if re.search(r'.pdf$', file):
        return True
    else:
        return False

def verficate_multiple_files(files):
    for file in files:
        if not format_check(file):
            return False
    return True

def verificate_has_headers(json_data):
    words = ['Employee', 'Retention', 'credit']
    headers_coords = proc_json.find_coordinates(json_data, words)
    if headers_coords:
        return True
    else:
        return False

# merge Company name with the rest of the data
def merge_company_name(json_data, company_name):
    # return json_data with company name like a dictionary in the first position
    return json_data.insert(0, company_name) 

def processing_data(file, responses_path, images_path):
    pdf_name = proc_pdf.convert_pdf_to_images(file, images_path)
    if not os.path.exists(f"{responses_path}"):
        os.makedirs(f"{responses_path}")
    call_to_ocr.ocr_processing(credentials_file, images_path, f"{responses_path}/", pdf_name)
    processing_json = []
    final_json = []
    
    if os.path.exists(f"{responses_path}/{pdf_name}/from_OCR_{pdf_name}"):
        json_files = glob.glob(f"{responses_path}/{pdf_name}/from_OCR_{pdf_name}/*.json")
        json_files.sort(key=os.path.getsize, reverse=True)
        first_iteration = True
        for file in json_files:
            with open(file, 'r') as f:
                json_data = json.load(f)
            if first_iteration:
                words = ['Employee', 'Retention', 'credit']
                coords = proc_json.find_coordinates(json_data, words)
                company_name = proc_json.find_company_name(json_data, coords) 
                company_name = proc_json.clean_company_name(company_name)

                first_iteration = False
                words = ["Master", "Employee", "List"]
                coords = proc_json.find_coordinates(json_data, words)

                names = proc_json.find_in_all_y(json_data, coords)
                names = proc_json.transform_structure(names)
                all_columns = proc_json.find_in_all_x(json_data, names)
                company_info = {'Company name': company_name}
                all_columns.insert(0, company_info)
                processing_json = all_columns
            else:  
                words = ['DocuSign', 'Envelope']
                coords = proc_json.find_coordinates(json_data, words)
                names = proc_json.find_in_all_y(json_data, coords)
                names = proc_json.transform_structure(names)
                all_columns = proc_json.find_in_all_x(json_data, names)
                processing_json.extend(all_columns)
  
        final_json = proc_json.json_to_dataframe_and_transform(processing_json) 
        ppp_fixed = proc_json.fix_ppp_reduction(final_json)
        final_json = ppp_fixed
        with open(f'{responses_path}/{pdf_name}/structured.json', 'w') as f:
            json.dump(final_json, f, indent=4)

    return final_json

def main(input_data, responses_path, images_path):
    multiple_files = None
    merged_data = None
    if len(input_data) > 1:
        final_results = []
        multiple_files = True
        for file in input_data:
            result = processing_data(file, responses_path, images_path)
            final_results.append(result)
        merged_data = proc_json.merge_dataframes(responses_path)

    else:
        multiple_files = False
        final_results = processing_data(input_data[0], responses_path, images_path)


    return final_results, multiple_files, merged_data
