from flask import Flask, render_template, request, redirect, session as flask_session
import boto3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management, can also be a static string

@app.route('/')
def index():
    flask_session.permanent = True  # Ensures that the session is permanent (i.e., not cleared when the browser closes)
    return render_template('index.html')

@app.route('/objects', methods=['GET', 'POST'])
def list_objects():
    if request.method == 'POST':
        access_key = request.form['access_key']
        secret_access_key = request.form['secret_access_key']
        bucket_name = request.form['bucket_name']
        region = request.form['region']
        mfa_device_serial = request.form.get('mfa_device_serial')
        mfa_token_code = request.form.get('mfa_token_code')

        # Store credentials and region in the Flask session
        flask_session['access_key'] = access_key
        flask_session['secret_access_key'] = secret_access_key
        flask_session['bucket_name'] = bucket_name
        flask_session['region'] = region

        if mfa_device_serial and mfa_token_code:
            flask_session['mfa_device_serial'] = mfa_device_serial
            flask_session['mfa_token_code'] = mfa_token_code

        return redirect('/show_objects')

    else:
        return render_template('index.html')

@app.route('/show_objects')
def show_objects():
    # Retrieve credentials from the Flask session
    access_key = flask_session.get('access_key')
    secret_access_key = flask_session.get('secret_access_key')
    bucket_name = flask_session.get('bucket_name')
    region = flask_session.get('region')
    mfa_device_serial = flask_session.get('mfa_device_serial')
    mfa_token_code = flask_session.get('mfa_token_code')

    if not all([access_key, secret_access_key, bucket_name, region]):
        return redirect('/')

    # Authenticate with AWS using session data
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )

    if mfa_device_serial and mfa_token_code:
        sts_client = session.client('sts')
        try:
            response = sts_client.get_session_token(
                DurationSeconds=3600,
                SerialNumber=mfa_device_serial,
                TokenCode=mfa_token_code
            )
            session = boto3.Session(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken'],
                region_name=region
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

@app.route('/logs')
def show_logs():
    # Retrieve credentials from session instead of URL parameters
    access_key = flask_session.get('access_key')
    secret_access_key = flask_session.get('secret_access_key')
    bucket_name = flask_session.get('bucket_name')
    object_key = request.args.get('object_key')
    region = flask_session.get('region')

    if not all([access_key, secret_access_key, bucket_name, object_key, region]):
        return redirect('/')

    # Create session with AWS
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )
    
    s3_client = session.client('s3')

    try:
        # Get object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content_type = response['ContentType']

        if content_type.startswith('text') or content_type == 'application/json':
            logs = response['Body'].read().decode('utf-8')
        else:
            logs = "This object format is not supported for display."

    except Exception as e:
        return f"Error fetching object: {str(e)}"

    return render_template('logs.html', logs=logs, object_key=object_key)

if __name__ == '__main__':
    app.run(debug=True)
