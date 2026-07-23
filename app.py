import os
from datetime import datetime
import markdown
from dotenv import load_dotenv
from google import genai
from pathlib import Path
from flask import Flask, render_template, request
from pypdf import PdfReader
from werkzeug.utils import secure_filename

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
def analyze_resume(resume_text, job_description):

    prompt = f"""
You are an expert ATS (Applicant Tracking System).

Resume:
{resume_text}

Job Description:
{job_description}

Analyze the resume and provide:

1. ATS Match Percentage
2. Missing Skills
3. Strengths
4. Weaknesses
5. Suggestions for Improvement
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        analysis = markdown.markdown(
            response.text,
            extensions=["extra", "nl2br"]
        )

        return analysis

    except Exception as e:

        print("Gemini Error:", e)

        return "❌ Unable to analyze the resume at the moment. Please try again later."

app = Flask(__name__)

UPLOAD_FOLDER = Path("uploads")

UPLOAD_FOLDER.mkdir(exist_ok=True)

def extract_pdf_text(file_path):

    try:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return text

    except Exception as e:

        print("PDF Error:", e)

        return None

@app.route("/", methods=["GET", "POST"])
def home():

    message = None
    resume_text = None
    job_description = ""
    analysis_result = None

    if request.method == "POST":

        resume_file = request.files.get("resume")

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        if not resume_file or resume_file.filename == "":

            message = "Please upload a resume."

        elif not resume_file.filename.lower().endswith(".pdf"):

            message = "Please upload only a PDF file."

        elif not job_description:

            message = "Please enter a job description."

        else:

            filename = secure_filename(resume_file.filename)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            filename = f"{timestamp}_{filename}"

            file_path = UPLOAD_FOLDER / filename

            resume_file.save(file_path)

            resume_text = extract_pdf_text(file_path)

            if not resume_text:

                message = "Could not read text from this PDF."

            else:

                analysis_result = analyze_resume(
                    resume_text,
                    job_description
                )

                print(analysis_result)

                message = "Resume analyzed successfully."

    return render_template(
        "index.html",
        message=message,
        resume_text=resume_text,
        job_description=job_description,
        analysis_result=analysis_result
    )


if __name__ == "__main__":
    app.run(debug=True)