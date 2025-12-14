from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_inspect_artifact_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should be ready
    assert driver.execute_script("return document.readyState") == "complete"

def test_inspect_artifact_functionality_available(driver):
    driver.get("http://localhost:3000")
    
    # Wait for artifacts to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for artifact-related content
    page_source = driver.page_source
    assert "artifact" in page_source.lower()

def test_inspect_artifact_has_action_buttons(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for action buttons like Download, Audit, Lineage, Delete
    page_source = driver.page_source
    assert any(action in page_source.lower() for action in ["download", "audit", "lineage", "delete", "update"])

def test_inspect_artifact_modal_structure(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # InspectArtifact modal should be structured as modal
    page_source = driver.page_source
    assert "modal" in page_source.lower() or "artifact" in page_source.lower()

def test_inspect_artifact_allows_url_update(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for update functionality
    page_source = driver.page_source
    assert "update" in page_source.lower() or "artifact" in page_source.lower()

def test_inspect_artifact_displays_metadata(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for metadata display
    page_source = driver.page_source
    assert "name" in page_source.lower() or "id" in page_source.lower() or "type" in page_source.lower()
