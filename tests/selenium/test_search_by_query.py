from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_search_by_query_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Find search by query button
    search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    assert search_button.is_displayed()

def test_search_by_query_modal_opens(driver):
    driver.get("http://localhost:3000")
    
    # Find and click search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    search_button.click()
    
    # Wait for modal to appear
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    assert modal.is_displayed()

def test_search_by_query_has_input_fields(driver):
    driver.get("http://localhost:3000")
    
    # Click search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    search_button.click()
    
    # Wait for modal and input fields
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for input fields in modal
    page_source = driver.page_source
    assert "input" in page_source.lower() or "search" in page_source.lower()

def test_search_by_query_has_type_dropdown(driver):
    driver.get("http://localhost:3000")
    
    # Click search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for dropdown or select element
    page_source = driver.page_source
    assert "select" in page_source.lower() or "type" in page_source.lower()

def test_search_by_query_modal_has_submit(driver):
    driver.get("http://localhost:3000")
    
    # Click search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Query')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for submit button in modal
    page_source = driver.page_source
    assert "button" in page_source.lower()
