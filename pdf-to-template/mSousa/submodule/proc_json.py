import re
from .logger import build_logger
import os
import json
import pandas as pd
import numpy as np
import glob
path = os.path.dirname(os.path.abspath(__file__))

# initialize logger
logger = build_logger('proc_json', path + '/logs')

# Extract x and y coordinates from a list of vertices
def extract_coordinates(vertices):
    x_coords = [vertex.get('x') for vertex in vertices]
    y_coords = [vertex.get('y') for vertex in vertices]
    return x_coords, y_coords

# Find the coordinates of maximum and mínimos words in the json data
def find_coordinates(json_data, words):
    logger.debug(f'Finding coordinates of words ' + ', '.join(words))
    annotations = json_data.get('textAnnotations', [])[1:]
    min_max_coords = {'x1': None, 'x2': None, 'y1': None, 'y2': None}

    for annotation in annotations:
        text = annotation.get('description', '')
        vertices = annotation.get('boundingPoly', {}).get('vertices', [])
        x_coords, y_coords = extract_coordinates(vertices)

        if text in words:
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)

            if min_max_coords['x1'] is None or x1 < min_max_coords['x1']:
                min_max_coords['x1'] = x1
            if min_max_coords['x2'] is None or x2 > min_max_coords['x2']:
                min_max_coords['x2'] = x2
            if min_max_coords['y1'] is None or y1 < min_max_coords['y1']:
                min_max_coords['y1'] = y1
            if min_max_coords['y2'] is None or y2 > min_max_coords['y2']:
                min_max_coords['y2'] = y2

    return min_max_coords

# Find all Text Annotations in the json data that are below the Y coordinate of the word
def find_in_all_y(json_data, coords, tolerance_x=16, tolerance_y=12):
    logger.debug(f'Finding text annotations below the Y coordinate of {coords}')
    annotations = json_data.get('textAnnotations', [])[1:]
    all_rows = []
    next_row = []
    next_y = None

    # Usa las coordenadas proporcionadas
    x1, x2 = coords['x1'], coords['x2']
    y1, y2 = coords['y1'], coords['y2']

    for annotation in annotations:
        vertices = annotation.get('boundingPoly', {}).get('vertices', [])
        x_coords, y_coords = extract_coordinates(vertices)
        x_min, x_max = min(x_coords), max(x_coords)
        y_min = min(y_coords)  # Usamos solo y_min para la comparación con y1

        description = annotation.get('description', '')

        if (x1 - (tolerance_x / 2)) <= x_min and x_max <= (x2 + tolerance_x) and y_min > y2:
            if re.match(r'^w+$', description.lower()) or description.lower() == 'docsign':
                continue
            if next_y is None or y_min <= next_y + tolerance_y:
                next_row.append({'text': description, 'x1': x_min, 'x2': x_max, 'y1': y_min, 'y2': max(y_coords)})
                next_y = y_min
            else:
                all_rows.append(next_row)
                next_row = [{'text': description, 'x1': x_min, 'x2': x_max, 'y1': y_min, 'y2': max(y_coords)}]
                next_y = y_min

    all_rows.append(next_row)
    return all_rows

