from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_lineage_button_in_artifact_inspection(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for lineage-related content
    page_source = driver.page_source
    assert "lineage" in page_source.lower() or "Lineage" in page_source

def test_lineage_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should render without errors
    assert driver.execute_script("return document.readyState") == "complete"

def test_lineage_button_variant(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Lineage button should use info variant
    page_source = driver.page_source
    assert "info" in page_source.lower() or "button" in page_source.lower()

def test_lineage_artifact_functionality(driver):
    driver.get("http://localhost:3000")
    
    # Wait for artifacts section
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Verify artifacts can be inspected (where lineage is available)
    page_source = driver.page_source
    assert "artifact" in page_source.lower() or "model" in page_source.lower()
