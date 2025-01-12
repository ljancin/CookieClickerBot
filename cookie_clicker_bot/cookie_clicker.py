import time
from datetime import datetime
import os
from BigNumber.BigNumber import BigNumber
import json
from timeit import default_timer as timer
import copy

from cookie_clicker_bot.buyables import Building, CompositeBuildingUpgrade, OtherUpgrade, CpsUpgrade, \
    BuildingUpgradeMultiplier, BuildingUpgradeAmount
from cookie_clicker_bot.numbers import BigNumberFromString, INFINITY, int_multipliers, ZERO_BIG_NUMBER
from cookie_clicker_bot.scripts import Scripts
from cookie_clicker_bot.tooltip_parser import TootlipParser
from cookie_clicker_bot.web_driver_manager import WebDriverManager

URL = 'https://orteil.dashnet.org/cookieclicker/'

SAVES_FOLDER = "saves"
SAVE_DATE_FORMAT = "%d_%m_%Y-%H_%M_%S"

CONFIG_PATH = "config.json"

GAME = "game"
TYPE = "type"
NEW = "new"
LAST = "last"
SAVE = "save"
MAX_WAIT_TIME = "max_wait_time"
TARGET_CLICK_PER_SECOND = "target_clicks_per_second"

UPGRADES_XPATH = f"//div[@id='upgrades' and contains(@class, 'storeSection upgradeBox')]"
UPGRADE_ELEMENTS_XPATH = f"//div[contains(@id, 'upgrade') and contains(@class, 'crate upgrade')]"
PRODUCTS_XPATH = f"//div[@id='products' and contains(@class, 'storeSection')]"
PRODUCT_ELEMENTS_XPATH = f"//div[contains(@id, 'product') and contains(@class, 'product unlocked')]"
COOKIE_XPATH = f"//button[@id='bigCookie']"
GOLDEN_COOKIE_PATH = f"//div[@class='shimmer']"
CLOSE_NOTIFICATIONS_XPATH = f"//div[@class='framed close sidenote']"

CLICKING_NAME = "Clicking"

CLICK_SEGMENT_DURATION = 2
CHECK_CLICK_FREQUENCY_INTERVAL_INITIAL = 1
CHECK_CLICK_FREQUENCY_INTERVAL_TARGET = 5

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, CONFIG_PATH)


class Config:
    def get_profile_path(self):
        def new_game():
            now = datetime.now()
            path = os.path.join(SAVES_FOLDER, now.strftime(SAVE_DATE_FORMAT))
            os.makedirs(path)
            return path

        if not os.path.exists(SAVES_FOLDER):
            os.makedirs(SAVES_FOLDER)

        saves = os.listdir(SAVES_FOLDER)

        if GAME in self.config:
            game = self.config[GAME]

            if TYPE in game:
                game_type = game[TYPE]
            else:
                raise KeyError("config: game type missing.")

            if game_type == NEW:
                profile_path = new_game()
            elif game_type == LAST:
                if len(saves) > 0:
                    profile_path = os.path.join(SAVES_FOLDER, saves[-1])
                else:
                    profile_path = new_game()
            elif game_type == SAVE:
                if SAVE in game:
                    save = game[SAVE]
                else:
                    raise KeyError("config: game save not specified.")

                profile_path = os.path.join(SAVES_FOLDER, save)
                if not os.path.exists(profile_path):
                    raise ValueError("config: specified save does not exist.")
            else:
                raise ValueError("config: invalid game type.")

        else:
            raise KeyError("config: game section missing.")

        return os.path.abspath(profile_path)

    def __init__(self):
        with open(config_path, 'r') as config_file:
            self.config = json.load(config_file)

            self.profile_path = self.get_profile_path()

            if MAX_WAIT_TIME in self.config:
                self.max_wait_time = self.config[MAX_WAIT_TIME]
            else:
                self.max_wait_time = None

            if TARGET_CLICK_PER_SECOND in self.config:
                self.target_clicks_per_second = self.config[TARGET_CLICK_PER_SECOND]
            else:
                self.target_clicks_per_second = None


