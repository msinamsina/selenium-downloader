from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class SpyderInterface(webdriver.Chrome):

    @classmethod
    def __new__(cls, *args, **kwargs):
        cls.__afc_hook = []
        cls.__register_all_hooks()
        return super().__new__(cls)

    @classmethod
    def __register_all_hooks(cls):
        methods = cls.__dict__
        for method in methods:
            print(method)
            if method.startswith('afc_hook_'):
                cls.register_afc_hook(getattr(cls, method))

    def __init__(self, detach=False):
        """This method is used to initialize the class. """
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", detach)
        super().__init__(options=chrome_options)
        self.__filters = {'include': set(), 'exclude': set()}

    @staticmethod
    def clean_url(url):
        if url[-1] != '/':
            url += '/'
        return url

    def list_urls(self, base_url, selector=None):
        """This method is used to find all the links in a page.

        Parameters
        ----------
        base_url : str
            The URL of the page.
        selector : str
            The CSS selector of the links.

        Returns
        -------
        list
            A list of the links.
        """
        links = []
        self.get(base_url)
        base_url = self.clean_url(base_url)

        if selector is None:
            selector = 'a'
            for link in self.find_elements(By.CSS_SELECTOR, selector):
                links.append(link.get_attribute('href'))
                return links
        else:
            # parent selector
            for elem in self.find_elements(By.CSS_SELECTOR, selector):
                link = elem.find_element(By.CSS_SELECTOR, 'a')
                if self.__filter_link_text(link):
                    continue
                url = self.__convert_relative_url_to_absolute(base_url, link.get_attribute('href'))
                elem_dict = {'name': link.text, 'url': url}
                elem_dict.update(self.after_find_child_hook(elem))
                links.append(elem_dict)
            return links

    def after_find_child_hook(self, child):
        elem_dict = {}
        for hook in self.__afc_hook:
            elem_dict.update(hook(child))
        return elem_dict

    @classmethod
    def register_afc_hook(cls, hook):
        """Register after find child hook

        Parameters
        ----------
        hook : function
            The function to be called after finding a child.
            The function should take one argument, which is the child element.
            The function should return a dictionary.


        Returns
        -------
        None

        Notes
        -----
        After running this method, the function will be called after finding a child.

        """
        cls.__afc_hook.append(hook)

    @staticmethod
    def __convert_relative_url_to_absolute(base, url):
        if 'http' not in url:
            url = base + url
        return url

    def __filter_link_text(self, link):
        for filter_item in self.__filters['include']:
            if filter_item not in link.text:
                return True
        for filter_item in self.__filters['exclude']:
            if filter_item in link.text:
                return True
        return False

    def include_filters(self, filters_list):
        if isinstance(filters_list, str):
            filters_list = [filters_list]
        self.__filters['include'] |= set(filters_list)

    def exclude_filters(self, filters_list):
        if isinstance(filters_list, str):
            filters_list = [filters_list]
        self.__filters['exclude'] |= set(filters_list)


class Spyder(SpyderInterface):
    def list_of_chile_urls(self, base_url):
        """This method is used to find all
        """
        return self.list_urls(base_url, 'table tbody tr')

    @staticmethod
    def afc_hook_is_dir(elem):
        if elem.find_element(By.CSS_SELECTOR, 'td.s').text == '-  ':
            return {'is_dir': True, 'children': []}
        else:
            return {'is_dir': False, 'children': None}

    def crawl_forward(self, urls):
        self.exclude_filters(['Parent'])
        for item in urls:
            if isinstance(item['children'], list):
                child_urls = self.list_of_chile_urls(item['url'])
                self.crawl_forward(child_urls)
                urls[urls.index(item)]['children'] = child_urls
        return urls

    def get_download_url(self, url):
        self.get(url)
