# Main module for pdf processing
import os
import re
import glob
import json
from .submodule import proc_pdf, call_to_ocr, proc_json

# Credentials for OCR
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

def main(file, responses_path, images_path):
    same_names = None
    pdf_name = proc_pdf.convert_pdf_to_images(file, images_path)
    if not os.path.exists(f"{responses_path}"):
        os.makedirs(f"{responses_path}")
    call_to_ocr.ocr_processing(credentials_file, images_path, f"{responses_path}/", pdf_name)
    final_json = []

    if os.path.exists(responses_path):
       print(f"processing {responses_path}/from_OCR_{pdf_name}/{pdf_name}/")
       json_files = glob.glob(f"{responses_path}/{pdf_name}/from_OCR_{pdf_name}/*.json")
       json_files.sort(key=os.path.getsize, reverse=True)
       print(f"processing {json_files} json files")
       first_iteration = True
       for file in json_files:
           print(f"Processing json file: {file}")
           with open(file, 'r') as f:
               json_data = json.load(f)
           if first_iteration:
               words = ['Employee', 'Retention', 'credit']
               coords = proc_json.find_coordinates(json_data, words)
               company_name = proc_json.find_company_name(json_data, coords) 
               company_name = proc_json.clean_company_name(company_name)
               print(f'company_name: {company_name}')
   
               first_iteration = False
               # Encuentra X1, X2 y la menor Y1 para "Master" y "tabs"
               words = ["Master", "Employee", "List"]
               coords = proc_json.find_coordinates(json_data, words)
   
               # Encuentra todos los textos que están debajo de "Master" y "tabs" y agrúpalos usando los valores obtenidos
               names = proc_json.find_in_all_y(json_data, coords)
               names = proc_json.transform_structure(names)
               all_columns = proc_json.find_in_all_x(json_data, names)
               company_info = {'Company name': company_name}
               print(f'company_info: {company_info}')
               all_columns.insert(0, company_info)
               final_json = all_columns
           else:
               print(f'processing json file {file}')
               words = ['DocuSign', 'Envelope']
               coords = proc_json.find_coordinates(json_data, words)
               names = proc_json.find_in_all_y(json_data, coords)
               names = proc_json.transform_structure(names)
               all_columns = proc_json.find_in_all_x(json_data, names)
               final_json.extend(all_columns)
       print('saving to json extructure')
       same_names = proc_json.agroup_duplicated_names(final_json)
       with open(f'{responses_path}/{pdf_name}/extructure.json', 'w') as f:
           json.dump(final_json, f, indent=4)

    return final_json, same_names
