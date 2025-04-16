import os
import time
import uuid
from PIL import Image
import base64
import pandas as pd
import google.generativeai as genai
from selenium import webdriver

# Use absolute paths for all folders
BASE_DIR = os.getcwd()
SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, "backend", "screenshots")

# Set up Google API key for genai and configure the client.
os.environ["GOOGLE_API_KEY"] = "AIzaSyD2cfkwJbq3613IirxiEGAP0V96OhDsozw"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def init_driver():
    """
    Initialize and return a Selenium WebDriver instance.
    """
    return webdriver.Chrome()

def take_screenshot(url):
    """
    Take a screenshot of the given URL using Selenium WebDriver.
    """
    driver = init_driver()
    try:
        driver.get(url)
        driver.maximize_window()
        time.sleep(4)  # Wait for page to load
        screenshot_name = f"{uuid.uuid4()}.png"
        screenshot_path = os.path.join(SCREENSHOTS_FOLDER, screenshot_name)
        driver.save_screenshot(screenshot_path)
        return screenshot_path
    finally:
        driver.quit()

def compare_screenshots(screenshot_path, ref_path):
    """
    Compare screenshots by merging them side-by-side and sending them
    to a Gemini Vision model for analysis.
    """
    try:
        # Open images using PIL.
        img1 = Image.open(screenshot_path)
        img2 = Image.open(ref_path)

        # Resize ref image to match screenshot dimensions.
        img2 = img2.resize(img1.size)

        # Merge the two images side-by-side.
        merged_image = Image.new("RGB", (img1.width * 2, img1.height))
        merged_image.paste(img1, (0, 0))
        merged_image.paste(img2, (img1.width, 0))

        # Ensure the screenshots folder exists.
        if not os.path.exists(SCREENSHOTS_FOLDER):
            os.makedirs(SCREENSHOTS_FOLDER)

        merged_image_name = f"merged_{uuid.uuid4().hex}.png"
        merged_image_path = os.path.join(SCREENSHOTS_FOLDER, merged_image_name)
        merged_image.save(merged_image_path)

        # Construct the prompt for Gemini Vision.
        prompt = """
## Task:
You are a senior UI QA engineer comparing two UI screenshots. The left image represents Version A, and the right image represents Version B. Your task is to produce comprehensive and exhaustive test cases that document both positive scenarios (elements that are consistent and correct in Version B when compared against Version A) and negative scenarios (discrepancies in Version B compared to Version A). **Ensure that every individual UI element or property is tested separately without grouping issues unless they are explicitly related.**

## Detailed Evaluation Aspects:
1. **Layout and Structure**
   - Examine header, footer, individual cards, sections, grid alignment, and overall layout.
2. **Color Scheme**
   - Compare background colors, text colors, button colors, icon colors, and overlays.
3. **Font Consistency**
   - Check font type, size, weight, and style for headings, labels, placeholders, paragraphs, and footers.
4. **Button/Icon Alignment**
   - Assess the placement and alignment of buttons and icons individually.
5. **Padding and Spacing**
   - Inspect the padding and spacing for input fields, cards, headers, footers, and other elements.
6. **Element Visibility**
   - Review whether icons, notifications, cards, or other components are fully visible and properly rendered.
7. **Text Accuracy**
   - Verify the spelling, grammar, and consistency of all textual elements such as labels, placeholders, tooltips, and UI strings.

## Output Requirements:
- **Exhaustive Coverage:** For every identified element and property, produce a unique test case—even if it means creating the maximum number of cases possible.
- **Comparison Focus:** Base each comparison on Version B, checking whether Version B meets or deviates from the established UI of Version A.
- **Single Header Usage:** Present all test cases in one markdown table. The header row (defining `Test Case ID`, `Title`, `Test Step`, `Expected Result`, `Actual Result`, and `Status`) should appear only once at the top and not be repeated.
- **Detailed Descriptions:** Include concise yet detailed descriptions for each test step, expected result, and actual result.
"""
        # Invoke the Gemini Vision model.
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        response = model.generate_content([prompt, merged_image], stream=False)

        return response.text, merged_image_path
    except Exception as e:
        print(f"Error in comparing screenshots: {e}")
        return f"Error in comparing screenshots: {e}", None

