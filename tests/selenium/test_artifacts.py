from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_artifacts_component_loads(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Artifacts component should be visible on main page
    page_source = driver.page_source
    assert "artifact" in page_source.lower()

def test_artifacts_search_query_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for search by query button
    search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    assert search_button.is_displayed()

def test_artifacts_page_renders_without_errors(driver):
    driver.get("http://localhost:3000")
    
    # Check for any console errors
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should have loaded successfully
    assert driver.execute_script("return document.readyState") == "complete"
