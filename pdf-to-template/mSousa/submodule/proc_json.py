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
    exclude_names = ['PPP Reduction', 'Total Wage']
    if result['text'] in exclude_names:
        logger.debug(f'return without processing: {result["text"]}')
        return result
    return result


# Check if the rows have the same Names or Last Names and return them into a single list of dictionaries (for issues report)
# receive a strcutured json data
def agroup_duplicated_names(names : list):
    pass
