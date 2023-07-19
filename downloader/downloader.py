from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class DownloaderDriver(webdriver.Chrome):
    def __init__(self, detach=False):
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", detach)
        super().__init__(options=chrome_options)
        self.__filters = {'include': [], 'exclude': []}

    @staticmethod
    def clean_url(url):
        if url[-1] != '/':
            url += '/'
        return url

    def list_of_chile_urls(self, base_url):
        self.get(base_url)
        base_url = self.clean_url(base_url)

        urls = []
        for tr in self.find_elements(By.CSS_SELECTOR, 'table tbody tr'):
            filter_flag = False
            link = tr.find_element(By.CSS_SELECTOR, 'a')
            for filter_item in self.__filters['include']:
                if filter_item not in link.text:
                    filter_flag = True
                    break
            for filter_item in self.__filters['exclude']:

                if filter_item in link.text:
                    filter_flag = True
                    break
            if filter_flag:
                continue

            children = tr.find_element(By.CSS_SELECTOR, 'td.s').text
            if "-  " == children:
                children = []

            url = link.get_attribute('href')
            if 'http' not in url:
                url = base_url + url
            urls.append({'name': link.text, 'url': url, 'children': children})
        return urls

    def crawl_forward(self, urls):
        self.__filters['exclude'] .append("Parent")
        for item in urls:
            if isinstance(item['children'], list):
                child_urls = self.list_of_chile_urls(item['url'])
                self.crawl_forward(child_urls)
                urls[urls.index(item)]['children'] = child_urls
        return urls

    def get_download_url(self, url):
        self.get(url)

    def include_filters(self, filters_list):
        self.__filters['include'] = filters_list

    def exclude_filters(self, filters_list):
        self.__filters['exclude'] = filters_list