def generate_report(comparison_result, screenshot_path, ref_path, merged_image_path, url):
    """
    Generate an HTML report based on the screenshot comparison result.
    """
    # Helper function to encode an image to Base64 for inline display.
    def encode_image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Convert images to Base64 strings.
    Version_A_base64 = encode_image_to_base64(screenshot_path)
    Version_B_base64 = encode_image_to_base64(ref_path)

    # Parse the comparison result and create a DataFrame
    data = []
    headers = None

    for line in comparison_result.split("\n"):
        if line.startswith("|"):
            cells = line.split("|")[1:-1]
            if headers is None:
                headers = [cell.strip() for cell in cells]
            else:
                data.append([cell.strip() for cell in cells])

    df = pd.DataFrame(data, columns=headers)

    # Save the DataFrame to an Excel file
    excel_path = "comparison_report.xlsx"
    df.to_excel(excel_path, index=False)

    # Encode the Excel file to Base64
    with open(excel_path, "rb") as excel_file:
        excel_base64 = base64.b64encode(excel_file.read()).decode("utf-8")

    # Count the test results
    passed_count = df['Status'].str.lower().str.contains('pass').sum()
    failed_count = df['Status'].str.lower().str.contains('fail').sum()
    na_count = df['Status'].str.lower().str.contains('n/a').sum()
    total_count = len(df)

    # Build the HTML report
    report_content = f"""
    <html>
    <head>
        <title>Vislance Report</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            body{{
            font-family: Arial;
            padding: 20px;
            }}
            th, td {{
                border: 1px solid black;
                padding: 10px;
                text-align: left;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
            }}
            .pass {{
                color: green;
                font-weight: bold;
            }}
            .fail {{
                color: red;
                font-weight: bold;
            }}
            .na {{
                color: blue;
                font-weight: bold;
            }}
            .image-container {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            img {{
                max-width: 50%;
                height: auto;
                margin: 5px;
            }}
            .resized-image {{
                width: 1000px;  
                height: auto; 
                margin: 0 2%;
            }}
            .filter-buttons {{
                margin-top: 20px;
            }}
            .filter-buttons button {{
                margin-right: 10px;
                padding: 10px;
                font-size: 16px;
                cursor: pointer;
            }}
        </style>
        <script>
            function filterResults(status) {{
                var rows = document.querySelectorAll("table tr");
                rows.forEach(function(row) {{
                    if (row.querySelector("td")) {{
                        var cell = row.querySelector("td:last-child");
                        if (cell.textContent.toLowerCase() === status.toLowerCase()) {{
                            row.style.display = "";
                        }} else {{
                            row.style.display = "none";
                        }}
                    }}
                }});
            }}
            function showAllResults() {{
                var rows = document.querySelectorAll("table tr");
                rows.forEach(function(row) {{
                    row.style.display = "";
                }});
            }}
            function downloadExcel() {{
                var link = document.createElement("a");
                link.href = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}";
                link.download = "comparison_report.xlsx";
                link.click();
            }}
        </script>
    </head>
    <body>
        <h2 style="text-align: center;">Vislance Report</h2>
        <p><strong>URL:</strong> {url}</p>
        <div class="image-container">
            <div>
                <p><strong>Version A:</strong></p>
                <img src="data:image/png;base64,{Version_A_base64}" alt="Version A" class="resized-image">
            </div>
            <div>
                <p><strong>Version B:</strong></p>
                <img src="data:image/png;base64,{Version_B_base64}" alt="Version B" class="resized-image">
            </div>
        </div>
        <h3 style="text-align: center;">Test Summary</h3>
        <table style="width: 50%; margin-left: auto; margin-right: auto;">
            <tr class="header">
                <th>Category</th>
                <th>Count</th>
            </tr>
            <tr>
                <td>Total Test Cases</td>
                <td>{total_count}</td>
            </tr>
            <tr>
                <td class="pass">Passed</td>
                <td class="pass">{passed_count}</td>
            </tr>
            <tr>
                <td class="fail">Failed</td>
                <td class="fail">{failed_count}</td>
            </tr>
            <tr>
                <td class="na">N/A</td>
                <td class="na">{na_count}</td>
            </tr>
        </table>
        <button onclick="downloadExcel()">Download Excel Report</button>
        <h3>Comparison Results</h3>
        <div class="filter-buttons">
            <button onclick="filterResults('pass')">Show Pass</button>
            <button onclick="filterResults('fail')">Show Fail</button>
            <button onclick="filterResults('na')">Show N/A</button>
            <button onclick="showAllResults()">Show All</button>
        </div>
        <table>
        <tr class="header">
            <th>Test Case ID</th>
            <th>Title</th>
            <th>Test Step</th>
            <th>Expected Result</th>
            <th>Actual Result</th>
            <th>Status</th>
    """
    first_row = True 
    second_row = True   
    row_index = 0  # To track table row index.
    for line in comparison_result.split("\n"):
        if line.startswith("|"):
            # Skip duplicate header row if encountered.
            if row_index == 0 or row_index==1:  
                row_index += 1
                continue
            else:
                report_content += "<tr>"
            cells = line.split("|")[1:-1]
            for i, cell in enumerate(cells):
                cell_content = cell.strip()
                if i == len(cells) - 1:  # For the Status column.
                    if "pass" in cell_content.lower():
                        report_content += f'<td class="pass">{cell_content}</td>'
                    elif "fail" in cell_content.lower():
                        report_content += f'<td class="fail">{cell_content}</td>'
                    elif "n/a" in cell_content.lower():
                        report_content += f'<td class="na">{cell_content}</td>'
                    else:
                        report_content += f"<td>{cell_content}</td>"
                else:
                    report_content += f"<td>{cell_content}</td>"
            report_content += "</tr>"
            row_index += 1

    report_content += f"""
        </table>
    </body>
    </html>
    """
    return report_content
