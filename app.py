import os
import boto3
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET= os.getenv("S3_BUCKET_NAME")

app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///files.db"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db= SQLAlchemy(app)
endpoint_url="http://localhost:4566"
client=boto3.client("s3",endpoint_url=endpoint_url,aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename= db.Column(db.String(30),nullable=False)
    status= db.Column(db.String(20),nullable=False)
    date_created= db.Column(db.DateTime,default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.errorhandler(413)
def request_entity_too_large(error):
    return {"Error": "File is too large. Maximum allowed size is 16MB"}, 413

@app.route('/',methods=['GET'])
def index():
    return "Hello World"

@app.route('/list',methods=['GET'])
def list():
    if request.method == 'GET':
        try:
            files=File.query.order_by(File.date_created).all()
            result=[
                {
                    "id":f.id,
                    "flename":f.filename,
                    "status":f.status,
                    "date_created":f.date_created
                }
                for f in files
            ]
            return jsonify(result),200
        except Exception as e:
            return {"Error":str(e)},500


@app.route('/download/<int:id>',methods=['GET'])
def download(id):
    if request.method == 'GET':
        try:
            file=File.query.get_or_404(id)
            url=client.generate_presigned_url(
                "get_object",
                Params={"Bucket":S3_BUCKET,"Key":file.filename},
                ExpiresIn=300

            )
            return {"Download URL":url},200
        
        except Exception as e:
            return {"Error":str(e)},500


@app.route('/delete/<int:id>',methods=['DELETE','POST'])
def delete(id):
    if request.method == 'DELETE':
        try:
            file=File.query.get_or_404(id)
            deleteobj=client.delete_object(Bucket=S3_BUCKET,Key=file.filename)
            file.status="DELETED"
            db.session.commit()
            return {"Message":f"{file.filename} deleted from S3"},200
        except Exception as e:
            return {"Error":str(e)},500

@app.route('/upload',methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file=request.files['file']
        if file.filename == '':
            return {"Error":"Bad Request-No file provided / invalid payload"},400
        if file.filename:
            filename=secure_filename(file.filename)
            try:
                client.upload_fileobj(file,Bucket=S3_BUCKET,Key=filename)
                file=File(filename=filename,status="UPLOADED")
                db.session.add(file)
                db.session.commit()
                return {"Message":f"{filename} uploaded successfully to S3"},201
            except Exception as e:
                return {"Error":str(e)},500



if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=8000)