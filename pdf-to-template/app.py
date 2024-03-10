from flask import Flask, request, redirect, url_for, render_template, session
import os
import json
from werkzeug.utils import secure_filename
from mSousa.main_module import main as mSousa_main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['UPLOAD_FOLDER'] = './pdf_directory'  # Actualiza esto con la ruta donde quieres guardar los archivos
app.config['IMAGES_FOLDER'] = './images'  # Actualiza esto con la ruta donde quieres guardar las imagenes
app.config['RESPONSE_FOLDER'] = './responses'  # Actualiza esto con la ruta donde quieres guardar las respuestas
# tengo que pasar la verficacion a un modulo
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return "No selected files", 400

        # Lista para almacenar nombres de los archivos procesados
        processed_files = []

        for file in files:
            filename = secure_filename(file.filename.replace(" ", "_"))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            data = mSousa_main(file_path, app.config['RESPONSE_FOLDER'], app.config['IMAGES_FOLDER'])
            json_data = json.dumps(data)

            filename_without_ext = os.path.splitext(filename)[0]
            processed_folder = os.path.join(app.config['RESPONSE_FOLDER'], filename_without_ext, 'processed')
            if not os.path.exists(processed_folder):
                os.makedirs(processed_folder)

            results_filename = filename_without_ext + '.json'
            results_filepath = os.path.join(processed_folder, results_filename)
            with open(results_filepath, 'w') as f:
                f.write(json_data)

            # Agrega el nombre del archivo procesado a la lista
            processed_files.append(results_filename)

        # Almacena los nombres de los archivos procesados en la sesión
        session['processed_files'] = processed_files

        # Redirige al usuario a la página de resultados
        return redirect(url_for('show_results'))

    return render_template('upload.html')

@app.route('/results', methods=['GET'])
def show_results():
    # Recupera los nombres de los archivos procesados de la sesión
    json_filenames = session.get('processed_files', [])

    datasets = []
    for filename in json_filenames:
        processed_folder = os.path.join(app.config['RESPONSE_FOLDER'], os.path.splitext(filename)[0], 'processed')
        results_filepath = os.path.join(processed_folder, filename)
        with open(results_filepath, 'r') as f:
            # Directamente cargar y agregar los datos al dataset
            datasets.append(json.load(f))

    return render_template('report.html', datasets=datasets)


def allowed_file(filename):
    if '.' not in filename:
        return False, "File has no extension"
    elif filename.rsplit('.', 1)[1].lower() != 'json':
        return False, "File is not a JSON file"
    else:
        return True, "File is valid"

if __name__ == '__main__':
    app.run(debug=True)

