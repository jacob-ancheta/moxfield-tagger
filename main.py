from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service(r"C:\Users\Jacob\OneDrive\Desktop\tools\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.get("https://www.google.com")
input("Press Enter to close the browser...")
driver.quit()