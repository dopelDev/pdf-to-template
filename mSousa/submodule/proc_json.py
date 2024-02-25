import re
import json

def extract_coordinates(vertices):
    x_coords = [vertex.get('x') for vertex in vertices]
    y_coords = [vertex.get('y') for vertex in vertices]
    return x_coords, y_coords

def find_coordinates(json_data, words):
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


def find_in_all_y(json_data, word1, word2, tolerance=4):
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


def transform_structure(all_rows):
    transformed = []
    for chunk in all_rows:
        text = ' '.join([row['text'] for row in chunk])
        x1 = min([row['x1'] for row in chunk])
        x2 = max([row['x2'] for row in chunk])
        y1 = min([row['y1'] for row in chunk])
        y2 = max([row['y2'] for row in chunk])
        transformed.append({'text': text, 'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2})
    return transformed

def find_in_all_x(json_data, data, tolerance=8):
    annotations = json_data.get('textAnnotations', [])[1:]
    results = []

    # Find the maximum X value in the annotations
    max_x = max(max(vertex.get('x', 0) for vertex in annotation.get('boundingPoly', {}).get('vertices', [{}])) for annotation in annotations)

    for item in data:
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

        # Add the last column to the result
        if next_column:
            result[f'column{column_number}'] = '$ ' + ' '.join(next_column)

        results.append(result)

    return results

def find_names_and_orders(json_data):
    name_pattern = r"([A-Za-z]+),\s([A-Za-z]+)(\s[A-Za-z])?"
    order_name = "N/A No Orders"
    annotations = json_data.get('textAnnotations', [])[1:]
    results = []

    for annotation in annotations:
        text = annotation.get('description', '')
        vertices = annotation.get('boundingPoly', {}).get('vertices', [])
        x_coords, y_coords = extract_coordinates(vertices)

        if re.match(name_pattern, text) or text == order_name:
            result = {
                'text': text,
                'x1': min(x_coords),
                'x2': max(x_coords),
                'y1': min(y_coords),
                'y2': max(y_coords)
            }
            results.append(result)

    return results
