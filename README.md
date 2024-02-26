# PDF to Template

This project allows for the conversion of PDF documents into a structured template format, utilizing `poppler-utils` for PDF rendering and `Tesseract` for Optical Character Recognition (OCR).

### Prerequisites

You'll need to have `poppler-utils` and `Tesseract` installed on your system to use this project. You can install them using your package manager. For example, on Ubuntu, you can use:

```bash
sudo apt-get install poppler-utils
sudo apt-get install tesseract-ocr
sudo apt-get install python3-virtualenv
cd pdf-to-template
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

### running the project
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app --worker-class gevent --timeout 90
```
