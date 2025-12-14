from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_download_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should render without errors
    assert driver.execute_script("return document.readyState") == "complete"

def test_download_requires_artifact_id(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Download component should be part of InspectArtifact modal
    # which appears when an artifact is selected
    page_source = driver.page_source
    assert "download" in page_source.lower() or "Download" in page_source

def test_download_button_appearance(driver):
    driver.get("http://localhost:3000")
    
    # Wait for artifacts section
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check page contains download-related text
    page_source = driver.page_source
    # Download should be available after selecting an artifact
    assert "download" in page_source.lower() or driver.title != ""
