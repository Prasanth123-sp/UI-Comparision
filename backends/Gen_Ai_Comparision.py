from PIL import Image
import google.generativeai as genai
import os
import uuid

BASE_DIR = os.getcwd()
SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, "backend", "screenshots")

# Set up Google API key for genai and configure the client.
os.environ["GOOGLE_API_KEY"] = "AIzaSyD2cfkwJbq3613IirxiEGAP0V96OhDsozw"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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