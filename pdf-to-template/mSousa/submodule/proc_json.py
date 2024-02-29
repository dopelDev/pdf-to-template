import re
import json
from .logger import build_logger
import os
path = os.path.dirname(os.path.abspath(__file__))

# initialize logger
logger = build_logger('proc_json', path + '/logs')

# Extract x and y coordinates from a list of vertices
def extract_coordinates(vertices):
    x_coords = [vertex.get('x') for vertex in vertices]
    y_coords = [vertex.get('y') for vertex in vertices]
    return x_coords, y_coords

# Find the coordinates of certians words in the json data
def find_coordinates(json_data, words):
    logger.info(f'Finding coordinates of words ' + ', '.join(words))
    annotations = json_data.get('textAnnotations', [])[1:]
    word_coords = {word: {'x1': None, 'x2': None, 'y1': None, 'y2': None} for word in words}

    for annotation in annotations:
        text = annotation.get('description', '')
        vertices = annotation.get('boundingPoly', {}).get('vertices', [])
        x_coords, y_coords = extract_coordinates(vertices)

        if text in words and word_coords[text]['x1'] is None:
            word_coords[text]['x1'] = min(x_coords)
            word_coords[text]['x2'] = max(x_coords)
            word_coords[text]['y1'] = min(y_coords)
            word_coords[text]['y2'] = max(y_coords)

        if all(coords['x1'] is not None for coords in word_coords.values()):
            break

    return word_coords

# Find all Text Annotations in the json data that are below the Y coordinate of the word
def find_in_all_y(json_data, word1, word2, tolerance=4):
    logger.info(f'Finding text annotations below the Y coordinate of {word1} and {word2}')
    annotations = json_data.get('textAnnotations', [])[1:]
    all_rows = []
    next_row = []
    next_y = None

    # Calcula los mínimos y máximos de las coordenadas usando x1, x2, y1, y2
    x1, x2 = min(word1['x1'], word2['x1']), max(word1['x2'], word2['x2'])
    y1, y2 = min(word1['y1'], word2['y1']), max(word1['y2'], word2['y2'])

    for annotation in annotations:
        vertices = annotation.get('boundingPoly', {}).get('vertices', [])
        x_coords, y_coords = extract_coordinates(vertices)
        x_min, x_max = min(x_coords), max(x_coords)
        y_min = min(y_coords)  # Usamos solo y_min para la comparación con y1

        description = annotation.get('description', '')

        # Modifica la condición para que coincida con la estructura deseada
        if (x1 - tolerance) <= x_min and x_max <= (x2 + tolerance) and y_min > y1:
            if re.match(r'^w+$', description.lower()) or description.lower() == 'docsign':
                continue
            if next_y is None or y_min <= next_y + tolerance:
                next_row.append({'text': description, 'x1': x_min, 'x2': x_max, 'y1': y_min, 'y2': max(y_coords)})
                next_y = y_min
            else:
                all_rows.append(next_row)
                next_row = [{'text': description, 'x1': x_min, 'x2': x_max, 'y1': y_min, 'y2': max(y_coords)}]
                next_y = y_min

    all_rows.append(next_row)
    return all_rows

# Transform the structure of the data so that each rows is a dictionary with the text and the coordinates into a single list
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

# Find all text annotations in the json data that are to the right of a certain X coordinate and between two Y coordinates
# receive a structured json data
def find_in_all_x(json_data, data, tolerance=8):
    logger.info(f'Finding text annotations to the right of a certain X coordinate')
    annotations = json_data.get('textAnnotations', [])[1:]
    results = []

    # Find the maximum X value in the annotations
    max_x = max(max(vertex.get('x', 0) for vertex in annotation.get('boundingPoly', {}).get('vertices', [{}])) for annotation in annotations)

    for item in data:
        logger.debug(f'Processing item: {item["text"]}')
        y1, y2, x2_max = item['y1'] - tolerance, item['y2'] + tolerance, item['x2']
        result = {'text': item['text']}
        next_column = []
        next_x = None
        column_number = 1

        for annotation in annotations:
            vertices = annotation.get('boundingPoly', {}).get('vertices', [])
            x_coords, y_coords = extract_coordinates(vertices)
            x_min = min(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            description = annotation.get('description', '')

            if y1 <= y_min and y_max <= y2 and x_min > x2_max and x_min <= max_x:
                if description == '$':
                    continue
                elif next_x is None or x_min <= next_x + 10:
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


# Check if the rows have the same Names or Last Names and return them into a single list of dictionaries (for issues report)
# receive a strcutured json data
def agroup_duplicated_names(data: list[dict]):
    logger.info('Checking if the rows have the same First Names or Last Names and return them into a single list of dictionaries')
    grouped_data = {}

    for item in data:
        if 'text' in item:
            # Remove commas and split the 'text' field into parts
            parts = item['text'].replace(',', '').split()
            if len(parts) >= 1:
                first_name = parts[0]  # Use the first part (name) as the key
                # Ignore names that end with '.' or are a set of 'I' or have less than 2 characters
                if not (first_name.endswith('.') or all(char == 'I' for char in first_name) or len(first_name) < 2):
                    if first_name not in grouped_data:
                        grouped_data[first_name] = []
                    # Append the entire item to the group
                    grouped_data[first_name].append(item)
            if len(parts) >= 2:
                last_name = parts[1]  # Use the second part (lastname) as the key
                # Ignore families whose names end with '.' or are a set of 'I' or have less than 2 characters
                if not (last_name.endswith('.') or all(char == 'I' for char in last_name) or len(last_name) < 2):
                    if last_name not in grouped_data:
                        grouped_data[last_name] = []
                    # Append the entire item to the group
                    grouped_data[last_name].append(item)

    # Convert the grouped data into the desired format, only including names with more than 1 occurrence
    result = [[{"Name": name}, *members] for name, members in grouped_data.items() if len(members) > 1]
    logger.debug(f'Grouped data: {result}')
    return result
