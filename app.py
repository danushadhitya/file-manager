import os
import boto3
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps


AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET= os.getenv("S3_BUCKET_NAME")
API_KEY=os.getenv("API_KEY")


app=Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///files.db"
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@db:5432/"
    f"{os.getenv('POSTGRES_DB')}"
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db= SQLAlchemy(app)
endpoint_url=os.getenv('AWS_ENDPOINT_URL')
client=boto3.client("s3",endpoint_url=endpoint_url,aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)

def check_auth(f):
    @wraps(f)
    def func(*args,**kwargs):
        auth_header=request.headers.get('X-API-KEY')
        if not auth_header or auth_header != API_KEY:
            return jsonify({"Error":"Unauthorized"}),401
        return f(*args,**kwargs)
    return func        

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename= db.Column(db.String(60),nullable=False)
    status= db.Column(db.String(20),nullable=False)
    date_created= db.Column(db.DateTime,default=datetime.utcnow)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"Error": "File is too large. Maximum allowed size is 16MB"}), 413

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/list',methods=['GET'])
@check_auth
def list():
    if request.method == 'GET':
        page=request.args.get('page',default=1,type=int)
        per_page=request.args.get('per_page',default=10,type=int)
        if page<1:
            page=1
        if per_page < 1 or per_page > 20:
            per_page=10    
        try:
            subset=File.query.order_by(File.date_created).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            result=[
                {
                    "id":f.id,
                    "filename":f.filename,
                    "status":f.status,
                    "date_created":f.date_created
                }
                for f in subset.items
            ]
            return jsonify({
                "files":result,
                "pagination":{
                    "page":subset.page,
                    "per_page":subset.per_page,
                    "pages":subset.pages,
                    "has_prev":subset.has_prev,
                    "has_next":subset.has_next
                }
            }),200
        except Exception as e:
            return jsonify({"Error":str(e)}),500


@app.route('/api/download/<int:id>',methods=['GET'])
@check_auth
def download(id):
    if request.method == 'GET':
        try:
            file=File.query.get_or_404(id)
            url=client.generate_presigned_url(
                "get_object",
                Params={"Bucket":S3_BUCKET,"Key":file.filename},
                ExpiresIn=300

            )
            url = url.replace('http://localstack:4566', 'http://localhost:4566')
            return jsonify({"URL":url}),200
        
        except Exception as e:
            return jsonify({"Error":str(e)}),500


@app.route('/api/delete/<int:id>',methods=['DELETE','POST'])
@check_auth
def delete(id):
    if request.method == 'DELETE':
        try:
            file=File.query.get_or_404(id)
            deleteobj=client.delete_object(Bucket=S3_BUCKET,Key=file.filename)
            file.status="DELETED"
            db.session.commit()
            return jsonify({"Message":f"{file.filename} deleted from S3"}),200
        except Exception as e:
            return jsonify({"Error":str(e)}),500

@app.route('/api/upload',methods=['POST'])
@check_auth
def upload_file():
    if request.method == 'POST':
        file=request.files['file']
        if file.filename == '':
            return jsonify({"Error":"Bad Request-No file provided / invalid payload"}),400
        if file.filename:
            filename=secure_filename(file.filename)
            try:
                client.upload_fileobj(file,Bucket=S3_BUCKET,Key=filename)
                file=File(filename=filename,status="UPLOADED")
                db.session.add(file)
                db.session.commit()
                return jsonify({"Message":f"{filename} uploaded successfully to S3"}),201
            except Exception as e:
                return jsonify({"Error":str(e)}),500



if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=8000)