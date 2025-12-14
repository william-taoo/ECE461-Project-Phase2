from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_reset_button_visible(driver):
    driver.get("http://localhost:3000")
    reset_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="reset-button"]'))
    )

    assert reset_button.is_displayed()

def test_reset_button_click(driver):
    driver.get("http://localhost:3000")
    reset_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="reset-button"]'))
    )

    reset_button.click()

    alert = WebDriverWait(driver, 10).until(EC.alert_is_present())
    assert "Registry reset" in alert.text

    alert.accept()