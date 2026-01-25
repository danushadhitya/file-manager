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

@app.route('/',methods=['GET'])
def index():
    return "Hello World"

@app.route('/list',methods=['GET'])
def list():
    files=File.query.order_by(File.date_created).all()
    for f in files:
        print(f"ID:{f.id}, Name:{f.filename},Status:{f.status},Date:{f.date_created}")
    return "Found"

@app.route('/download/<int:id>',methods=['GET'])
def download(id):
    file=File.query.get_or_404(id)
    url=client.generate_presigned_url(
        "get_object",
        Params={"Bucket":S3_BUCKET,"Key":file.filename},
        ExpiresIn=300

    )
    print(url)
    return "Download"


@app.route('/upload',methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file=request.files['file']
        if file.filename == '':
            flash('No selected file')
        if file.filename:
            filename=secure_filename(file.filename)
            print(type(filename))
            client.upload_fileobj(file,Bucket=S3_BUCKET,Key=filename)
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