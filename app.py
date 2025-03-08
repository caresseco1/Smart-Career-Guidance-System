from flask import Flask, jsonify, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import joblib
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import requests  # For making API requests

nltk.download("stopwords")
nltk.download("punkt")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'b9d16a3435e4015f7b8b01adba921491'  # Set secret key for session management

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///feedback.db"
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

# Function to fetch job listings from JSearch API
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

@app.route("/assessment")
def assessment():
    return render_template("assesment.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/job_market_analysis")
def job_market_analysis():
    return render_template("job_market_analysis.html")

@app.route("/resume_review")
def resume_review():
    return render_template("resume_review.html")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        resume_text = request.form.get("resume_text", "").strip()

        if not resume_text:
            return jsonify({"Error": "No resume text provided"}), 400

        # Clean and transform the text
        cleaned_text = clean_text(resume_text)
        resume_tfidf = vectorizer.transform([cleaned_text])

        # Predict job role
        predicted_role = model.predict(resume_tfidf)[0]

        # Fetch job listings for the predicted role in India
        job_listings = fetch_job_listings(predicted_role, country="in")

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
            "Predicted Job Role": predicted_role,
            "Jobs": jobs
        })

    except Exception as e:
        return jsonify({"Error": str(e)}), 500

# Define Feedback Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # Save feedback to database
    new_feedback = Feedback(name=name, email=email, message=message)
    db.session.add(new_feedback)
    db.session.commit()

    # Send Email Notification
    msg = Message("New Feedback Received", sender=email, recipients=["your-email@gmail.com"])
    msg.body = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"
    mail.send(msg)

    flash('Your message has been received and emailed successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/view_feedback')
def view_feedback():
    feedbacks = Feedback.query.all()
    return render_template("feedback.html", feedbacks=feedbacks)

if __name__ == "__main__":
    app.run(debug=True)
