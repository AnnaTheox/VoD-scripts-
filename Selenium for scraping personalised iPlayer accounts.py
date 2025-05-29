#image dimensions integration

import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

EDGEDRIVER_PATH = r"C:\Users\kdpk341\Desktop\0305 webdriver\msedgedriver.exe"
options = Options()
options.add_argument("-inprivate")  # Open in private mode
options.use_chromium = True
service = Service(EDGEDRIVER_PATH)
driver = webdriver.Edge(service=service, options=options)
driver.set_window_size(1920, 1080)

genres = []
usernames = []
passwords = []

titles = []
descriptions = []
carousel_titles = []
carousel_order = []
row_order = []
image_sizes = []  # For storing image sizes
image_modes = []  # For storing image modes (Landscape/Portrait)
progcount = 0
seen_sections = set()  # TRACKING TO PREVENT DUPLICATION

with open("iplayer-logins.csv", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)
    login_count = 0
    for row in reader:
        genres.append(row[0])
        usernames.append(row[1])
        passwords.append(row[2])
        login_count += 1
    print(f"Read in {login_count} logins)")

done_clean = False

def extract_programme_data():
    global progcount
    
    # INFINITE SCROLL
    SCROLL_PAUSE_TIME = 0.5

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # SCRAPING SECTIONS IN ORDER
    sections = driver.find_elements(By.TAG_NAME, "section")
    
    first_hero_processed = False  # FLAG 1ST PROGRAMME BECAUSE IT KEEPS GETTING DUPLICATED
    hero_class = "hero-promo"
    section_class = "section"

    # DUPLICATION: TRACKING + SKIPPING SCRAPED SECTIONS
    for index, section in enumerate(sections, start=1):
        section_id = str(section)

        if section_id in seen_sections:
            continue
        seen_sections.add(section_id)

        class_name = section.get_attribute("class")  # Get the class attribute
        if hero_class in class_name.split():  # Ensure it's checking individual class names
            #Process hero board
            print(f"Section {index} is HERO BOARD - contains the class '{hero_class}'.")
            
            title_tag = section.find_element(By.CLASS_NAME, "hero-promo__title")
            description_tag = section.find_element(By.CLASS_NAME, "hero-promo__synopsis")

            hero_title = title_tag.text.strip() if title_tag else f"Hero/Promo {index}"
            hero_description = description_tag.text.strip() if description_tag else ""

            # 1ST PROGRAMME HERO CAROUSEL
            if not first_hero_processed:
                first_hero_processed = True  # Mark first hero carousel as processed
                section_name = f"Hero Carousel {index}"
                hero_count = 0
                # Extract programmes ONLY for the first hero carousel
                for item in section.find_elements(By.CLASS_NAME, "hero-promo__card"):
                    hero_count += 1
                    prog_title_tag = item.find_element(By.CLASS_NAME, "hero-promo__title")
                    prog_desc_tag = item.find_element(By.CLASS_NAME, "hero-promo__synopsis")

                    prog_title = prog_title_tag.text.strip() if prog_title_tag else "Unknown Programme"
                    prog_desc = prog_desc_tag.text.strip() if prog_desc_tag else ""

                    # Get image info from <picture> tag
                    picture_tag = item.find_element(By.TAG_NAME, "picture")
                    if picture_tag:
                        size = picture_tag.size  # Returns a dictionary {'height': ..., 'width': ...}
                        ewidth = size['width']
                        eheight = size['height']
                        esize = ewidth*eheight
                        if ewidth < eheight:
                            ecategory = 'portrait'
                        else:
                            ecategory = 'landscape'

                    #store data in variables              
                    carousel_titles.append(section_name)
                    carousel_order.append(index)
                    row_order.append(hero_count)
                    if prog_title: titles.append(prog_title)
                    if prog_desc: descriptions.append(prog_desc)
                    if esize: image_sizes.append(esize)  
                    if ecategory: image_modes.append(ecategory)

                    progcount += 1
            else:
                section_name = f"Promo Banner {index}"

                titles.append(hero_title)
                descriptions.append(hero_description)
                carousel_titles.append(section_name)
                carousel_order.append(index)
                row_order.append(1)
                image_sizes.append("Unknown")  # No image for promo banners
                image_modes.append("Unknown")  # No image for promo banners

                progcount += 1

            print(f"Extracted {section_name}: {hero_title} - {hero_description}")

        elif section_class in class_name.split():  # Ensure it's checking individual class names:
            #Process normal rows
            print(f"Section {index} is a NORMAL ROW - does NOT contain the class '{hero_class}'.")
            try:
                carousel_title = section.find_element(By.TAG_NAME, "h2")
                carousel_name = carousel_title.text.strip() if carousel_title else f"Carousel {index}"
            except:
                print(f"carousel title failed on carousel {index}")
                carousel_title = "missing/failed"
                carousel_name = "missing/failed"
                
            row_count = 0
            for post in section.find_elements(By.CLASS_NAME, "carrousel__item"):
                row_count += 1
                programme = post.find_element(By.CLASS_NAME, "content-item-root")
                title = post.find_element(By.CLASS_NAME, "content-item-root__meta")
                rsimage = post.find_element(By.CLASS_NAME, "rs-image")

                row_order.append(row_count)
                if programme:
                    aria_label = programme.get_attribute("aria-label")
                    if aria_label: descriptions.append(aria_label)
                
                if title:
                    titles.append(title.text.strip())
                    carousel_titles.append(carousel_name)
                    carousel_order.append(index)

                if rsimage:
                    size = rsimage.size  # Returns a dictionary {'height': ..., 'width': ...}
                    ewidth = size['width']
                    eheight = size['height']
                    esize = ewidth*eheight
                    if ewidth < eheight:
                        ecategory = 'portrait'
                    else:
                        ecategory = 'landscape'
                    image_sizes.append(esize)  
                    image_modes.append(ecategory) 

                progcount += 1

