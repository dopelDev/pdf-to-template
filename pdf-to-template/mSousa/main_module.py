# Main module for pdf processing
import os
import re
import glob
import json
from .submodule import proc_pdf, call_to_ocr, proc_json

# Credentials for OCR
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

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
        with open(f'{responses_path}/{pdf_name}/extructure.json', 'w') as f:
            json.dump(final_json, f, indent=4)

    return final_json

def main(input_data, responses_path, images_path):
    if isinstance(input_data, list):
        final_results = []
        merge_results = []
        for file in input_data:
            result = processing_data(file, responses_path, images_path)
            final_results.append(result)
    else:
        final_results = processing_data(input_data, responses_path, images_path)

    proc_json.merge_dataframes(responses_path)

    return final_results
