from apps.home import blueprint
from flask import render_template, request, request, current_app, send_from_directory, flash, redirect, url_for, jsonify
from flask_login import login_required
from apps.authentication.routes import current_user, log_user_action
from jinja2 import TemplateNotFound
import os

from apps import db
from werkzeug.utils import secure_filename

import subprocess
import shutil

from moviepy.editor import VideoFileClip
from pydub import AudioSegment


@blueprint.route('/index')
@login_required
def index():

    if current_user.is_authenticated:
        username = current_user.username
        log_user_action(username, "in Home Page.")

    # Call the gallery function to get videos
    video_folder = 'apps/static/videos'  # Update the path here
    videos = [f for f in os.listdir(video_folder) if f.endswith('.mp4')]  # Get all mp4 videos
    print("Videos found:", videos)  # Debug print

    return render_template('home/index.html', segment='index', videos=videos)


@blueprint.route('/<template>', methods=['GET', 'POST'])
@login_required
def route_template(template):
    try:

        if not template.endswith('.html'):
            template += '.html'

        if current_user.is_authenticated:
            username = current_user.username
            log_user_action(username, "in " + template)

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print(f"An error occurred: {e}")  # Debug print
        return render_template('home/page-500.html'), 500
    

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
    

@blueprint.route('/dashboard')
@login_required
def dashboard():
    username = current_user.username  # Get the username from the session
    return render_template('dashboard.html', username=username)

@blueprint.route('/api/media/<username>', methods=['GET'])
def get_media(username):
    base_path = f'apps/data_user/{username}'
    
    # Define paths
    video_path = os.path.join(base_path, 'video')
    audio_path = os.path.join(base_path, 'audio')
    output_path = os.path.join(base_path, 'output')

    # Prepare response data
    media_data = {
        'video': [],
        'audio': [],
        'output': []
    }

    # Load video files
    if os.path.exists(video_path):
        media_data['video'] = [
            {'name': file, 'file': f"{video_path}/{file}"}
            for file in os.listdir(video_path) if file.endswith(('.mp4', '.mkv'))
        ]

    # Load audio files
    if os.path.exists(audio_path):
        media_data['audio'] = [
            {'name': file, 'file': f"{audio_path}/{file}"}
            for file in os.listdir(audio_path) if file.endswith(('.mp3', '.wav'))
        ]

    # Load output files
    if os.path.exists(output_path):
        media_data['output'] = [
            {'name': file, 'file': f"{output_path}/{file}"}
            for file in os.listdir(output_path) if file.endswith(('.mp4', '.mkv'))
        ]

    return jsonify(media_data)




@blueprint.route('/upload-profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    if 'profile_image' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page

    file = request.files['profile_image']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page

    if file and allowed_image(file.filename):
        username = current_user.username
        profile_dir = os.path.join(current_app.config['USER_DATA_ROOT'], username, 'profile', 'dp')

        try:
            os.makedirs(profile_dir, exist_ok=True)
        except Exception as e:
            flash(f"Error creating directory: {str(e)}", "danger")
            return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page

        file_path = os.path.join(profile_dir, current_app.config['PROFILE_IMAGE_NAME'])

        try:
            file.save(file_path)
        except Exception as e:
            flash(f"Error saving file: {str(e)}", "danger")
            return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page

        log_user_action(username, "profile picture is updated.")
        flash("Profile image uploaded successfully", "success")
        return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page

    flash("Invalid file type", "danger")
    return redirect(url_for('home_blueprint.route_template', template='user'))  # Redirect to user page



def allowed_image(filename):
    allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@blueprint.route('/user_data/<username>/profile/dp/<filename>')
@login_required
def profile_image(username, filename):
    # Construct the full path to the user's profile directory
    profile_dir = os.path.join(current_app.config['USER_DATA_ROOT'], username, 'profile', 'dp')
    
    # Check if the directory and file exist
    if not os.path.exists(os.path.join(profile_dir, filename)):
        return "File not found", 404

    # Serve the file
    return send_from_directory(profile_dir, filename)


# upload Video & Audio

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_user_directory(username, filetype):
    base_dir = current_app.config['UPLOAD_FOLDER']
    if filetype == 'video':
        return os.path.join(base_dir, username, 'video')
    elif filetype == 'audio':
        return os.path.join(base_dir, username, 'audio')

def get_temp_directory(username):
    base_dir = current_app.config['UPLOAD_FOLDER']
    return os.path.join(base_dir, username, 'temp')

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def convert_to_mp4(input_path, output_path):
    try:
        # Convert video to mp4
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, codec='libx264')
        clip.close()
    except Exception as e:
        print(f"Error converting video: {e}")

