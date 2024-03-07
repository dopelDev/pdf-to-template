from google.cloud import vision
from google.oauth2 import service_account
import os
import glob
import re
from time import sleep

# Set the environment variable for Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f'{os.getcwd()}/cosmic-octane-402721-14cfb94c3c72.json'
credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

def ocr_processing(cre, image_dir, dest_path, pdf_name):
    # Get all the images in the directory
    image_files = glob.glob(f"{image_dir}/{pdf_name}/*.png")

    # Extract the base name of the PDF and remove the extension
    pdf_name_without_ext = os.path.splitext(os.path.basename(pdf_name))[0]

    # Create the final directory based on the PDF name and within it, a 'response' subdirectory
    final_dest_path = os.path.join(dest_path, pdf_name_without_ext)
    print(f"final_dest_path: {final_dest_path}")
    print(f"image_dir: {image_dir}")
    print(f"image_files: {image_files}")
    print(f"pdf_name: {pdf_name}")
    if not os.path.exists(final_dest_path):
        os.makedirs(final_dest_path)

    for i, image_path in enumerate(image_files):
        try:
            # Load the credentials and create a Cloud Vision API client
            credentials = service_account.Credentials.from_service_account_file(cre)
            client = vision.ImageAnnotatorClient(credentials=credentials)
            print(f"client: {client}")

            # Ensure the image file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"File not found: {image_path}")

            # Load the image from the specified file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)

            # Make a text detection request on the image
            response = client.text_detection(image=image)

            # Check for errors in the response
            if response.error.message:
                raise Exception(f'Error Code: {response.error.code}\nError Message: {response.error.message}')

            # Convert the response to JSON format
            response_json = vision.AnnotateImageResponse.to_json(response)  # This line was missing before

            # Extract the base name of the image, remove the extension and final numbers
            image_name_without_ext = re.sub(r'\d+$', '', os.path.splitext(os.path.basename(image_path))[0])

            # Append the index to the filename to maintain uniqueness and save it in the 'response' subdirectory
            json_file_path = os.path.join(final_dest_path, f'{image_name_without_ext}{i}.json')
            with open(json_file_path, 'w') as json_file:
                json_file.write(response_json)

            print(f"The credentials verification was successful for {image_path}. The API response has been saved at '{json_file_path}'.")
        except FileNotFoundError as e:
            print(f"Error opening the image file: {e}")
        except Exception as e:
            print(f"Error verifying credentials: {e}")
    sleep(1)

