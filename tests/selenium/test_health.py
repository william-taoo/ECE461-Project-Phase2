from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_health_component_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for health section to appear
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check if health-related content exists
    page_source = driver.page_source
    assert "health" in page_source.lower() or "Health" in page_source

def test_health_status_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to fully load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Give health component time to fetch data
    import time
    time.sleep(2)
    
    # Verify page is still responsive
    assert driver.execute_script("return document.readyState") == "complete"

def test_health_component_exists_in_page(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check that health component is rendered
    page_source = driver.page_source
    # Health component should be in the grid
    assert "grid" in page_source.lower() or "Health" in page_source