class CookieClicker:
    tooltip_parser = TootlipParser()
    manager = None
    base_cps_dict = {}

    check_click_frequency_interval = CHECK_CLICK_FREQUENCY_INTERVAL_INITIAL

    def __init__(self):
        self.wait_after_click = None
        self.config = None
        self.buildings = []
        self.clicking = None

        self.upgrades = []
        self.upgrades_unknown = []

        self.bank = ZERO_BIG_NUMBER
        self.cookies_per_click = ZERO_BIG_NUMBER
        self.cps = ZERO_BIG_NUMBER
        self.clicking_cps = ZERO_BIG_NUMBER
        self.n_buffs = 0

        self.clicks_in_interval = 0
        self.avg_clicks_per_second = 0
        self.click_measure_start = None

    def start(self):
        self.config = Config()
        if self.config.target_clicks_per_second is not None and self.config.target_clicks_per_second > 0:
            self.wait_after_click = 1 / self.config.target_clicks_per_second

        self.manager = WebDriverManager(URL, self.config.profile_path)

        while True:
            try:
                res = self.manager.execute_script(Scripts.GET_GAME_TIME)
                if res is not None:
                    break
            except (Exception,):
                pass

        self.base_cps_dict = self.manager.execute_script(Scripts.GET_BUILDINGS_BASE_CPS)

    def simulation_copy(self):
        cookie_clicker_copy = CookieClicker()
        cookie_clicker_copy.base_cps_dict = self.base_cps_dict

        for b in self.buildings:
            cookie_clicker_copy.buildings.append(b.copy(cookie_clicker_copy))
        cookie_clicker_copy.clicking = self.clicking.copy(cookie_clicker_copy)

        for u in self.upgrades:
            cookie_clicker_copy.upgrades.append(u.copy(cookie_clicker_copy))

        cookie_clicker_copy.bank = copy.deepcopy(self.bank)
        cookie_clicker_copy.cps = copy.deepcopy(self.cps)

        cookie_clicker_copy.config = self.config

        return cookie_clicker_copy

    def click(self, duration):
        if self.click_measure_start is not None \
                and timer() - self.click_measure_start > self.check_click_frequency_interval:
            self.avg_clicks_per_second = BigNumber(self.clicks_in_interval / self.check_click_frequency_interval)

            if self.check_click_frequency_interval != CHECK_CLICK_FREQUENCY_INTERVAL_TARGET:
                self.check_click_frequency_interval = CHECK_CLICK_FREQUENCY_INTERVAL_TARGET

            if self.cookies_per_click == ZERO_BIG_NUMBER:
                self.cookies_per_click = BigNumberFromString(self.manager.execute_script(Scripts.GET_COOKIES_PER_CLICK))

            self.clicking_cps = self.avg_clicks_per_second * self.cookies_per_click

            self.clicks_in_interval = 0
            self.click_measure_start = timer()

        try:
            click_segment_start = timer()
            while timer() - click_segment_start < duration:
                cookie = self.manager.wait_until_clickable(COOKIE_XPATH)
                cookie.click()

                # start measuring only after first click succeeds
                if self.click_measure_start is None:
                    self.click_measure_start = timer()

                self.clicks_in_interval += 1

                if self.wait_after_click is not None and self.wait_after_click > 0:
                    time.sleep(self.wait_after_click)

        except (Exception,):
            # click failed
            return False

        return True

    def click_golden_cookie(self):
        # TODO wrath cookie
        golden_cookies = self.manager.get_elements(GOLDEN_COOKIE_PATH, False)

        golden_cookie_clicked = False
        while len(golden_cookies) > 0:
            for g in golden_cookies:
                try:
                    g.click()
                    golden_cookie_clicked = True
                except (Exception,):
                    pass

            golden_cookies = self.manager.get_elements(GOLDEN_COOKIE_PATH, False)

        return golden_cookie_clicked

    def update_buildings(self):
        try:
            products_element = self.manager.get_element(PRODUCTS_XPATH, True)
            product_elements = self.manager.get_elements(PRODUCT_ELEMENTS_XPATH, True, products_element)
        except (Exception,):
            self.buildings = []
            return

        self.buildings = []

        if self.avg_clicks_per_second > ZERO_BIG_NUMBER:
            self.clicking = Building(self, CLICKING_NAME, 1, INFINITY, self.clicking_cps, None)

        for p in product_elements:
            building_name = p.text.split('\n')[0]

            tooltip_html = self.manager.execute_script(Scripts.GET_BUILDING_TOOLTIP, building_name)
            self.tooltip_parser.Reset()
            self.tooltip_parser.feed(tooltip_html)
            count, price, totalCps = self.tooltip_parser.Get()

            self.buildings.append(Building(self, building_name, count, price, totalCps, p.get_attribute("id")))

    def UpgradeFactory(self, upgrade_element, upgrades_js):
        try:
            upgrade_data_id = upgrade_element.get_attribute("data-id")
            upgrade_id = upgrade_element.get_attribute("id")
        except (Exception,):
            return None

        try:
            upgrade_object = upgrades_js[upgrade_data_id]
        except (Exception,):
            return None

        price = BigNumber(upgrade_object["price"])

        def get_first_bold_section(input_html):
            startIndex = input_html.index("<b>")
            endIndex = input_html.index("</b>")
            return input_html[startIndex + len("<b>"):endIndex]

        name = upgrade_object["name"]
        desc = upgrade_object["desc"]

        if "building" not in upgrade_object:
            if "mouse and cursors are" in desc:
                multiplier = int_multipliers[get_first_bold_section(desc)]
                buildingsToUpgrade = [self.clicking, self.get_building("Cursor")]
                return CompositeBuildingUpgrade(self, name, multiplier - 1, price, buildingsToUpgrade,
                                                upgrade_id)

            elif "Clicking gains" in desc:
                boldSection = get_first_bold_section(desc)
                percentageIndex = boldSection.index("%")
                percentage = float(boldSection[1:percentageIndex]) / 100
                return BuildingUpgradeAmount(self, name, BigNumber(percentage) * self.cps * self.avg_clicks_per_second,
                                             price, self.get_building(CLICKING_NAME), upgrade_id)

            elif "Cookie production multiplier" not in desc:
                return OtherUpgrade(self, name, price, upgrade_id)

            else:
                # "+x%"
                # TODO check if first char is not a number
                percentage = int(get_first_bold_section(desc)[1:-1])
                return CpsUpgrade(self, name, percentage / 100, price, upgrade_id)
        else:
            multiplier = int_multipliers[get_first_bold_section(desc)]

            return BuildingUpgradeMultiplier(self, name, multiplier - 1, price,
                                             self.get_building(upgrade_object["building"]), upgrade_id)

    def update_upgrades(self):
        try:
            upgrades_js = self.manager.execute_script(Scripts.GET_UPGRADES)
        except (Exception,):
            self.upgrades = self.upgrades_unknown = []
            return

        if len(upgrades_js) == 0:
            self.upgrades = self.upgrades_unknown = []
            return

        try:
            updates_element = self.manager.get_element(UPGRADES_XPATH, True)
            upgrade_elements = self.manager.get_elements(UPGRADE_ELEMENTS_XPATH, True, updates_element)
        except (Exception,):
            self.upgrades = self.upgrades_unknown = []
            return

        self.upgrades = []
        self.upgrades_unknown = []

        for u in upgrade_elements:
            upgrade = self.UpgradeFactory(u, upgrades_js)
            if upgrade is None:
                continue

            if isinstance(upgrade, OtherUpgrade):
                self.upgrades_unknown.append(upgrade)
            else:
                self.upgrades.append(upgrade)

    def update_periodic(self):
        self.bank = BigNumberFromString(self.manager.execute_script(Scripts.GET_BANK))
        self.n_buffs = self.manager.execute_script(Scripts.GET_N_BUFFS)

    def update_for_calculations(self):
        self.cps = BigNumber(self.manager.execute_script(Scripts.GET_CPS)) + self.clicking_cps
        self.cookies_per_click = BigNumberFromString(self.manager.execute_script(Scripts.GET_COOKIES_PER_CLICK))
        self.clicking_cps = self.avg_clicks_per_second * self.cookies_per_click

        self.update_buildings()
        self.update_upgrades()

        try:
            close_notifications_button = self.manager.get_element(CLOSE_NOTIFICATIONS_XPATH, False)
            close_notifications_button.click()
        except (Exception,):
            pass

    def get_building(self, name):
        for b in self.buildings + [self.clicking]:
            if b.name == name:
                return b

    def get_buyable(self, name):
        for b in self.buildings + self.upgrades:
            if b.name == name:
                return b

    def get_evaluable_buyables(self):
        if self.config.max_wait_time is None:
            return self.buildings + self.upgrades

        return list(filter(lambda b: b.time_to_buy() <= self.config.max_wait_time, self.buildings + self.upgrades))
