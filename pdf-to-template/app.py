from flask import Flask, request, redirect, url_for, render_template, jsonify
import os
import json
from werkzeug.utils import secure_filename
from mSousa.main_module import main as mSousa_main

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './pdf_directory'  # Actualiza esto con la ruta donde quieres guardar los archivos
app.config['IMAGES_FOLDER'] = './images'  # Actualiza esto con la ruta donde quieres guardar las imagenes
app.config['RESPONSE_FOLDER'] = './responses'  # Actualiza esto con la ruta donde quieres guardar las respuestas
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    duplicate_names = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400
        filename = file.filename.replace(" ", "_")
        if file:
            filename = secure_filename(filename)  # Use the modified filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            data, duplicate_names = mSousa_main(file_path, app.config['RESPONSE_FOLDER'], app.config['IMAGES_FOLDER']) 
            json_data = json.dumps(data)

            # Guarda los resultados en un archivo
            results_filename = filename + '.json'
            results_filepath = os.path.join(app.config['RESPONSE_FOLDER'], results_filename)
            with open(results_filepath, 'w') as f:
                f.write(json_data)

            if duplicate_names is not None:
                json_data_duplicate_names = json.dumps(duplicate_names)
                results_filename_duplicate_names = filename + '_duplicate_names.json'
                results_filepath_duplicate_names = os.path.join(app.config['RESPONSE_FOLDER'], results_filename_duplicate_names)
                with open(results_filepath_duplicate_names, 'w') as f:
                    f.write(json_data_duplicate_names)
                
                # Redirige al usuario a la URL de resultados
                return redirect(url_for('show_results_with_duplicates', filename=results_filename, filename_duplicates=results_filename_duplicate_names))

            return redirect(url_for('show_results', filename=results_filename))

    else:
        return render_template('upload.html')

@app.route('/results/<filename>', methods=['GET'])
def show_results(filename):
    # Carga los resultados del archivo
    results_filepath = os.path.join(app.config['RESPONSE_FOLDER'], filename)
    with open(results_filepath, 'r') as f:
        results = f.read()
    return render_template('report.html', data=json.loads(results))

@app.route('/results/<filename>/<filename_duplicates>', methods=['GET'])
def show_results_with_duplicates(filename, filename_duplicates):
    # Carga los resultados del archivo
    results_filepath = os.path.join(app.config['RESPONSE_FOLDER'], filename)
    with open(results_filepath, 'r') as f:
        results = f.read()
    # Carga los resultados del archivo
    results_filepath_duplicates = os.path.join(app.config['RESPONSE_FOLDER'], filename_duplicates)
    with open(results_filepath_duplicates, 'r') as f:
        results_duplicates = f.read()
    # Find duplicates
    return render_template('report_with_duplicates.html', data=json.loads(results), duplicate_names=json.loads(results_duplicates))


def allowed_file(filename):
    if '.' not in filename:
        return False, "File has no extension"
    elif filename.rsplit('.', 1)[1].lower() != 'json':
        return False, "File is not a JSON file"
    else:
        return True, "File is valid"

if __name__ == '__main__':
    app.run(debug=True)

