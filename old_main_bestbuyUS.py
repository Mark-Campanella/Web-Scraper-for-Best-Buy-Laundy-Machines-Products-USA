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
search_for = "washer & dryer"


#-----------------------------------------------------Do Not Modify if no changes are required------------------------------------------------------#

class_search_bar = "search-input"
class_search_button = "header-search-button"

class_items = "sku-item"
class_next_button = "sku-list-page-next"

class_show_full_specs = "c-button.c-button-outline.c-button-md.show-full-specs-btn.col-xs-6"

class_product_5_star = "ugc-c-review-average.font-weight-medium.order-1"
class_product_review_amount = "c-reviews.order-2"
class_product_price = "priceView-hero-price.priceView-customer-price"

class_ul_item_specs = "zebra-stripe-list.inline.m-none.p-none"
class_li_item_specs = "zebra-list-item.mt-500"
class_div_each_spec = "zebra-row.flex.p-200.justify-content-between.body-copy-lg"
class_div_spec_type = "mr-100.inline"
class_div_spec_text = "w-full"

# Global Variables
next_page = None
links = []
products_data = []
all_headers = set()

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
    
def handle_survey():
    try:
        # Verifica se o botão "no thanks" está presente
        no_thanks_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "survey_invite_no"))
        )
        no_thanks_button.click()
        print("Survey dismissed")
    except:
        print("No survey popup")
        
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
    global products_data, all_headers
    driver.get(link) #Go to the object's page
    driver.implicitly_wait(20) #Wait the page to load
    handle_survey()
    try:
        product_name_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        product_name = product_name_element.text
    except Exception as e: print("Some error, ", e)
    
    if "Package" in product_name: return
    
    product_info = {'Link': link, 'Name' : product_name} #append its link in the dictionary
    
    # Get price
    try:
        price_div = driver.find_element(By.CLASS_NAME, 'priceView-hero-price.priceView-customer-price')
        price = price_div.find_element(By.TAG_NAME, 'span').text
    except:
        try:
            driver.execute_script("window.scrollBy(0, 150)")           
            driver.find_element(By.CLASS_NAME,"priceView-tap-to-view-price.priceView-tap-to-view-price-bold").click()
            try:
                price_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'restricted-pricing__regular-price-section'))
                )
                price_div = price_div.find_element(By.CLASS_NAME, 'pricing-price')
                price_div = price_div.find_element(By.CLASS_NAME, 'priceView-hero-price.priceView-customer-price')
                price = price_div.find_element(By.TAG_NAME, 'span').text
            except Exception as e_text:
                print("Couldn't get the price because ", e_text)
            
            try:
                close_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "c-close-icon.c-modal-close-icon"))
                )
                close_btn.click()
            except Exception as e:
                print(f"Error clicking close button: {e}")
                try:
                    # Usar JavaScript para clicar no botão
                    driver.execute_script("arguments[0].click();", close_btn)
                except Exception as js_e:
                    print(f"Error clicking close button with JS: {js_e}")
                    try:
                        driver.refresh()
                    except Exception as all_e:
                        print("Error in all atempts to click in the close button: ", all_e)
        except: price = ""
        
    finally:
        # Add information
        product_info['Price'] = price
    try:
            # Espera até que o elemento de cinco estrelas esteja presente e obtenha o texto
        five_star = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_product_5_star))
        ).text
    
        # Espera até que o elemento de quantidade de reviews esteja presente e obtenha o texto
        review_amount = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_product_review_amount))
        ).text
        
        product_info['Five Star'] = five_star
        product_info['Review Amount'] = review_amount
    except Exception as e: print("Some error occurred while getting the Five Star / Review Amount Data:", e)
    
    try:
        WebDriverWait(driver,30).until(EC.element_to_be_clickable((By.CLASS_NAME,class_show_full_specs))).click() #click the show full specs button
    except Exception as e: print(f"We couldn't click in the button, error: ", e)
    
    try:
        # Wait until all elements with the specified class are located in the DOM
        list_of_specs_ul = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'zebra-stripe-list.inline.m-none.p-none'))
        )

        # Initialize dictionaries to store specifications
        complete_specs = {}

        # Iterate through each item in the list of specification elements
        for each_item in list_of_specs_ul:
            try:
                # Extract the header text
                header = each_item.find_element(By.CLASS_NAME, "mr-100.inline").text

                # Extract the specification text
                spec = each_item.find_element(By.CLASS_NAME, "w-full").text

                # Combine headers and specs into the complete_specs dictionary
                complete_specs[header] = spec

                # Add header to the global all_headers set
                all_headers.add(header)

            except Exception as e:
                print(f"Error extracting specification: {e}")
                continue

    except Exception as e:
        # Handle any exception that occurs in the try block
        print(f"Error occurred: {e}")

    finally:
        # Update the product information dictionary with the complete specifications
        product_info.update(complete_specs)

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
    handle_survey()
    search = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, class_search_bar)))
    search.send_keys(search_for)
    
    time.sleep(2)
    
    button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, class_search_button)))
    button.click()
    
    driver.implicitly_wait(20)  # Wait for it to load
    
    #this is test aligned, to make it faster
    try:
        links = pd.read_csv("product_links.csv")
        links = links["Product Links"].to_list()
          
    except:
        scrape_page(driver)
        ##For test purposes, comment this section and delete the above sentence   
        # while True:
        #     '''
        #     For each page, scrape the links until you find no more pages
        #     '''
        #     handle_survey()
        #     scrape_page(driver)
           
            # if next_page: 
            #     driver.get(next_page)
            #     print(f"Navigating to next page: {next_page}")

            # else: 
            #     break
    
except Exception as e:
    print("Not able to run the code, error: ", e)

    
if not os.path.exists("product_links.csv"):
    df = pd.DataFrame(links, columns=['Product Links'])
    df.to_csv("product_links.csv", index=False)

process_products(driver)

# Convert the list of dictionaries into a dataframe, printing top 5 items for checking
df = pd.DataFrame(products_data)
# Reorder columns based on all_headers
all_headers = list(all_headers)
columns_order = ['Link', 'Name', 'Price', 'Five Star', 'Review Amount'] + all_headers
df = df.reindex(columns=columns_order)

print(df.head(20))
df.to_csv('product_data.csv', index=False)

driver.quit()