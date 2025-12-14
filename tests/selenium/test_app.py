from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_app_loads(driver):
    driver.get("http://localhost:3000")
    
    # Check if dashboard title is visible
    title = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dashboard-title"]'))
    )
    
    assert title.is_displayed()
    assert "Registry Dashboard" in title.text