# Find all text annotations in the json data that are to the right of a certain X coordinate and between two Y coordinates
# receive a structured json data
def find_in_all_x(json_data, names_coords, tolerance_x=12, tolerance_y=12):
    #  Check if the rows have the same length and process them
    # receive a strcutured json data
    def check_rows_lenght_then_process(result: dict): 
        regex = r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b'
        exclude_names = ['PPP Reduction', 'Total Wage']
        if result['text'] in exclude_names:
            logger.debug(f'return without processing: {result["text"]}')
            return result
        # Iterate over each item in the 'result' dictionary
        for key in list(result.keys()):
            # If the key starts with 'column' and the value matches the regex twice,
            # split the value into two and add the second value to the next column
            if key.startswith('column') and len(re.findall(regex, result[key])) == 2:
                values = re.findall(regex, result[key])
                next_column = 'column' + str(int(key[6:]) + 1)
                i = None
                if next_column in result:
                    # If the next column already exists, shift all subsequent columns
                    i = int(next_column[6:])
                    while f'column{i}' in result:
                        i += 1
                    while i > int(next_column[6:]):
                        result[f'column{i}'] = result[f'column{i-1}']
                        i -= 1
                # Make the last part of the split the previous column
                result[key] = '$ ' + values[1]
                # Make the previous column the second column
                result[next_column] = result[key]
                # Make the first part of the split the last column
                result[f'column{i}'] = '$ ' + values[0]
        
        # Return the 'result' dictionary
        return result
    
    logger.debug(f'Finding text annotations to the right of a certain X coordinate')
    annotations = json_data.get('textAnnotations', [])[1:]
    results = []

    # Find the maximum X value in the annotations
    max_x = max(max(vertex.get('x', 0) for vertex in annotation.get('boundingPoly', {}).get('vertices', [{}])) for annotation in annotations)

    for item in names_coords:
        logger.debug(f'Processing item: {item["text"]}')
        y1, y2, x2_max = item['y1'] - tolerance_y, item['y2'] + tolerance_y, item['x2']
        result = {'text': item['text']}
        next_column = []
        next_x = None
        column_number = 1
        first_letter_found = False

        for annotation in annotations:
            vertices = annotation.get('boundingPoly', {}).get('vertices', [])
            x_coords, y_coords = extract_coordinates(vertices)
            x_min = min(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            description = annotation.get('description', '')

            if y1 <= y_min and y_max <= y2 and x_min > x2_max and x_min <= max_x:
                if description == '$':
                    continue
                elif not first_letter_found and description.isalpha():
                    result['text'] += ' ' + description
                    first_letter_found = True
                elif next_x is None or x_min <= next_x + tolerance_x:
                    next_column.append(description)
                    next_x = x_min
                else:
                    result[f'column{column_number}'] = '$ ' + ' '.join(next_column)
                    next_column = [description]
                    next_x = x_min
                    column_number += 1

        if next_column:
            result[f'column{column_number}'] = '$ ' + ' '.join(next_column)
        if len(result) < 23:
            logger.debug(f'Rows founded for: {item["text"]} Rows length: {len(result)} is less than 23')
            result = check_rows_lenght_then_process(result)
        results.append(result)

    return results

# Transform the structure of the data so that each rows is a dictionary with the text and the coordinates into a single list
# agrouping the text of the rows
def transform_structure(all_rows):
    logger.info('Transforming structure of the data')
    transformed = []
    for chunk in all_rows:
        text = ' '.join([row['text'] for row in chunk])
        x1 = min([row['x1'] for row in chunk])
        x2 = max([row['x2'] for row in chunk])
        y1 = min([row['y1'] for row in chunk])
        y2 = max([row['y2'] for row in chunk])
        transformed.append({'text': text, 'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2})
    return transformed

# search for the name of the company in the json data
def get_company_name(json_data, coords):
    
    def find_company_name(json_data, coords, tolerance_x=6):
        logger.debug(f'Finding the name of the company in the json data')
        annotations = json_data.get('textAnnotations', [])[1:]
        company_name = []
    
        x1, x2 = coords['x1'], coords['x2']
    
        for annotation in annotations:
            vertices = annotation.get('boundingPoly', {}).get('vertices', [])
            x_coords, _ = extract_coordinates(vertices)
            x_min, x_max = min(x_coords), max(x_coords)
            description = annotation.get('description', '')
    
            if (x1 - tolerance_x / 2) <= x_min and x_max <= (x2 + tolerance_x):
                company_name.append(description) 
    
        logger.debug(f'Company name: {company_name}')
        return company_name
    
    def clean_company_name(company_name: list[str]):
        logger.debug(f'Cleaning the company name')
        excluded_words = ['Attachment', 'Employee', 'Retention', 'Credit']
        numeric = re.compile(r'\d')
        single_letter = re.compile(r'^[a-zA-Z]$')
        clean_words = []
    
        for chunk in company_name:
            logger.debug(f'Processing chunk: {chunk}')
            if chunk in excluded_words:
                continue
            if numeric.search(chunk):
                break
            if single_letter.search(chunk):
                continue
            clean_words.append(chunk) 
            logger.debug(f'Clean words: {clean_words}')
    
        return ' '.join(clean_words)

    company_name = find_company_name(json_data, coords)
    clean_name = clean_company_name(company_name)
    dict_company_name = {'Company name': clean_name}
    return dict_company_name

# Convert the json data to a data frame and return it like a json
def json_to_dataframe_and_transform(json_data):
    # Convertir JSON a DataFrame
    df = pd.DataFrame(json_data)
    
    # Crear un nuevo DataFrame para los datos transformados
    transformed_data = []
    
    # Nombre de la compañía
    company_name = df.iloc[0]['Company name']
    
    # Iterar sobre las filas del DataFrame original, excluyendo la primera fila que es el nombre de la compañía
    for _, row in df.iloc[1:].iterrows():
        # Diccionario para los datos transformados de esta fila
        transformed_row = {'Company name': company_name, 'Employee Name': row['text']}
        
        # Iterar sobre cada conjunto de 3 columnas para cada trimestre
        for i in range(1, 22, 3):  # de 1 a 21 en pasos de 3 para los 7 trimestres
            quarter = (i - 1) // 3 + 1
            quarter_data = {
                'Total Wage': row.get(f'column{i}', 'N/A'),
                'Qualified Wage': row.get(f'column{i+1}', 'N/A'),
                'ERC Credit': row.get(f'column{i+2}', 'N/A')
            }
            transformed_row[f'Q{quarter}'] = quarter_data
        
        # La columna 22 es el total general
        transformed_row['Total'] = row.get('column22', 'N/A')  # Asumiendo que el total está en la columna 22
        
        transformed_data.append(transformed_row)
    
    # Convertir la lista de diccionarios a un DataFrame
    transformed_df = pd.DataFrame(transformed_data)
    return transformed_data

# work a dataframe 
def merge_dataframes(responses_path):
    logger.info(f'Searching structured jsons in {responses_path}')
    logger.info('Merging dataframes')
    
    # Convert monetary strings to numbers
    def to_number(value):
        if pd.isna(value):
            return value  # Keep NaN as NaN
        if value == '$ 0.00':
            return 0  # Keep 0 as 0
        # Remove $ and commas, then convert to float
        return float(value.replace('$', '').replace(',', '').strip())

    # Sum monetary values and convert back to monetary string format
    def sum_monetary_values(series):
        total = series.apply(to_number).sum()
        if pd.isna(total):
            return total  # Return NaN if total is NaN
        if total == 0:
            return '$ 0.00'  # Return '$ 0.00' if total is 0
        return f'${total:,.2f}'  # Convert back to string in monetary format
    
    # Search for all JSON files in the responses folder
    json_files = glob.glob(f"{responses_path}/**/structured.json", recursive=True)
    dataframes = []
    for index, file in enumerate(json_files):
        with open(file, 'r') as f:
            json_data = json.load(f)
        logger.info(f'Processing file: {file}')
        # Convert JSON to DataFrame and transform data
        df = pd.DataFrame(json_data)
        df.to_csv(f'df{index}.csv', index=False)
        dataframes.append(df)
    logger.info(f'JSON files: {json_files}')
    
    if not dataframes:
        logger.error('No dataframes to merge.')
        return pd.DataFrame()  # Return an empty DataFrame if there are no dataframes to merge
    
    # Concatenate all dataframes
    concatenated_df = pd.concat(dataframes, ignore_index=True)
    concatenated_df.to_csv('concatenated_df.csv', index=False)
    
    # Sort by 'Employee Name' or any other relevant column
    concatenated_df.sort_values(by=['Employee Name'], inplace=True)
    
    # Group by 'Employee Name' and aggregate using custom functions
    # -- LEGACY --
    logger.info('Concatenated dataframes')
    concatenated_df.rename(columns={concatenated_df.columns[0]: 'Company Name'}, inplace=True)
    logger.info('Renamed columns')
    grouped_df = concatenated_df.groupby('Employee Name', as_index=False).agg({
        'Total': sum_monetary_values,
        'Company Name': lambda x: 'Data Merged'  # Replace company names with "Data Merged"
        # Add more columns as needed
    })
    # -- LEGACY --
    logger.info('Dataframes merged') 
    logger.info(grouped_df)
    grouped_df.to_csv('grouped_df.csv', index=False)
    # transform the dataframe to a json
    logger.info('Dataframes transformed to json')
    grouped_json_str = grouped_df.to_json(orient='records')
    grouped_json = json.loads(grouped_json_str)
    logger.info('Dataframes transformed to json')
    logger.info(grouped_json)
    return grouped_json

# Work a dataframe to fix the PPP Reduction row
def fix_ppp_reduction(json_data):
    for data in json_data:
        if data.get('Employee Name') == 'PPP Reduction':
            # Inicializar all_data como una lista plana de los valores deseados
            all_data = []
            for key, value in data.items():
                if 'Q' in key:
                    all_data.extend([
                        value['Total Wage'], value['Qualified Wage'], value['ERC Credit']
                    ])

            # Filtrar None para evitar errores con np.nan
            all_data = [x for x in all_data if x is not None]

            index_of_all_data = 0  # Índice para iterar sobre all_data

            # Iterar sobre las entradas 'Q'
            for q_key in [f'Q{value}' for value in range(1, 8)]:  # Asumiendo que hay 7 entradas 'Q'
                if q_key in data:
                    # Establecer 'Total Wage' a np.nan
                    data[q_key]['Total Wage'] = np.nan

                    # Asignar nuevos valores a 'Qualified Wage' y 'ERC Credit' desde all_data
                    for sub_key in ['Qualified Wage', 'ERC Credit']:
                        if index_of_all_data < len(all_data):
                            data[q_key][sub_key] = all_data[index_of_all_data]
                            index_of_all_data += 1
                        else:
                            break  # Salir si no hay más datos en all_data para asignar

    return json_data
