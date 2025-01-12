import os

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from cookie_clicker_bot.scripts import SCRIPTS_ROOT

WAIT_TIMEOUT = 1


class WebDriverManager:

    def __init__(self, url, profile_path):
        chrome_options = Options()

        chrome_options.add_argument(f"user-data-dir={profile_path}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(url)
        self.actions = ActionChains(self.driver)

        self.scripts = {}

    def wait(self, xPath, condition, parent=None):
        if parent is None:
            parent = self.driver

        conditionSatisfied = condition((By.XPATH, xPath))
        return WebDriverWait(parent, WAIT_TIMEOUT).until(conditionSatisfied)

    def wait_until_present(self, xPath, parent=None):
        return self.wait(xPath, ec.presence_of_element_located, parent)

    def wait_until_clickable(self, xPath, parent=None):
        return self.wait(xPath, ec.element_to_be_clickable, parent)

    def get_element(self, xPath, wait, parent=None):
        if parent is None:
            parent = self.driver

        if wait:
            self.wait_until_present(xPath, parent)

        return parent.find_element(By.XPATH, xPath)

    def get_elements(self, xPath, wait, parent=None):
        if parent is None:
            parent = self.driver

        if wait:
            self.wait_until_present(xPath, parent)

        return parent.find_elements(By.XPATH, xPath)

    def execute_script(self, script_name, arg=None):
        if script_name not in self.scripts:
            script_path = os.path.join(SCRIPTS_ROOT, script_name)
            with open(script_path, 'r') as script:
                self.scripts[script_name] = script.read()

        return self.driver.execute_script(self.scripts[script_name], arg)

    def move_to_element(self, element):
        self.actions.move_to_element(element).perform()
