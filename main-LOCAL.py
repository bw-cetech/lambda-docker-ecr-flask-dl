# Reference: https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask


import flask
from flask import request, redirect, flash, url_for, abort

# do we need dash ?
# import dash
# from dash.dependencies import Input, Output, State

import boto3
import io

import imghdr
import os

from python.dlmodel import Model

from werkzeug.utils import secure_filename

from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

#from tensorflow.keras.utils import load_img, img_to_array
from tensorflow.keras.preprocessing.image import load_img, img_to_array

app = flask.Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
app.config['UPLOAD_FOLDER'] = 'tmp/' # NB tmp/ wors locally, but AWS needs /tmp/ ?

def validate_image(stream):
    header = stream.read(1024)  # increased from 512 as bad request with large images
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format # (format if format != 'jpeg' else 'jpg') ASSUMES JPEG AND JPG FORMAT CAN BOTH BE UPLOADED

def write_image_to_s3(myImg, bucket, key, region_name='eu-west-1'):
    """Write an image array into S3 bucket

    Parameters
    ----------
    bucket: string
        Bucket name
    key : string
        Path in s3

    Returns
    -------
    None
    """
    s3 = boto3.resource('s3', region_name)
    bucket = s3.Bucket(bucket)
    object = bucket.Object(key)
    #file_stream = io.BytesIO()
    #im = Image.fromarray(img_array)
    #myImg.save(file_stream) # , format='png')
    object.put(Body=myImg, ContentType='image/png') # previously Body=file_stream.getvalue()
    
    #below does put the image in s3, but its not the correct format
    # s3 = boto3.client("s3", region_name=region_name)
    # s3.upload_fileobj(
    #         myImg,
    #         bucket,
    #         key #,
    #         # ExtraArgs={
    #         #     'ContentType': 'image/png'
    #         # }
    #     )
    
    
    # with open(myImg, 'rb') as src: # myImgPath ?
    #     client.put_object(
    #         ACL='public-read',
    #         Bucket=bucket,
    #         Key=key,
    #         Body=src
    #     )

    # with open('/tmp/'+ myImg, "rb") as f: # must read in binary mode 
    #     s3.upload_fileobj(f, bucket, key)
    
    

def read_image_from_s3(bucket, key, region_name='eu-west-1'):
    """Load image file from s3.

    Parameters
    ----------
    bucket: string
        Bucket name
    key : string
        Path in s3

    Returns
    -------
    np array
        Image array
    """
    
    s3 = boto3.resource('s3', region_name='eu-west-1')
    bucket = s3.Bucket(bucket)
    object = bucket.Object(key)
    response = object.get()
    file_stream = response['Body'].read()
    myImg = Image.open(io.BytesIO(file_stream))
    # return np.array(im)
    myImg = myImg.resize((224,224))
    myImg_array = img_to_array(myImg)
    return myImg_array

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    #print(uploaded_file.read())
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            abort(400)

        # currentPath = os.getcwd() 
        # os.chdir('tmp/')
        # savedImg = uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # savedImg = uploaded_file.save(filename)

        # img = load_img(os.path.join(app.config['UPLOAD_FOLDER'], filename),color_mode='rgb', target_size=(224, 224)) # works locally, but not on aws
        # img = load_img(filename, color_mode='rgb', target_size=(224, 224)) 

        # below test load from AWS
        # import requests
        # import io
        # import imageio.v3 as iio
        # image_url = 'https://github.com/bw-cetech/lambda-docker-ecr-flask-dl/blob/bf3e205ff91ef7202cb067552d3685f33cf6e9b4/static/uploads/00015_00010_00027.png?raw=true'
        # response = requests.get(image_url)
        # response.raise_for_status()
        # f = io.BytesIO(response.content)
        # img = iio.imread(f, index=None) # instead of below
        # # img = load_img(f, color_mode='rgb', target_size=(224, 224)) # DOESNT WORK but filename instead of f works
        # img = Image.fromarray(img).resize((224, 224))
        
        # os.chdir(currentPath) # change back

        # BELOW CODE BLOCK WORKS LOCALLY BUT NOT ON AWS
        # import imageio as iio
        # import io
        # buffer = io.BytesIO()
        # uploaded_file.save(buffer)
        # img = iio.imread(buffer, format='PNG')
        # img = Image.fromarray(img).resize((224, 224))

        # img_array = img_to_array(img)

        # model = Model()

        # return flask.render_template("index.html", token=model.runInference(img_array))
        
        myBucket = 'serverless-flask-contain-serverlessdeploymentbuck-o6ukv650uooh'
        myKey = 'serverless/serverless-flask-container/uplImg.png'
        write_image_to_s3(uploaded_file, myBucket, myKey, region_name='eu-west-1')

        dl_Array = read_image_from_s3(myBucket, myKey, region_name='eu-west-1')

        model = Model()

        return flask.render_template("index.html", token=model.runInference(dl_Array))

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 80))