import requests #library for making HTTP requests
from bs4 import BeautifulSoup #library used for parsing HTML and XML documents
import csv #module for CSV file handling
from urllib.parse import urljoin # urljoin function is used to construct an absolute URL
import os #module to help with OS function: file/directory operations and path manipulation

# ******************************************************************
# **** Use Python Basics for Market Analysis ** With OOP ***********
# ******************************************************************

# constant variable - used for joined URLs
BASE_URL = 'http://books.toscrape.com/'

# Responsibility: Represents a single book and extracts its data
class Book:
    def __init__(self, url):
        self.url = url
        self.soup = self._get_soup()
        self.data = self._extract_data()

    def _get_soup(self):
        response = requests.get(self.url)
        return BeautifulSoup(response.content, 'html.parser')

    def _extract_data(self):
        title = self.soup.select_one('h1').text
        category = self.soup.select_one('#default > div > div > ul > li:nth-child(3) > a').text
        description_tag = self.soup.select_one('#content_inner > article > p')
        description = description_tag.text if description_tag else 'None'

        table = self.soup.find('table', class_='table table-striped')
        headers = [th.text.strip() for th in table.find_all('th')]
        values = [td.text.strip() for td in table.find_all('td')]
        details = dict(zip(headers, values))

        rating = self.soup.select_one('[class^="star-rating "]').get('class')[1]
        image_src = self.soup.find('img')['src'].replace('../..', '')
        image_url = urljoin(BASE_URL, image_src)

        self._save_image(image_url, category)

        return [
            self.url,
            details.get('UPC'),
            title,
            details.get('Price (incl. tax)'),
            details.get('Price (excl. tax)'),
            details.get('Availability'),
            description,
            category,
            rating,
            image_url
        ]

    def _save_image(self, image_url, category):
        folder = f"{category}_images"
        os.makedirs(folder, exist_ok=True)
        img_data = requests.get(image_url).content
        img_name = os.path.basename(image_url)
        img_path = os.path.join(folder, img_name)
        with open(img_path, 'wb') as f:
            f.write(img_data)

    def get_data(self):
        return self.data

# Responsibility: Handles scraping of all books within a category
class CategoryScraper:
    def __init__(self, category_url, category_name):
        self.category_url = category_url
        self.category_name = category_name
        self.book_urls = self._get_book_urls()

    def _get_book_urls(self):
        urls = []
        page_url = self.category_url
        while True:
            soup = BeautifulSoup(requests.get(page_url).content, 'html.parser')
            containers = soup.find_all('div', class_='image_container')
            for container in containers:
                link = container.find('a')['href'].replace('../../..', 'catalogue')
                urls.append(urljoin(BASE_URL, link))

            if not soup.find('li', class_='next'):
                break
            page_num = len(urls) // 20 + 2
            page_url = self.category_url.replace('index.html', f'page-{page_num}.html')
        return urls

    def scrape_books(self):
        headers = [
            'product_page_url', 'universal_product_code', 'book_title',
            'price_including_tax', 'price_excluding_tax', 'quantity_available',
            'product_description', 'book_category', 'review_rating', 'image_url'
        ]
        filename = f"{self.category_name}-bookCategoryData.csv"
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for url in self.book_urls:
                book = Book(url)
                writer.writerow(book.get_data())

# Responsibility: Orchestrates the entire scraping process across categories
class BookScraper:
    def __init__(self, homepage_url):
        self.homepage_url = homepage_url
        self.categories = self._get_categories()

    def _get_categories(self):
        soup = BeautifulSoup(requests.get(self.homepage_url).content, 'html.parser')
        nav = soup.find('ul', class_='nav nav-list')
        links = nav.find_all('a')
        categories = []
        for link in links[1:]:  # skip "Books" category
            href = link.get('href')
            name = link.text.strip()
            full_url = urljoin(BASE_URL, href)
            categories.append((full_url, name))
        return categories

    def run(self):
        for url, name in self.categories:
            print(f"Scraping category: {name}")
            scraper = CategoryScraper(url, name)
            scraper.scrape_books()

# Gatekeeper condition - runs the script if not being imported
if __name__ == "__main__":
    BookScraper(BASE_URL).run()