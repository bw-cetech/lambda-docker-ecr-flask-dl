import serverless_wsgi

import flask
from flask import request, redirect, flash, url_for, abort

import dash
from dash.dependencies import Input, Output, State

import imghdr
import os

from python.dlmodel import Model

from werkzeug.utils import secure_filename

import PIL

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

        # refactored routine below to convert image to array before passing to inference module
        savedImg = uploaded_file.save(filename)
        img = PIL.Image.open(filename) # to address PIL errors
        img_resized = img.resize((224,224))
        img_array = img_to_array(img_resized) # originally img_to_array(img) using image.load_img above
        model = Model()
        return flask.render_template("index.html", token=model.runInference(img_array))

    return redirect(url_for('index'))

def handler(event, context):
    return serverless_wsgi.handle_request(main, event, context)
