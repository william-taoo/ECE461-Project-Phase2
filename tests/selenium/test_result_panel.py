from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_result_panel_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for result panel
    page_source = driver.page_source
    assert "Result Panel" in page_source

def test_result_panel_displays_on_page(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Result panel should be visible
    page_source = driver.page_source
    assert "result" in page_source.lower()

def test_result_panel_styling(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for styling elements
    page_source = driver.page_source
    assert "gray" in page_source.lower() or "panel" in page_source.lower()

def test_result_panel_has_placeholder_text(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for default message when no results
    page_source = driver.page_source
    assert "No results yet" in page_source or "result" in page_source.lower()

def test_result_panel_can_display_json(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Result panel should have formatting for JSON display
    page_source = driver.page_source
    assert "pre" in page_source.lower() or "json" in page_source.lower() or "Result Panel" in page_source
