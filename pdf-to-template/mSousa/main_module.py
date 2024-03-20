# Main module for pdf processing
import os
import glob
import json
from .submodule import proc_pdf, call_to_ocr, proc_json, proc_dataframe

# Credentials for OCR
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

def checking_headers(json_path):
    def checking_coordinates(coords):
        if coords['x1'] is None or coords['y1'] is None or coords['x2'] is None or coords['y2'] is None:
            return False
        else: 
            return True

    with open(json_path, 'r') as file:
        json_file = json.load(file)
    words = ['Master', 'Employee', 'List']
    coords = proc_json.find_coordinates(json_file, words)
    print(f'FROM CHECKING HEADERS {coords}')

    if checking_coordinates(coords):
        return True
    else:
        return False

def processing_with_headers(json_path):
    with open(json_path, 'r') as file:
        json_file = json.load(file)
    words = ['Master', 'Employee', 'List']
    coords = proc_json.find_coordinates(json_file, words)
    print(f'FROM PROCESSING WITH HEADERS {coords}')
    employee_list = proc_json.find_in_all_y(json_file, coords)
    employee_list_structured = proc_json.transform_structure(employee_list)
    columns = proc_json.find_in_all_x(json_file, employee_list_structured) 

    return columns 

def processing_without_headers(json_path):
    with open(json_path, 'r') as file:
        json_file = json.load(file)
    words = ['DocuSign', 'Envelope']
    coords = proc_json.find_coordinates(json_file, words)
    print(f'FROM PROCESSING WITHOUT HEADERS {coords}')
    employee_list = proc_json.find_in_all_y(json_file, coords)
    employee_list_structured = proc_json.transform_structure(employee_list)
    columns = proc_json.find_in_all_x(json_file, employee_list_structured)

    return columns

# process json file or files
def sub_main(files, response_path, images_path):
    def processing_pdf(file, response_path, images_path):
        # Process pdf file
        # 1. Check directories
        if not os.path.exists(f'{response_path}'):
            os.makedirs(f'{response_path}')
        # 2. Convert pdf to images
        pdf_name = proc_pdf.convert_pdf_to_images(file, images_path)
        if not os.path.exists(f'{response_path}/{pdf_name}'):
            os.makedirs(f'{response_path}/{pdf_name}')
        # 3. Call to OCR
        jsons_path = []
        call_to_ocr.ocr_processing(credentials_file, f'{images_path}/{pdf_name}', f'{response_path}/', pdf_name)
        if os.path.exists(f'{response_path}/{pdf_name}/from_OCR_{pdf_name}'):
            json_files = glob.glob(f'{response_path}/{pdf_name}/from_OCR_{pdf_name}/*.json')
            json_files.sort(key=os.path.getsize, reverse=True)
            jsons_path.extend(json_files)
        
        return jsons_path
    # Sub main function for processing json files
    jsons_path = []
    if isinstance(files, list):
        for file in files:
            json_path = processing_pdf(file, response_path, images_path)
            jsons_path.extend(json_path)
    else:
        jsons_path.extend(processing_pdf(files, response_path, images_path))

    return jsons_path

def processing_json(companies):
    pass
        
def main(files, response_path, images_path):
    # Main function for processing pdf files
    # Process pdf files to OCR json files
    jsons_path = sub_main(files, response_path, images_path)
    print(f'FROM MAIN {jsons_path}')
    # Process json files
    companies = []
    columns = []
    # 1 processing single json file
    if len(jsons_path) == 1:
        if checking_headers(jsons_path[0]):
            columns = processing_with_headers(jsons_path[0])
            company_name = proc_json.get_company_name(jsons_path[0])
            companies.append({'company_name': company_name, 'columns': columns})
        else:
            return "Don't allow to process this file"
    # 2 processing multiple json files
    else:
        first_itereation = True
        for json_path in jsons_path:
            if first_itereation:
                if checking_headers(json_path):
                    columns = processing_with_headers(json_path)
                    company_name = proc_json.get_company_name(json_path)
                    companies.append({'company_name': company_name, 'columns': columns})
                else:
                    return "Don't allow to process this file"
                first_itereation = False
            else:
                if checking_headers(json_path):
                    columns = processing_with_headers(json_path)
                    company_name = proc_json.get_company_name(json_path)
                    companies.append({'company_name': company_name, 'columns': columns})
                else:
                    columns = processing_without_headers(json_path)
                    if companies:
                        companies[-1]['columns'].extend(columns)
                    else:
                        return "Error: No previous company found to append columns"
    # 3 processing companies
    processing_json(companies)
    # 4 debugging
    for company in companies:
        print(f'Company: {company["company_name"]}')
        print(f'Columns: {company["columns"]}')
