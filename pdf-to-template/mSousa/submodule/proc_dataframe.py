import pandas as pd
import numpy as np
from .logger import build_logger
import os
path = os.path.dirname(os.path.abspath(__file__))

# Crear un logger
logger = build_logger('proc_dataframe', path + '/logs')

# Fuction get duplicate names
def get_duplicate_names(json_data):
    df = pd.DataFrame(json_data)
    
    duplicate_name_parts = set()
    name_parts = {}
    
    for name in df['Employee Name']:
        parts = [part for part in name.split() if len(part) > 1]
        for part in parts:
            if part in name_parts and part not in duplicate_name_parts:
                duplicate_name_parts.add(part)
            name_parts[part] = name_parts.get(part, 0) + 1
    
    duplicate_rows = []
    for index, row in df.iterrows():
        name = row['Employee Name']
        for part in duplicate_name_parts:
            if part in name:
                duplicate_rows.append(index)
                break
    
    duplicate_data = df.iloc[duplicate_rows].to_dict(orient='records')
    
    return duplicate_data

def json_to_dataframe_and_transform(json_data, company_name):
    # Work a dataframe to fix the PPP Reduction row
    logger.info('Transforming JSON data to DataFrame')
    def fix_ppp_reduction(ppp_reduction_data):
        logger.info('Fixing PPP Reduction data')
        # Función para corregir los datos de la fila 'PPP Reduction'
        if ppp_reduction_data.get('Employee Name') == 'PPP Reduction':
            # Inicializar all_data como una lista plana de los valores deseados
            all_data = []
            for key, value in ppp_reduction_data.items():
                if 'Q' in key:
                    all_data.extend([
                        value['Total Wage'], value['Qualified Wage'], value['ERC Credit']
                    ])
    
            # Filtrar None para evitar errores con np.nan
            all_data = [x for x in all_data if x is not None]
    
            index_of_all_data = 0  # Índice para iterar sobre all_data
    
            # Iterar sobre las entradas 'Q'
            for q_key in [f'Q{value}' for value in range(1, 8)]:  # Asumiendo que hay 7 entradas 'Q'
                if q_key in ppp_reduction_data:
                    # Establecer 'Total Wage' a np.nan
                    ppp_reduction_data[q_key]['Total Wage'] = np.nan
    
                    # Asignar nuevos valores a 'Qualified Wage' y 'ERC Credit' desde all_data
                    for sub_key in ['Qualified Wage', 'ERC Credit']:
                        if index_of_all_data < len(all_data):
                            ppp_reduction_data[q_key][sub_key] = all_data[index_of_all_data]
                            index_of_all_data += 1
                        else:
                            break  # Salir si no hay más datos en all_data para asignar
    
        return ppp_reduction_data 
    # Convertir JSON a DataFrame
    df = pd.DataFrame(json_data)
    
    # Crear un nuevo DataFrame para los datos transformados
    transformed_data = []
    
    # Iterar sobre las filas del DataFrame original, excluyendo la primera fila que es el nombre de la compañía
    for _, row in df.iloc[1:].iterrows():
        # Diccionario para los datos transformados de esta fila
        transformed_row = {'Company Name': company_name, 'Employee Name': row['text']}
        
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
    # Debugging
    ppp_reduction_data = next((data for data in transformed_data if data['Employee Name'] == 'PPP Reduction'), None)
    fixed_ppp_reduction_data = fix_ppp_reduction(ppp_reduction_data)

    transformed_df = pd.DataFrame(transformed_data)
    return transformed_data

