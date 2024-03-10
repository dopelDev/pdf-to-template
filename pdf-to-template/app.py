from flask import Flask, request, redirect, url_for, render_template, session, g
import os
import json
from werkzeug.utils import secure_filename
import uuid
from flask_session import Session
from mSousa.main_module import main as mSousa_main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

@app.before_request
def before_request():
    if 'session_id' not in session:
        session['session_id'] = uuid.uuid4().hex  # Genera un UUID para la sesión si no existe uno

    session_id = session.get('session_id')
    session_folder_name = f'session_{session_id}'
    base_path = os.path.join('.', session_folder_name)

    if not os.path.exists(base_path):
        os.makedirs(base_path)
        os.makedirs(os.path.join(base_path, 'pdf_directory'))
        os.makedirs(os.path.join(base_path, 'images'))
        os.makedirs(os.path.join(base_path, 'responses'))

    g.session_folder = base_path
    g.pdf_directory = os.path.join(base_path, 'pdf_directory')
    g.images_folder = os.path.join(base_path, 'images')
    g.response_folder = os.path.join(base_path, 'responses')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return "No selected files", 400

        processed_files = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename.replace(" ", "_"))
                file_path = os.path.join(g.pdf_directory, filename)
                file.save(file_path)

                data = mSousa_main(file_path, g.response_folder, g.images_folder)
                json_data = json.dumps(data)

                filename_without_ext = os.path.splitext(filename)[0]
                processed_folder = os.path.join(g.response_folder, filename_without_ext, 'processed')
                if not os.path.exists(processed_folder):
                    os.makedirs(processed_folder)

                results_filename = filename_without_ext + '.json'
                results_filepath = os.path.join(processed_folder, results_filename)
                with open(results_filepath, 'w') as f:
                    f.write(json_data)

                processed_files.append(results_filename)

        session['processed_files'] = processed_files
        return redirect(url_for('show_results'))

    return render_template('upload.html')

@app.route('/results', methods=['GET'])
def show_results():
    json_filenames = session.get('processed_files', [])
    datasets = []

    for filename in json_filenames:
        processed_folder = os.path.join(g.response_folder, os.path.splitext(filename)[0], 'processed')
        results_filepath = os.path.join(processed_folder, filename)
        with open(results_filepath, 'r') as f:
            datasets.append(json.load(f))

    return render_template('report.html', datasets=datasets)

if __name__ == '__main__':
    app.run(debug=True)

