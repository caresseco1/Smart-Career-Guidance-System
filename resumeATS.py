from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to get Gemini output
def get_gemini_output(pdf_text, prompt):
    response = model.generate_content([pdf_text, prompt])
    return response.text

# Function to read PDF
def read_pdf(filepath):
    pdf_reader = PdfReader(filepath)
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text()
    return pdf_text

@app.route('/ats', methods=['GET', 'POST'])
def ats():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        job_description = request.form.get('job_description', '')
        analysis_option = request.form.get('analysis_option', 'Quick Scan')
        
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                pdf_text = read_pdf(filepath)
                
                if analysis_option == "Quick Scan":
                    prompt = f"""
                    You are ResumeChecker, an expert in resume analysis. Provide a quick scan of the following resume:
                    
                    1. Identify the most suitable profession for this resume.
                    2. List 3 key strengths of the resume.
                    3. Suggest 2 quick improvements.
                    4. Give an overall ATS score out of 100.
                    
                    Resume text: {pdf_text}
                    Job description (if provided): {job_description}
                    """
                elif analysis_option == "Detailed Analysis":
                    prompt = f"""
                    You are ResumeChecker, an expert in resume analysis. Provide a detailed analysis of the following resume:
                    
                    1. Identify the most suitable profession for this resume.
                    2. List 5 strengths of the resume.
                    3. Suggest 3-5 areas for improvement with specific recommendations.
                    4. Rate the following aspects out of 10: Impact, Brevity, Style, Structure, Skills.
                    5. Provide a brief review of each major section (e.g., Summary, Experience, Education).
                    6. Give an overall ATS score out of 100 with a breakdown of the scoring.
                    
                    Resume text: {pdf_text}
                    Job description (if provided): {job_description}
                    """
                else:  # ATS Optimization
                    prompt = f"""
                    You are ResumeChecker, an expert in ATS optimization. Analyze the following resume and provide optimization suggestions:
                    
                    1. Identify keywords from the job description that should be included in the resume.
                    2. Suggest reformatting or restructuring to improve ATS readability.
                    3. Recommend changes to improve keyword density without keyword stuffing.
                    4. Provide 3-5 bullet points on how to tailor this resume for the specific job description.
                    5. Give an ATS compatibility score out of 100 and explain how to improve it.
                    
                    Resume text: {pdf_text}
                    Job description: {job_description}
                    """
                
                response = get_gemini_output(pdf_text, prompt)
                
                # Clean up the uploaded file
                os.remove(filepath)
                
                return render_template('results.html', 
                                     response=response,
                                     job_description=job_description,
                                     analysis_option=analysis_option)
            
            except Exception as e:
                os.remove(filepath)
                return render_template('error.html', error=str(e))
    
    return render_template('ats.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    if request.method == 'POST':
        user_question = request.form.get('user_question', '')
        pdf_text = request.form.get('pdf_text', '')
        previous_analysis = request.form.get('previous_analysis', '')
        
        if user_question and pdf_text:
            chat_prompt = f"""
            Based on the resume and analysis above, answer the following question:
            {user_question}
            
            Resume text: {pdf_text}
            Previous analysis: {previous_analysis}
            """
            chat_response = get_gemini_output(pdf_text, chat_prompt)
            return render_template('chat_response.html', chat_response=chat_response)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)