def convert_to_mp3(input_path, output_path):
    try:
        # Convert audio to mp3
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format='mp3')
    except Exception as e:
        print(f"Error converting audio: {e}")

@blueprint.route('/upload-video', methods=['POST'])
@login_required
def upload_video():
    username = current_user.username

    if 'video' not in request.files:
        flash('No video file part', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    file = request.files['video']

    if file.filename == '':
        flash('No selected video file', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    if file and allowed_file(file.filename, current_app.config['ALLOWED_VIDEO_EXTENSIONS']):
        filename = secure_filename(file.filename)
        user_dir = get_user_directory(username, 'video')
        temp_dir = get_temp_directory(username)
        ensure_directory_exists(user_dir)
        ensure_directory_exists(temp_dir)

        # Save the original video
        original_path = os.path.join(user_dir, filename)
        try:
            file.save(original_path)
        except Exception as e:
            flash('Error saving video file', 'danger')
            print(f"Error saving video file: {e}")
            return redirect(url_for('home_blueprint.route_template', template='lipsync'))

        # Temporary file path for processing
        temp_video_path = os.path.join(temp_dir, 'temp_uploaded_video.mp4')

        # If the temporary file already exists, remove it
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

        # Convert to .mp4 if necessary
        if not filename.lower().endswith('.mp4'):
            convert_to_mp4(original_path, temp_video_path)
        else:
            # Copy the original video to the temp folder instead of renaming
            shutil.copy(original_path, temp_video_path)

        log_user_action(username, "uploaded and converted video file.")
        flash('Video uploaded and converted successfully', 'success')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))
    else:
        flash('Invalid video file type', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

@blueprint.route('/upload-audio', methods=['POST'])
@login_required
def upload_audio():
    username = current_user.username

    if 'audio' not in request.files:
        flash('No audio file part', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    file = request.files['audio']

    if file.filename == '':
        flash('No selected audio file', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    if file and allowed_file(file.filename, current_app.config['ALLOWED_AUDIO_EXTENSIONS']):
        filename = secure_filename(file.filename)
        user_dir = get_user_directory(username, 'audio')
        temp_dir = get_temp_directory(username)
        ensure_directory_exists(user_dir)
        ensure_directory_exists(temp_dir)

        original_path = os.path.join(user_dir, filename)
        try:
            # Save the original audio
            file.save(original_path)
        except Exception as e:
            flash('Error saving audio file', 'danger')
            print(f"Error saving audio file: {e}")
            return redirect(url_for('home_blueprint.route_template', template='lipsync'))

        # Temporary file paths for processing
        temp_audio_path = os.path.join(temp_dir, 'temp_uploaded_audio.mp3')

        # Remove the temporary file if it already exists
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        # Convert to .mp3 if necessary
        if not filename.lower().endswith('.mp3'):
            convert_to_mp3(original_path, temp_audio_path)
        else:
            # Copy the original video to the temp folder instead of renaming
            shutil.copy(original_path, temp_audio_path)

        log_user_action(username, "uploaded and converted audio file.")
        flash('Audio uploaded and converted successfully', 'success')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    flash('Invalid audio file type', 'danger')
    return redirect(url_for('home_blueprint.route_template', template='lipsync'))


@blueprint.route('/process', methods=['POST'])
@login_required
def process_lipsync():
    username = current_user.username
    log_user_action(username, "in process page and process is started.")

    # Retrieve form data
    start_time = request.form.get('start-time', type=int)
    end_time = request.form.get('end-time', type=int)
    padding_top = request.form.get('padding-top', type=int, default=0)
    padding_right = request.form.get('padding-right', type=int, default=0)
    padding_left = request.form.get('padding-left', type=int, default=0)
    padding_bottom = request.form.get('padding-bottom', type=int, default=0)
    output_filename = request.form.get('output-filename')
    model_type = request.form.get('model-type')

    # Define paths for video, audio, and output
    video_path = f"apps/user_data/{username}/temp/temp_uploaded_video.mp4"
    audio_path = f"apps/user_data/{username}/temp/temp_uploaded_audio.mp3"
    output_path = os.path.join(f"apps/user_data/{username}/output", output_filename + '.mp4')

    # Placeholder for WAV2Lip processing logic


    # Check if the video file exists
    if not os.path.exists(video_path):
        flash("Video file does not exist.", "danger")
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    # Check if the audio file exists
    if not os.path.exists(audio_path):
        flash("Audio file does not exist.", "danger")
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

    # Call the WAV2Lip processing function
    success = process_wav2lip(video_path, audio_path, start_time, end_time, 
                              (padding_top, padding_right, padding_left, padding_bottom), 
                              model_type, output_path)

    if success:
        flash('File processing completed successfully!', 'success')
        return redirect(url_for('home_blueprint.preview', output_video_url=output_path))
    else:
        flash('Error occurred while processing the files. Please try again.', 'danger')
        return redirect(url_for('home_blueprint.route_template', template='lipsync'))

def process_wav2lip(video_path, audio_path, start_time, end_time, padding, model_type, output_path):
    checkpoint_path = 'apps/Wav2Lip-FYP-main/checkpoints/wav2lip.pth' if model_type == 'normal' else 'apps/Wav2Lip-FYP-main/checkpoints/wav2lip_gan.pth'
    wav2lip_path = "apps/Wav2Lip-FYP-main"

    trimmed_video_path = trim_media(video_path, start_time, end_time, padding, 'video')
    trimmed_audio_path = trim_media(audio_path, start_time, end_time, padding, 'audio')

    command = [
        'python', os.path.join(wav2lip_path, 'inference.py'),
        '--checkpoint_path', checkpoint_path,
        '--face', trimmed_video_path,
        '--audio', trimmed_audio_path,
        '--outfile', output_path
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        flash(f"WAV2Lip Output: {result.stdout}", "success")
        return True
    except subprocess.CalledProcessError as e:
        flash(f"Error occurred: {e.stderr}", "danger")
        return False

def trim_media(media_path, start_time, end_time, padding, media_type):
    output_trimmed_path = f"{os.path.splitext(media_path)[0]}_trimmed{os.path.splitext(media_path)[1]}"

    if start_time is None or end_time is None:
        return media_path

    start_time = max(0, start_time - padding[0])
    duration = max(0, end_time - start_time + padding[1])

    if duration <= 0:
        flash("Invalid duration for trimming, returning the original media path.", "danger")
        return media_path

    if media_type == 'video':
        command = [
            'ffmpeg', '-ss', str(start_time), '-i', media_path, '-t', str(duration),
            '-c:v', 'libx264', '-c:a', 'aac', '-y', output_trimmed_path
        ]
    elif media_type == 'audio':
        command = [
            'ffmpeg', '-ss', str(start_time), '-i', media_path, '-t', str(duration),
            '-c:a', 'aac', '-y', output_trimmed_path
        ]
    else:
        flash("Unsupported media type", "danger")
        return media_path

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        flash(f"Trim media output: {result.stdout}", "success")
        return output_trimmed_path
    except subprocess.CalledProcessError as e:
        flash(f"Error trimming media: {e.stderr}", "danger")
        return media_path