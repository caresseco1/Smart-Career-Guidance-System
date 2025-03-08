from flask import Flask, render_template, request, jsonify
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
    return render_template("resume_review.html")  # Corrected template name

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

if __name__ == "__main__":
    app.run(debug=True)
