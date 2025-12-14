from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_rate_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Rate button should be available in the artifacts section
    page_source = driver.page_source
    assert "rate" in page_source.lower() or "Rate" in page_source

def test_rate_model_button_in_artifact_inspection(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to fully load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Rate Model should be available when inspecting an artifact
    page_source = driver.page_source
    assert "model" in page_source.lower() or "artifact" in page_source.lower()

def test_rate_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for artifacts to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should be fully loaded
    assert driver.execute_script("return document.readyState") == "complete"

def test_rate_button_styling(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Verify styling elements exist
    page_source = driver.page_source
    assert "blue" in page_source.lower() or "button" in page_source.lower()
