import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import pandas as pd
import os
#-------------------------------------------------------Driver CONFIGURATION-------------------------------------------------------------------------#
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-geolocation")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-extensions")

driver = webdriver.Chrome(options=chrome_options)
stealth(driver,
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

#-----------------------------------------------------Personalization Variables---------------------------------------------------------------------#
url = "https://www.bestbuy.com/?intl=nosplash"
class_search_bar = "search-input"
search_for = "washer & dryer"
class_search_button = "header-search-button"

class_items = "sku-item"
class_next_button = "sku-list-page-next"

class_show_full_specs = "c-button.c-button-outline.c-button-md.show-full-specs-btn.col-xs-6"
class_name = "body-copy-lg.v-fw-regular"

# Global Variables
next_page = None
links = []
products_data = []


#----------------------------------------------------------------Functions-------------------------------------------------------------------------#
def scrape_page(driver):
    '''
    This function gets the link of each object of each page in the 'keywords' pages.
    It will change variables such as 'product_link' and 'next_page',
    putting all the links inside product_link and going to the next page if there is one
    
    Parameters:
        -driver: webdriver
    '''
    global links
    global next_page
        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("Scrolled to bottom of the page.")
    try:
        # wait until elements are found
        elems = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, class_items)))
        print(f"Found {len(elems)} elements with class {class_items}.")

        tags = [elem.find_element(By.TAG_NAME, "a") for elem in elems]
        links.extend([tag.get_attribute("href") for tag in tags])
        
        try:
            next_page = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_next_button))).get_attribute("href")
            print(f"Found next page: {next_page}")
        except:
            next_page = None
            print("No next page found.")
    except Exception as e: print("Error!! ",e)

def process_product(driver:webdriver, link:str):
    '''
    For each object whose link was copied in the product_link:
    →it will fetch some informations
    →process a dictionary if this informations
    →append in the list of the dictionaries that contains all machines
    
    For all of them, we are trying to get, if not found, leave it blank, because there are lots of differences between each object
    
    Parameters:
        -driver: webdriver
        -link: str
    '''
    global products_data
    driver.get(link) #Go to the object's page
    driver.implicitly_wait(20) #Wait the page to load
    try:
        WebDriverWait(driver,).until(
            EC.presence_of_element_located((By.CLASS_NAME,class_show_full_specs))).click()
    except:
        return

    product_info = {'Link': link} #append it's link in the dictionary

    try:
        name = driver.find_element(By.CLASS_NAME, class_name).text 
        product_info['Name'] = name #append it's name in the dictionary      
    except: product_info['Name'] = ""
    
    products_data.append(product_info)#Add item in the list of items

def process_products(driver:webdriver):
    '''
        Iterates for each link, in the end let go of the list of links
    '''
    global links
    for link in links: process_product(driver, link)

    links.clear()

#---------------------------------------------------------------------------Begining---------------------------------------------------------------------#    
try:        
    driver.get(url)
    driver.implicitly_wait(20)  # Wait for it to load
    print("Page loaded.")
    search = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, class_search_bar)))
    search.send_keys(search_for)
    
    time.sleep(2)
    
    button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, class_search_button)))
    button.click()
    
    driver.implicitly_wait(20)  # Wait for it to load
    try:
        links = pd.read_csv("product_links.csv")
        links = links["Product Links"].to_list()    
    except:
        while True:
            '''
            For each page, scrape the links until you find no more pages
            '''
            scrape_page(driver)
            if next_page: 
                driver.get(next_page)
                print(f"Navigating to next page: {next_page}")

            else: 
                break
        
except Exception as e:
    print("Not able to run the code, error: ", e)

    
if not os.path.exists("product_links.csv"):
    df = pd.DataFrame(links, columns=['Product Links'])
    df.to_csv("product_links.csv", index=False)

process_products(driver)

# Convert the list of dictionaries into a dataframe, printing top 5 items for checking
df = pd.DataFrame(products_data)
print(df.head(20))
df.to_csv('product_data.csv', index=False)

driver.quit()