def getPageandScrape(genre, username, password):

    #testing
    #print(f"Processed login: {username}")

    global driver

    #test and relaunch if driver has previously quit
    if driver is None: 
        driver = webdriver.Edge(service=service, options=options)
        driver.set_window_size(1920, 1080)

    try:
        # 1. Open iPlayer
        driver.get("https://www.bbc.co.uk/iplayer")

        # 2. Accept Cookies
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#bbccookies-accept-button"))
            ).click()
            print("Cookies accepted.")
        except Exception:
            print("No cookies popup found or already accepted.")

        if genre == "Clean":
            print("Scraping without login")
        else:        
            # 3. SIGN IN
            driver.get("https://account.bbc.com/signin")

            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#user-identifier-input"))
            )
            email_field.send_keys(username)

            driver.find_element(By.CSS_SELECTOR, "#submit-button").click()

            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#password-input"))
            )
            password_field.send_keys(password)

            driver.find_element(By.CSS_SELECTOR, "#submit-button").click()

            # 4. WAIT GLOBAL NAVIGATION LOADING
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#global-navigation"))
            )

            print("Successfully logged in.")

            # 5. Go to iPlayer
            driver.get("https://www.bbc.co.uk/iplayer")

        # 6. Wait for Content to Load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.hero-promo"))
        )


        # 7. SCRAPE + SAVE

        # reset other variables so they don't duplicate
        titles.clear()
        descriptions.clear()
        carousel_titles.clear()
        carousel_order.clear()
        row_order.clear()
        image_sizes.clear()  # For storing image sizes
        image_modes.clear()  # For storing image modes (Landscape/Portrait)

        extract_programme_data()

        platform = 'iplayer'
        today = datetime.today().date().strftime("%d%m%y")
        output_file = genre + "_" + platform + "_" + today

        csv_filename = output_file + ".csv"
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Carousel Name", "Carousel Order", "Row order", "Title", "Aria Description", "Image Size", "Image Mode"])
            writer.writerows(zip(carousel_titles, carousel_order, row_order, titles, descriptions, image_sizes, image_modes))

        print(f"Scraping complete! Data saved to {csv_filename}")

        ## DO THE SCREENSHOT
        # Get total height of the page
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Set viewport height
        viewport_height = driver.execute_script("return window.innerHeight")

        # List to store screenshots
        screenshots = []

        # Scroll and capture screenshots
        for y in range(0, total_height, viewport_height):
            driver.execute_script(f"window.scrollTo(0, {y})")
            time.sleep(1)  # Wait for the page to load

            screenshot_path = f"screenshot_{y}.png"
            driver.save_screenshot(screenshot_path)
            screenshots.append(Image.open(screenshot_path))

        # Stitch screenshots together
        final_image = Image.new("RGB", (screenshots[0].width, total_height))
        y_offset = 0

        for img in screenshots:
            final_image.paste(img, (0, y_offset))
            y_offset += img.height

        final_image.save(output_file + ".png")

    finally:
        driver.quit()
        driver = None

#actually do the work now the functions have been defined
for index, genre in enumerate(genres, start=0):
    print(f"Scraping iplayer for the: {genre} account")
    getPageandScrape(genre, usernames[index], passwords[index])
