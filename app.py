from flask import Flask, render_template, request
import boto3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/objects', methods=['GET', 'POST'])
def list_objects():
    if request.method == 'POST':
        access_key = request.form['access_key']
        secret_access_key = request.form['secret_access_key']
        bucket_name = request.form['bucket_name']
        mfa_device_serial = request.form.get('mfa_device_serial')  # Get MFA device serial number
        mfa_token_code = request.form.get('mfa_token_code')  # Get MFA token code

        # Authenticate with AWS
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
            aws_session_token=None,  # Ensure session token is initially None
        )

        if mfa_device_serial and mfa_token_code:
            # Assume role with MFA
            sts_client = session.client('sts')
            try:
                response = sts_client.get_session_token(
                    DurationSeconds=3600,  # Adjust the duration as needed
                    SerialNumber=mfa_device_serial,
                    TokenCode=mfa_token_code
                )
                session = boto3.Session(
                    aws_access_key_id=response['Credentials']['AccessKeyId'],
                    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                    aws_session_token=response['Credentials']['SessionToken']
                )
            except Exception as e:
                return f"Error authenticating with MFA: {str(e)}"

        s3_client = session.client('s3')

        # List objects in S3 bucket
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            objects = response.get('Contents', [])
        except Exception as e:
            return f"Error listing objects: {str(e)}"

        return render_template('objects.html', objects=objects, bucket_name=bucket_name)

    else:
        # Handle GET request (e.g., redirect to index page)
        return render_template('index.html')

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
        logs = response['Body'].read().decode('utf-8', errors='replace')
    except Exception as e:
        logs = f"Error retrieving logs: {str(e)}"

    return render_template('logs.html', logs=logs, object_key=object_key)

if __name__ == '__main__':
    app.run(debug=True)
