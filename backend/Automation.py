import os
import time
import uuid
from selenium import webdriver

# Use absolute paths for all folders
BASE_DIR = os.getcwd()
SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, "backend", "screenshots")

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

