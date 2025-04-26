import http
import os
import bcrypt
from flask import Flask, json, jsonify, render_template, request, flash, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import joblib
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import requests

from train_model import suggest_jobs  # For making API requests

import os

nltk.download("stopwords")
nltk.download("punkt")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'b9d16a3435e4015f7b8b01adba921491'  # Set secret key for session management

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://caresse:CareerGo#2024@localhost/careergo'  # Temporarily using hardcoded credentials for testing
db = SQLAlchemy(app)

# Configure Flask-Mail for email notifications
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "caressecorreia@gmail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "xonq obnu rnnj efqs"  # Use App Password if using Gmail

mail = Mail(app)

# Load trained model & vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# JSearch API Configuration
JSEARCH_API_KEY = "b61bbb41dfmsh6854e2ea484a585p12bd6ejsnd9aea51c469a"  # Replace with your JSearch API key
JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"

# Function to clean and preprocess resume text
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    return " ".join(tokens)

# Function to suggest job roles based on resume text and skills using decision_function scores
def suggest_jobs(resume_text, skills="", score_threshold=0.0, top_n=5):
    combined_text = resume_text + " " + skills
    cleaned_text = clean_text(combined_text)
    resume_tfidf = vectorizer.transform([cleaned_text])
    scores = model.decision_function(resume_tfidf)  # Get scores for all classes
    scores = scores.flatten()
    classes = model.classes_
    # Filter job roles with scores above threshold
    good_matches = [(job, score) for job, score in zip(classes, scores) if score > score_threshold]
    # Sort by score descending
    good_matches.sort(key=lambda x: x[1], reverse=True)
    # Return only top_n job roles
    return [job for job, score in good_matches[:top_n]]

def fetch_job_listings(job_title, country="in"):
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": job_title,
        "page": "1",
        "num_pages": "3",
        "country": country
    }
    response = requests.get(JSEARCH_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        return []

@app.route("/")
def home():
    return render_template("index.html")

# Removed /ats_score route and handler

@app.route("/assessment")
def assessment():
    return render_template("assesment.html")

@app.route("/resume_upload", methods=["GET"])
def resume_upload():
    return render_template("resume_upload.html")

@app.route("/check_resume", methods=["POST"])
def check_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        # Save file temporarily
        filename = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filename)
        
        # Get job description
        job_description = request.form.get('job_description', '')
        
        # Removed ATS checker usage
        
        # Return error since ATS checker removed
        return jsonify({"error": "ATS Score Checker functionality removed"}), 501
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/resume_review", methods=["GET", "POST"])
def resume_review():
    if request.method == "POST":
        # Handle file upload
        if 'resume_file' in request.files:
            file = request.files['resume_file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            if file:
                # Save file temporarily
                filename = os.path.join('uploads', file.filename)
                os.makedirs('uploads', exist_ok=True)
                file.save(filename)
                
                # Get job description if provided
                job_description = request.form.get('job_description', '')
                
                # Removed ATS checker usage
                # Return error since ATS checker removed
                flash('ATS Score Checker functionality removed')
                return redirect(request.url)
        
        # Handle text input
        elif 'resume_text' in request.form:
            resume_text = request.form.get('resume_text', '').strip()
            job_description = request.form.get('job_description', '')
            
            if not resume_text:
                flash('No resume text provided')
                return redirect(request.url)
            
            # Removed ATS checker usage
            flash('ATS Score Checker functionality removed')
            return redirect(request.url)
    
    return render_template("resume_review.html")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/get_company_insights", methods=["GET"])
def get_company_insights():
    company_username = request.args.get("username", "amazon")  # Default to Amazon
    url = "https://linkedin-data-api.p.rapidapi.com/get-company-insights"
    querystring = {"username": company_username}

    headers = {
        "x-rapidapi-key": "YOUR_RAPIDAPI_KEY",  # Replace with your actual API key
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        return jsonify(response.json())  # Return JSON response
    else:
        return jsonify({"Error": f"Error {response.status_code}: {response.text}"}), response.status_code

@app.route("/predict", methods=["POST"])
def predict():
    try:
        resume_text = request.form.get("resume_text", "").strip()
        skills = request.form.get("skills", "").strip()

        if not resume_text:
            return jsonify({"Error": "No resume text provided"}), 400

        # Suggest job roles based on the combined resume text and skills
        suggested_jobs = suggest_jobs(resume_text, skills, score_threshold=0.0, top_n=5)  # Get top 5 good match job roles

        # Fetch job listings for the predicted roles in India
        if not suggested_jobs:
            return jsonify({"Error": "No job roles suggested based on the resume text and skills."}), 404

        job_listings = []
        for job in suggested_jobs:
            listings = fetch_job_listings(job, country="in")  # Use each suggested job
            job_listings.extend(listings)  # Add all listings to the job_listings list

        if not job_listings:
            return jsonify({"Error": "No job listings found for the suggested job role."}), 404

        # Extract job details (title, company, location, apply link)
        jobs = []
        for job in job_listings:
            jobs.append({
                "title": job.get("job_title", "N/A"),
                "company": job.get("employer_name", "N/A"),
                "location": job.get("job_location", "N/A"),
                "apply_link": job.get("job_apply_link", "#")
            })

        return jsonify({
            "Suggested Job Roles": suggested_jobs,
            "Jobs": jobs
        })

    except Exception as e:
        return jsonify({"Error": str(e)}), 500

# Define User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# **Signup Route**
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    password = data.get('password')

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': 'Email already registered'}), 400

    # Hash Password and Save User
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=first_name + " " + last_name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Registration successful!'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({'status': 'success', 'message': 'Login successful'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

# **Logout Route**
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/view_feedback')
def view_feedback():
    feedbacks = Feedback.query.all()
    return render_template("feedback.html", feedbacks=feedbacks)

if __name__ == "__main__":
    app.run(debug=True)