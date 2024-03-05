# Main module for pdf processing
import os
import re
import glob
import json
from .submodule import proc_pdf, call_to_ocr, proc_json

# Credentials for OCR
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

def get_company_name(inc_name):
    company_name = []  # Inicializa company_name como una lista vacía

    for chunks in inc_name:
        for chunk in chunks:
            text = chunk['text']
            if text == "Inc" or re.search(r'\d', text):
                company_name.append("Inc")
                break  # Detiene la recolección al encontrar la primera coma o un texto que contenga un número
            if text != "Employee" and text != "Retention":  # Ignora la palabra "Employee"
                company_name.append(text)  # Agrega la palabra actual a company_name
        else:
            continue  # Continúa al siguiente chunk si no se encontró coma o número en el chunk actual
        break  # Sale del bucle externo si se encontró una coma o un número

    # Une las partes para obtener el nombre de la empresa como una cadena
    company_name_str = " ".join(company_name)

    return company_name_str


def main(file, responses_path, images_path):
    same_names = None
    pdf_name = proc_pdf.convert_pdf_to_images(file, images_path)
    if not os.path.exists(f"{responses_path}/results/{pdf_name}"):
        os.makedirs(f"{responses_path}/results/{pdf_name}")
    call_to_ocr.ocr_processing(credentials_file, images_path, f"{responses_path}/results", pdf_name)
    final_json = []

    if os.path.exists(responses_path):
       print(f"processing {responses_path}/results/{pdf_name}/")
       json_files = glob.glob(f"{responses_path}/results/{pdf_name}/*.json")
       json_files.sort(key=os.path.getsize, reverse=True)
       print(f"processing {json_files} json files")
       first_iteration = True
       for file in json_files:
           print(f"Processing json file: {file}")
           with open(file, 'r') as f:
               json_data = json.load(f)
           if first_iteration:
               words = ['Employee', 'Retention', 'Credit']
               coords = proc_json.find_coordinates(json_data, words)
               inc_name = proc_json.find_in_all_y(json_data, coords)
               company_name = get_company_name(inc_name)
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
       with open(f'{responses_path}/results/extructure.json', 'w') as f:
           json.dump(final_json, f, indent=4)

    return final_json, same_names
