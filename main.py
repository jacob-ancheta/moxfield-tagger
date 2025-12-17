from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# selenium accesses elements using locators like By.ID, By.NAME, By.CSS_SELECTOR, By.XPATH, etc.

service = Service(r"C:\Users\Jacob\OneDrive\Desktop\tools\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service)
# url = input("paste url here (must be unlisted or public): ")
url = "https://www.google.com"
url2 = "https://moxfield.com/"
url3 = "https://moxfield.com/decks/IAy9EmFU6E69zz-WGrsc-g"
driver.get(str(url3))


card_list = []
#cards = driver.find_elements(By.CSS_SELECTOR, '.decklist-card')
wait = WebDriverWait(driver, 15)

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.table-deck-row-link.text-body")))
cards = driver.find_elements(By.CSS_SELECTOR, "a.table-deck-row-link.text-body")

for card in cards:
    # checks if has attribute href, ignoring section titles
    href = card.get_attribute("href")
    if href and "/cards/" in href:
        name_spans = card.find_elements(By.CSS_SELECTOR, "span.underline")
        full_name = " ".join(span.text.strip() for span in name_spans if span.text.strip())
        if full_name not in card_list:
            card_list.append(full_name)

print(card_list)
input("Press Enter to close the browser..." )
driver.quit()
