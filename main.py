import serverless_wsgi

import flask
from flask import request, redirect, flash, url_for, abort

import dash
from dash.dependencies import Input, Output, State

import imghdr
import os

from python.dlmodel import Model

from werkzeug.utils import secure_filename

# from PIL import Image, ImageFile
# ImageFile.LOAD_TRUNCATED_IMAGES = True

#from tensorflow.keras.preprocessing import image # NB using this instead of import PIL to handle errors reading images. See also https://github.com/python-pillow/Pillow/issues/4678
from tensorflow.keras.utils import load_img, img_to_array

main = flask.Flask(__name__)
main.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 # increased as bad request with large images
main.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
main.config['UPLOAD_FOLDER'] = '/tmp/'

def validate_image(stream):
    header = stream.read(1024)  # increased from 512 as bad request with large images
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format # (format if format != 'jpeg' else 'jpg') ASSUMES JPEG AND JPG FORMAT CAN BOTH BE UPLOADED

@main.route('/')
def index():
    return flask.render_template('index.html')

@main.route('/', methods=['POST'])
def upload_files():
    # return "<p>Hello, World!</p>" test - this works
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    # return filename  test - this works
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # return file_ext # test - this is returned
        # return validate_image(uploaded_file.stream) # test - this is not returned
        """ if file_ext not in main.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            abort(400) """ # removed validation for now, can test as a post-process

        """ savedImg = uploaded_file.save(os.path.join(main.config['UPLOAD_FOLDER'], filename))
        
        img = load_img(os.path.join(main.config['UPLOAD_FOLDER'], filename),color_mode='rgb', target_size=(224, 224)) """
        
        #uploaded_file.save(os.path.join(main.config['UPLOAD_FOLDER'], filename))
        #img = load_img(os.path.join(main.config['UPLOAD_FOLDER'], filename),color_mode='rgb', target_size=(224, 224))

        # a new approach to change directly to AWS tmp storage location
        currentPath = os.getcwd() 
        os.chdir('/tmp/')
        # savedImg = uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        savedImg = uploaded_file.save(filename)

        # img = load_img(os.path.join(app.config['UPLOAD_FOLDER'], filename),color_mode='rgb', target_size=(224, 224)) # works locally, but not on aws
        # img = load_img(filename, color_mode='rgb', target_size=(224, 224)) 
        
        # replaces above nightmare load_img / PIL issues
        # import imageio as iio
        # import imageio_freeimage

        """ import io
        buffer = io.BytesIO()
        uploaded_file.save(buffer) # this is an alternative to saving on AWS (/tmp/) which appears to be impossible to solve before I am dead from trying """
        #f = io.BytesIO(uploaded_file.stream) # should be similar to io.BytesIO(response.content)
        import cv2
        path = r'/tmp/00015_00010_00027.png'
        img = cv2.imread(path)  # cv2.imread not reading - None Type
        # test if file has really been saved
        """ a = os.listdir('/tmp')
        for x in a:
            print(x) """

        # test below image has been read, and its size
        # return flask.render_template("index.html", token=os.path.join('r', main.config['UPLOAD_FOLDER'], filename, 'EXTRA:', img, img.shape)) 

        img = cv2.resize(img, (224, 224))
        #img = iio.imread(filename, format='PNG') # or try again buffer ?
        #img = Image.fromarray(img).resize((224, 224))

        # below test specific image load from AWS - FINALLY THIS WORKS (AFTER ADDING RELATIVE PATH TO TF MODEL)!
        """ import requests
        import io
        import imageio.v3 as iio
        image_url = 'https://github.com/bw-cetech/lambda-docker-ecr-flask-dl/blob/bf3e205ff91ef7202cb067552d3685f33cf6e9b4/static/uploads/00015_00010_00027.png?raw=true'
        response = requests.get(image_url)
        response.raise_for_status()
        f = io.BytesIO(response.content)
        img = iio.imread(f, index=None) # instead of below
        # img = load_img(f, color_mode='rgb', target_size=(224, 224)) # DOESNT WORK but filename instead of f works
        img = Image.fromarray(img).resize((224, 224)) """

        os.chdir(currentPath) # change back

        img_array = img_to_array(img)

        model = Model()
        return flask.render_template("index.html", token=model.runInference(img_array))

    return redirect(url_for('index'))

def handler(event, context):
    return serverless_wsgi.handle_request(main, event, context)
