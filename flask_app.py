
# A very simple Flask Hello World app for you to get started with...

import os
from flask import Flask, render_template, request, redirect, url_for

UPLOAD_FOLDER = '/home/odygrd/guildstats/uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload')
def upload_file():
   return render_template('upload.html')

@app.route("/")
def index():
    return render_template("index.html")

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     uploaded_file = request.files['file']
#     if uploaded_file.filename != '':
#         uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename))
#     return redirect(url_for('index'))