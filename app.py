import os
import boto3
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/mnt/c/Users/danus/Documents/file-manager'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///files.db"

db= SQLAlchemy(app)
endpoint_url="http://localhost:4566"
client=boto3.client("s3",endpoint_url=endpoint_url)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename= db.Column(db.String(30),nullable=False)
    status= db.Column(db.String(20),nullable=False)
    date_created= db.Column(db.DateTime,default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/',methods=['GET'])
def index():
    return "Hello World"

@app.route('/upload',methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file=request.files['file']
        if file.filename == '':
            flash('No selected file')
        if file.filename:
            filename=secure_filename(file.filename)
            print(type(filename))
            client.upload_fileobj(file,Bucket='uploadedfiles',Key=filename)
            file=File(filename=filename,status="UPLOADED")
            db.session.add(file)
            db.session.commit()
            return jsonify({
                "message":"File uploaded successfully"
            }),200


if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=8000)