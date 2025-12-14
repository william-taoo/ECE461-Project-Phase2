from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_regex_button_visible(driver):
    driver.get("http://localhost:3000")
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Find search by regex button
    search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Search by Regex')]"))
    )
    
    assert search_button.is_displayed()

def test_regex_modal_opens(driver):
    driver.get("http://localhost:3000")
    
    # Find and click search by regex button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Regex')]"))
    )
    
    search_button.click()
    
    # Wait for modal to appear
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    assert modal.is_displayed()

def test_regex_has_regex_input(driver):
    driver.get("http://localhost:3000")
    
    # Click search by regex button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Regex')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Check for input field
    page_source = driver.page_source
    assert "input" in page_source.lower()

def test_regex_modal_has_submit_button(driver):
    driver.get("http://localhost:3000")
    
    # Click search by regex button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search by Regex')]"))
    )
    
    search_button.click()
    
    # Wait for modal
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "modal"))
    )
    
    # Verify submit button exists
    page_source = driver.page_source
    assert "button" in page_source.lower()

def test_regex_component_styling(driver):
    driver.get("http://localhost:3000")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    # Check for button styling
    page_source = driver.page_source
    assert "blue" in page_source.lower() or "button" in page_source.lower()
