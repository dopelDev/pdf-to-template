import pandas as pd

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

