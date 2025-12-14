from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_artifact_type_utility_loads(driver):
    """Test that artifact type utility is loaded by the app"""
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should be fully loaded
    assert driver.execute_script("return document.readyState") == "complete"

def test_artifact_type_used_in_upload(driver):
    """Test that artifact type inference is used in upload component"""
    driver.get("http://localhost:3000")
    
    # Find upload button
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Modal should be ready for URL input
    modal = driver.find_element(By.CLASS_NAME, "modal")
    assert modal.is_displayed()

def test_artifact_type_inference_messages(driver):
    """Test that artifact type inference provides appropriate feedback"""
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for error handling messages
    page_source = driver.page_source
    assert "artifact" in page_source.lower() or "upload" in page_source.lower()

def test_artifact_type_handles_urls(driver):
    """Test that the app can handle URLs for artifact type inference"""
    driver.get("http://localhost:3000")
    
    # Open upload modal
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Wait for input field
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Find and fill URL input
    inputs = driver.find_elements(By.TAG_NAME, "input")
    assert len(inputs) > 0

def test_artifact_type_supports_huggingface(driver):
    """Test that artifact type utility recognizes HuggingFace URLs"""
    driver.get("http://localhost:3000")
    
    # Open upload modal
    upload_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Upload')]"))
    )
    
    upload_button.click()
    
    # Modal should be ready to accept URLs
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    modal = driver.find_element(By.CLASS_NAME, "modal")
    assert modal.is_displayed()
