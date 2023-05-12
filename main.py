import csv
import logging

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class Crawler:

    def __init__(self):
        self.table = None
        self.browser = None
        '''filename='web_scraping_log.log','''
        logging.basicConfig(encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    def init_browser(self):
        options = Options()
        options.add_argument('--headless')
        self.browser = webdriver.Chrome(options=options)

    def get_bs4(self, url):
        self.browser.get(url)
        html = self.browser.page_source
        return BeautifulSoup(html, 'html5lib')

    def get_next_page(self, url):
        bs = self.get_bs4(url)
        next_page_url = bs.find('a', {'class': 'next'}).attrs['href']
        current_page_url = next_page_url
        return current_page_url

    @staticmethod
    def parse(info_field):
        field_content = []
        for info in info_field.children:
            if type(info) == NavigableString:
                info = info.strip().replace('\n', '').replace('\t', '').replace('\xa0', '').replace('\xe9', '')
                field_content.append(info)
        return field_content

    def get_contacts(self, search_results_url, full_contacts_info_page_urls):
        # logging.debug('Current url:' + str(search_results_url))
        for full_contacts_info_page_url in full_contacts_info_page_urls:
            full_contact_info, full_contact_info_page_href = self.get_contact_info_and_href(full_contacts_info_page_url)
            # Get shopname
            parsed_shopname = self.get_shopname(full_contact_info_page_href)
            # Get owner
            parsed_owner = self.get_owner(full_contact_info)
            # Get address
            parsed_address, parsed_address_contents = self.get_address(full_contact_info)
            # Get nation
            parsed_nation = parsed_address_contents[-1]
            try:
                # Get telephone
                telephones = self.get_telephone(full_contact_info)
            except AttributeError:
                telephones = self.get_mobile(full_contact_info)
            # Get email
            parsed_email = self.get_email(full_contact_info)
            try:
                # Get website
                parsed_website = self.get_website(full_contact_info)
            except AttributeError:
                parsed_website = None
            try:
                # Get instagram
                parsed_insta = self.get_instagram(full_contact_info)
            except AttributeError:
                parsed_insta = None
            row = self.save_to_dictionary(parsed_address, parsed_email, parsed_insta, parsed_nation, parsed_owner,
                                          parsed_shopname, parsed_website, telephones)
            self.debug(row, search_results_url)

    def get_contact_info_and_href(self, full_contacts_info_page_url):
        full_contact_info_page_href = self.get_bs4(full_contacts_info_page_url.a.attrs['href'])
        full_contact_info = full_contact_info_page_href.find('div', {'class', 'contact-wrap'})
        return full_contact_info, full_contact_info_page_href

    def save_to_dictionary(self, parsed_address, parsed_email, parsed_insta, parsed_nation, parsed_owner,
                           parsed_shopname, parsed_website, telephones):
        row = {'SHOP NAME': parsed_shopname, 'OWNER': parsed_owner, 'ADDRESS': parsed_address,
               'NATION': parsed_nation,
               'TELEPHONES': telephones, 'E-MAIL': parsed_email, 'WEBSITE': parsed_website,
               'INSTAGRAM': parsed_insta, }
        self.table.append(row)
        return row

    def get_instagram(self, full_contact_info):
        insta_tag = full_contact_info.find('dt', {'class': {'social-icon', 'instagram'}}).find_next('dd').a
        parsed_insta = self.parse(insta_tag)
        parsed_insta = ''.join(parsed_insta)
        return parsed_insta

    def get_website(self, full_contact_info):
        website_tag = full_contact_info.find('dt', {'class': 'website'}).find_next('dd').a
        parsed_website = self.parse(website_tag)
        parsed_website = ''.join(parsed_website)
        return parsed_website

    def get_email(self, full_contact_info):
        email_tag = full_contact_info.find('dt', {'class': 'email'}).find_next('dd').a
        parsed_email = self.parse(email_tag)
        parsed_email = ''.join(parsed_email)
        return parsed_email

    def get_mobile(self, full_contact_info):
        return full_contact_info.find('dt', {'class': 'mobile'}).find_next('dd').a.get_text()

    def get_telephone(self, full_contact_info):
        return full_contact_info.find('dt', {'class': 'phone'}).find_next('dd').a.get_text()

    def get_address(self, full_contact_info):
        address_tags = full_contact_info.find('div', {'class': 'address'})
        parsed_address_contents = self.parse(address_tags)
        parsed_address = ' '.join(parsed_address_contents[:-1])
        return parsed_address, parsed_address_contents

    def get_owner(self, full_contact_info):
        owner_tag = full_contact_info.find('dt', {'class': 'contact'}).find_next('dd')
        parsed_owner = self.parse(owner_tag)
        parsed_owner = ''.join(parsed_owner)
        return parsed_owner

    def get_shopname(self, full_contact_info_page_href):
        shopname_tag = full_contact_info_page_href.find('header', {'id': 'content-header'}).h1
        shopname = self.parse(shopname_tag)
        parsed_shopname = ''.join(shopname)
        return parsed_shopname

    @staticmethod
    def debug(row, search_results_url):
        logging.debug('Current url:' + str(search_results_url))
        row = dict(row)
        logging.debug('-' * 70)
        for key, value in row.items():
            logging.debug(key + ': ' + str(value))
        logging.debug('-' * 70)

    def record_to_csv_file(self, filename):
        csv_columns = []
        for column in self.table[0].keys():
            csv_columns.append(column)
        csv_file = filename
        try:
            with open(csv_file, 'w', newline='') as csv_file_object:
                writer = csv.DictWriter(csv_file_object, dialect='excel', fieldnames=csv_columns, delimiter=';')
                writer.writeheader()
                for data in self.table:
                    writer.writerow(data)
        except IOError:
            print('I/O error')

    def start_parse(self, url):
        self.init_browser()
        current_page_url = url
        self.table = []
        try:
            while current_page_url != '':
                bs = self.get_bs4(current_page_url)
                full_contacts_info_page_urls = bs.find_all('div', {'class', 'more'})
                self.get_contacts(current_page_url, full_contacts_info_page_urls)
                current_page_url = self.get_next_page(current_page_url)
        except KeyboardInterrupt:
            print("Program is finishing...")
        self.browser.quit()
        filename = 'iLab_table.xlsx'
        self.record_to_csv_file('iLab_table.csv')
        print(f"File was written to file {filename}")
        print('Program was closed.')


crawler = Crawler()
start_page = 'https://ilab.org/page/affiliate-search-results?business=&bookseller=&country=&city=&specialty' \
             '=&association=&submit=&page=1'
crawler.start_parse(start_page)
