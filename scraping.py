import sys; import os
import time

from selenium import webdriver
from pyvirtualdisplay import Display


class TranscriptSpider():
    def __init__(self, driver_fp, url_to_crawl):
        self.driver_fp = driver_fp
        self.url_to_crawl = url_to_crawl
        self.all_items = []
        self.data = None

    def start_driver(self):
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.driver = webdriver.Chrome(executable_path=self.driver_fp)

    def close_driver(self):
        self.display.stop()
        self.driver.quit()

        
    def get_page(self, url):
        self.driver.get(url)
        time.sleep(2.5)

        
    def grab_items(self):
        self.data = self.driver.page_source
            
            
    def parse(self):
        self.start_driver()
        self.get_page(self.url_to_crawl)
        self.grab_items()
        self.close_driver()