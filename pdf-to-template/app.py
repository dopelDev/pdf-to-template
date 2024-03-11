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
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    session['processed_files'] = []
    data = None
    multiple_files = None
    if request.method == 'POST':
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return "No selected files", 400
        
        print(f'From App: {files} \nType: {type(files)}')
        pdf_directories_files = []
        
        allowed_files = None 
        for file in files:
            if file and allowed_file(file.filename):
                allowed_files = True
                filename = secure_filename(file.filename.replace(" ", "_"))
                pdf_directories_files.append(os.path.join(g.pdf_directory, filename))
            else:
                allowed_files = False
                break

        # Here Template for don't allow files

        if allowed_files:
            for index, file in enumerate(files):
                print(f'FROM APP: {pdf_directories_files[index]}')   
                file.save(pdf_directories_files[index])

            data, multiple_files = mSousa_main(pdf_directories_files, g.response_folder, g.images_folder)
        session['total_results'] = data 

        return redirect(url_for('show_results',multiple_files=multiple_files ))

    return render_template('upload.html')

@app.route('/results', methods=['GET'])
def show_results():
    data = session.get('total_results', None)
    multiple_files = request.args.get('multiple_files', 'False') == 'True'
    print(f'Multiple Files: ', type(multiple_files))
    if multiple_files:
        return render_template('report_multiply.html', datasets=data)
    else:
        return render_template('report.html', datasets=data)

if __name__ == '__main__':
    app.run(debug=True)

