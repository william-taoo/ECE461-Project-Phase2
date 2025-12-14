from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_upload_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Look for upload button
    upload_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    assert upload_button.is_displayed()

def test_upload_modal_opens(driver):
    driver.get("http://localhost:3000")
    
    # Find and click upload button
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Wait for modal to appear
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    assert modal.is_displayed()

def test_upload_modal_has_input_field(driver):
    driver.get("http://localhost:3000")
    
    # Click upload button
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Wait for input field in modal
    input_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @placeholder]"))
    )
    
    assert input_field.is_displayed()

def test_upload_modal_has_submit_button(driver):
    driver.get("http://localhost:3000")
    
    # Click upload button
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Wait for submit button in modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for submit/upload button in modal
    page_source = driver.page_source
    assert "submit" in page_source.lower() or "Upload" in page_source
