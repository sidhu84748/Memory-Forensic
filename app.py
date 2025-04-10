from flask import Flask, render_template, request, send_file
import subprocess
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
REPORTS_FOLDER = "reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

VOLATILITY_PATH = "python2 /usr/local/bin/vol1"

@app.route("/", methods=["GET", "POST"])
def index():
    profiles = []
    file_path = None
    analysis_output = ""

    if request.method == "POST":
        file = request.files["memory_file"]
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            cmd = f"{VOLATILITY_PATH} -f {file_path} imageinfo"
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            analysis_output = result.stdout

            for line in result.stdout.split("\n"):
                if "Suggested Profile(s)" in line:
                    profile_part = line.split(":")[1].strip()
                    profiles = [p.strip() for p in profile_part.split(",")]

    return render_template("index.html", profiles=profiles, file=file_path, analysis_output=analysis_output)

@app.route("/analyze", methods=["POST"])
def analyze():
    memory_file = request.form["file"]
    profile = request.form["profile"]
    plugin = request.form["plugin"]

    cmd = f"{VOLATILITY_PATH} -f {memory_file} --profile={profile} {plugin}"
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    print("Command Output:", result.stdout)  
    print("Command Error:", result.stderr)  

    # Save report as PDF with proper formatting
    report_path = os.path.join(REPORTS_FOLDER, f"{plugin}_report.pdf")
    doc = SimpleDocTemplate(report_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add Title
    elements.append(Paragraph("<b>Memory Analysis Report</b>", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Profile:</b> {profile}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Plugin:</b> {plugin}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # Preserve table format with monospaced font
    elements.append(Preformatted(result.stdout, styles["Code"]))

    # Build PDF
    doc.build(elements)

    return render_template("results.html", output=result.stdout, report_file=os.path.basename(report_path))

@app.route("/download_report")
def download_report():
    file_name = request.args.get("file")
    file_path = os.path.join(REPORTS_FOLDER, file_name)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

