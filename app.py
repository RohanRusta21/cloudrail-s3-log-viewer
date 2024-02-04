from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
from dotenv import load_dotenv
import boto3

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_GEMINI_KEY"))
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/objects', methods=['POST'])
def list_objects():
    access_key = request.form['access_key']
    secret_access_key = request.form['secret_access_key']
    bucket_name = request.form['bucket_name']

    # Authenticate with AWS
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key
    )
    s3_client = session.client('s3')

    # List objects in S3 bucket
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        objects = response.get('Contents', [])
    except Exception as e:
        return f"Error listing objects: {str(e)}"

    return render_template('objects.html', objects=objects, bucket_name=bucket_name)

@app.route('/logs', methods=['POST', 'GET'])
def display_logs():
    access_key = request.form['access_key'] if request.method == 'POST' else request.args.get('access_key')
    secret_access_key = request.form['secret_access_key'] if request.method == 'POST' else request.args.get('secret_access_key')
    bucket_name = request.form['bucket_name'] if request.method == 'POST' else request.args.get('bucket_name')
    object_key = request.form['object_key'] if request.method == 'POST' else request.args.get('object_key')

    # Authenticate with AWS
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key
    )
    s3_client = session.client('s3')

    # Retrieve logs from S3 object
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        logs = response['Body'].read().decode('utf-8')
    except Exception as e:
        logs = f"Error retrieving logs: {str(e)}"

    return render_template('logs.html', logs=logs, object_key=object_key)

@app.route('/generate', methods=['POST'])
def generate_content():
    prompt = request.json['prompt']

    try:
        response = model.generate_content(prompt)
        return jsonify({'message': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
