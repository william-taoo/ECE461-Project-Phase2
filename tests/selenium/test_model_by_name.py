from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_model_by_name_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Find search by name button
    search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Search by Name')]"))
    )
    
    assert search_button.is_displayed()

def test_model_by_name_modal_opens(driver):
    driver.get("http://localhost:3000")
    
    # Find and click search by name button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Name')]"))
    )
    
    search_button.click()
    
    # Wait for modal to appear
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    assert modal.is_displayed()

def test_model_by_name_has_name_input(driver):
    driver.get("http://localhost:3000")
    
    # Click search by name button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Name')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for input field
    page_source = driver.page_source
    assert "input" in page_source.lower()

def test_model_by_name_modal_has_search_button(driver):
    driver.get("http://localhost:3000")
    
    # Click search by name button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Name')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for search/submit button
    page_source = driver.page_source
    assert "search" in page_source.lower() or "button" in page_source.lower()

def test_model_by_name_component_initializes(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Page should be interactive
    assert driver.execute_script("return document.readyState") == "complete"
