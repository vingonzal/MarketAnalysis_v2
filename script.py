import requests #library for making HTTP requests
from bs4 import BeautifulSoup #library used for parsing HTML and XML documents
import csv #module for CSV file handling
from urllib.parse import urljoin # urljoin function is used to construct an absolute URL
import os #module to help with OS function: file/directory operations and path manipulation

# *************************************************************
# *******Project: Use Python Basics for Market Analysis********
# *************************************************************

# Begin at the main() function below

# function to retrieve each individual book's data - Phase 1 - Extraction
def getSingleBookData(url):
    page = requests.get(url)
    # Get the URL of the current page
    product_page_url = page.url
    # create soup object
    soup = BeautifulSoup(page.content, 'html.parser')
    # find elements (title, category, description) using selectors
    book_title = soup.select_one('#content_inner > article > div.row > div.col-sm-6.product_main > h1').text
    book_category = soup.select_one('#default > div > div > ul > li:nth-child(3) > a').text
    if soup.select_one('#content_inner > article > p') == None:
        product_description = 'None'
    else:
        product_description = soup.select_one('#content_inner > article > p').text
    # locate table using the <table> tag
    table = soup.find('table', class_='table table-striped') 
    # loop through table to find and store headers
    table_headers = [th.text.strip() for th in table.find_all('th')]
    # loop through table to find and store table data
    table_data = [td.text.strip() for td in table.find_all('td')]
    # declare empty dictionary
    element_dict = {}
    # fill dictionary with keys (headers) and values (table data) using loop
    for item in range(len(table_headers)):
        element_dict[table_headers[item]] = table_data[item]
    # assign target elements the corresponding dictionary value
    universal_product_code = element_dict['UPC']
    price_excluding_tax = element_dict['Price (excl. tax)']
    price_including_tax = element_dict['Price (incl. tax)']
    quantity_available = element_dict['Availability']
    find_rating = soup.select_one('[class^="star-rating "]')
    # retrieve rating (represented by second index)
    review_rating = find_rating.get('class')[1]
    # image url
    main_image = soup.find('img')
    if main_image:
        image_url = main_image["src"].replace("../..", "")
    base_url = 'http://books.toscrape.com/'
    # use urljoin to combine base url with relative url to get absolute URL
    image_url = urljoin(base_url, image_url)
    # Phase 4 task
    saveImages(image_url, book_category) #call function to download image url
    # return all elements
    return product_page_url, universal_product_code, book_title, price_including_tax, price_excluding_tax, quantity_available, product_description, book_category, review_rating, image_url

# function to download images - Phase 4
def saveImages(image_link, category):
    url = image_link   
    image_folder = f"{category}_images"
    # check if a folder already exists - if not, make a new folder
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    # send request to get the image link and store the binary data into the response object
    img_data = requests.get(url).content
    img_name = os.path.basename(url)  # Get the "tail" or base from URL: filename.jpg
    img_path = os.path.join(image_folder, img_name) #contruct file path
    # prepare and open file using img_path in write and binary mode
    with open(img_path, 'wb') as handler: #assign open file object to handler variable
        handler.write(img_data) #load the file

# #visit category page and extract URLs - Phase 2
def singleCategoryData(url, book_category):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    urls = []
    page_num = 2
    while True:
        # scan for and store the book URL data represented by their image
        find_urls = soup.find_all('div', attrs={'class':'image_container'})
        # loop through each element found under 'image_container' class
        for element in find_urls:
            # loop through each <a> tag
            for link in element.find_all('a'):
                # retrieve URL (specified as local link/relative URL)
                href = link.get('href').replace("../../..", "catalogue")
                if href:
                    # add relative URL to urls list
                    urls.append(href)
        # evaluate if a next page exists, if not then stop while loop
        # use loop to store list items then scan for the 'next' text
        page_list_items = [li.text.strip() for li in soup.find_all('li')]
        if 'next' not in page_list_items:
            break  # No more pages, stop while loop
        base_url = url.replace("index.html","")
        next_page = f"{base_url}page-{page_num}.html" #starts at page #2
        page = requests.get(next_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        page_num += 1

    base_url = 'http://books.toscrape.com/'
    # use urljoin to combine base url with relative url to get absolute URL
    full_links = []
    for url in urls:
        absolute_url = urljoin(base_url, url)
        #store absolute URL in full_links list
        full_links.append(absolute_url)
    
    #create list of csv column headers
    element_headings = ['product_page_url', 'universal_product_code', 'book_title', 'price_including_tax', 'price_excluding_tax', 'quantity_available', 'product_description', 'book_category', 'review_rating', 'image_url']
    
    #Open a new file to write to called ‘{category]-bookCategoryData.csv’ using this function
    saveCSVData(book_category, full_links, element_headings) 

# function to create CSV file and write data to it - Load the data
def saveCSVData(book_category, full_links, element_headings):
    title = f"{book_category}-bookCategoryData.csv"
    with open(title, 'w', encoding="utf-8", newline='') as csvfile:
        # Create a writer object with that file
        writer = csv.writer(csvfile, delimiter=',')
        # write headers on first row
        writer.writerow(element_headings) 
    
        # use a loop to go through each link and write its data found on onto each subsequent row
        for i in range(len(full_links)):
            # call function for each book page and store elements in bookData tuple
            bookData = (getSingleBookData(full_links[i]))
            # write the scraped data for each book on each row
            writer.writerow(bookData)

# function to extract all category URLs and metadata - Phase 3
def getCategories(url):
    home_page = requests.get(url)
    # create soup object
    soup = BeautifulSoup(home_page.content, 'html.parser')
    # locate navigation section with categories
    navigation_section = soup.find_all('ul', class_='nav nav-list') 
    # list for URLs
    category_urls = []
    # list for Categories
    category_list = []    
    for element in navigation_section:
        # loop through each <a> tag
        for link in element.find_all('a'):
            # retrieve URL (specified as local link/relative URL)
            href = link.get('href')
            # retrieve category listed as text
            category = link.text.strip()
            if href:
                # add relative URL to Urls list and text to Category list
                category_urls.append(href)
                category_list.append(category)
    base_url = 'http://books.toscrape.com/'
    # use urljoin to combine base url with relative url to get absolute URL
    full_links = []
    for url in category_urls:
        absolute_url = urljoin(base_url, url)
        # store absolute URL in full_links list
        full_links.append(absolute_url)
    # return both lists
    return full_links, category_list

# main function - orchestrates the workflow and initiates scraping process
def main():
    # call getCategories function to retrieve and return each Category link and name
    category_links, categories = list(getCategories('http://books.toscrape.com/'))

    # loop through lists and call the singleCategoryData function for each category link
    # start at index 1 ("Books" category is not valid and at index 0)
    for category_link, category in zip(category_links[1:], categories[1:]):
        singleCategoryData(category_link, category)

# call main function to kick off web scraping/ETL scripts
main()
