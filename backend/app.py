import os
import zipfile
import io
from flask import Flask, request, render_template, send_file, send_from_directory
from Automation import take_screenshot
from generate_reports import generate_report
from Gen_Ai_Comparision import compare_screenshots

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Use absolute paths for consistency
BASE_DIR = os.getcwd()
SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, "backend", "screenshots")

# Ensure required folders exist
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

# Function to delete files after use
def delete_files_after_use(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Route to serve screenshots (if needed)
@app.route('/screenshots/<filename>')
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOTS_FOLDER, filename)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    urls = request.form.getlist('url')
    references = request.files.getlist('reference')

    if not urls or not references or len(urls) != len(references):
        return "Please provide both URLs and reference screenshots for comparison.", 400

    comparison_results = []
    for url, reference in zip(urls, references):
        # Capture screenshot for the provided URL.
        screenshot_path = take_screenshot(url)
        
        # Save the uploaded reference image into the screenshots folder.
        ref_path = os.path.join(SCREENSHOTS_FOLDER, reference.filename)
        reference.save(ref_path)

        # Compare the screenshots and create the merged image.
        comparison_result, merged_image_path = compare_screenshots(screenshot_path, ref_path)
        if not merged_image_path:
            print(f"Error: Failed to merge images for URL: {url}")
            continue

        # Generate an HTML report that includes a unique download link for the Excel file.
        report_content = generate_report(comparison_result, screenshot_path, ref_path, merged_image_path, url)
        comparison_results.append(report_content)

    if not comparison_results:
        return "Error: No valid comparisons could be performed.", 500

    # Build a ZIP file containing all generated HTML reports.
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for i, report_content in enumerate(comparison_results):
            zipf.writestr(f"Visual_Test_Report_{i+1}.html", report_content)
    
    zip_buffer.seek(0)

    # Optionally, clean up the screenshots folder after processing.
    delete_files_after_use(SCREENSHOTS_FOLDER)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='Visual_Test_Reports.zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
