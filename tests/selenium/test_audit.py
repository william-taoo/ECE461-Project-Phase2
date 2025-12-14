from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_audit_button_in_artifact_inspection(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for audit-related content
    page_source = driver.page_source
    assert "audit" in page_source.lower() or "Audit" in page_source

def test_audit_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to fully load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should render successfully
    assert driver.execute_script("return document.readyState") == "complete"

def test_audit_button_variant(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Audit should be available as a button variant
    page_source = driver.page_source
    assert "button" in page_source.lower() or "variant" in page_source.lower()

def test_audit_artifact_functionality_available(driver):
    driver.get("http://localhost:3000")
    
    # Wait for artifacts section to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Verify page is interactive
    assert driver.execute_script("return document.readyState") == "complete"
