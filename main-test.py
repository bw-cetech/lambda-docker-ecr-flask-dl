import serverless_wsgi

import flask
from flask import request, redirect, flash, url_for, abort

import dash
from dash.dependencies import Input, Output, State

import imghdr
import os

from python.dlmodel import Model

from werkzeug.utils import secure_filename

main = flask.Flask(__name__)
main.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 # increased as bad request with large images
main.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
main.config['UPLOAD_PATH'] = 'static/uploads'

def validate_image(stream):
    header = stream.read(1024)  # increased from 512 as bad request with large images
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format # (format if format != 'jpeg' else 'jpg') ASSUMES JPEG AND JPG FORMAT CAN BOTH BE UPLOADED

@main.route('/')
def index():
    files = os.listdir(main.config['UPLOAD_PATH'])
    return flask.render_template('index.html', files=files)

@main.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in main.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            abort(400)
        uploaded_file.save(os.path.join(main.config['UPLOAD_PATH'], filename))
        model = Model()
        return os.path.join(main.config['UPLOAD_PATH'], filename) # for testing
        return flask.render_template("index.html", token=model.runInference(filename))
    return redirect(url_for('index'))

@main.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(main.config['UPLOAD_PATH'], filename)

def handler(event, context):
    return serverless_wsgi.handle_request(main, event, context)

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 80))
