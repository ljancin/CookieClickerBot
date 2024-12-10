import os
import threading
from enum import Enum, auto
from threading import Thread

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from datetime import datetime
import time


class Multiplier(Enum):
    NONE = 0
    million = 2
    billion = auto()
    trillion = auto()
    quadrillion = auto()
    quintillion = auto()
    sextillion = auto()
    septillion = auto()
    octillion = auto()
    nonillion = auto()
    decillion = auto()
    undecillion = auto()
    duodecillion = auto()
    tredecillion = auto()

    def __sub__(self, other):
        if isinstance(other, Multiplier):
            return Multiplier(self.value - other.value)
        elif isinstance(other, int):
            return Multiplier(self.value - other)

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Multiplier):
            return self.value == other.value
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Multiplier):
            return self.value > other.value
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Multiplier):
            return self.value < other.value
        return NotImplemented


intMultipliers = {
    "twice": 2,
    "three times": 3,
    "four times": 4,
    "five times": 5,
}


class NumberWithMultiplier:
    MULTIPLIER_STEP = 1000
    MIN_MULTIPLIER = 1_000_000

    @staticmethod
    def FromString(stringRepresentation):
        def stringToFloat(floatString):
            return float(floatString.replace(",", ''))

        stringRepresentationSplit = stringRepresentation.split(" ")
        if len(stringRepresentationSplit) == 1:
            return NumberWithMultiplier(stringToFloat(stringRepresentation), Multiplier.NONE)

        numberString = stringRepresentationSplit[0]
        multiplierString = stringRepresentationSplit[1]

        return NumberWithMultiplier(stringToFloat(numberString), Multiplier[multiplierString])

    def __init__(self, number=0.0, multiplier=Multiplier.NONE):
        self.number = number
        self.multiplier = multiplier

        # premali number
        while self.number < 1 and self.multiplier > Multiplier.million:
            self.number *= NumberWithMultiplier.MULTIPLIER_STEP
            self.multiplier -= 1
        if self.number < 1 and self.multiplier == Multiplier.million:
            self.number *= NumberWithMultiplier.MIN_MULTIPLIER
            self.multiplier = Multiplier.NONE

        # preveliki number
        if self.number >= NumberWithMultiplier.MIN_MULTIPLIER and self.multiplier == Multiplier.NONE:
            self.number /= NumberWithMultiplier.MIN_MULTIPLIER
            self.multiplier = Multiplier.million

        if self.multiplier != Multiplier.NONE:
            while self.number >= NumberWithMultiplier.MULTIPLIER_STEP:
                self.number /= NumberWithMultiplier.MULTIPLIER_STEP
                self.multiplier += 1

    def __add__(self, other):
        def EqualizeMultipliers(smaller, bigger):
            if smaller.multiplier == Multiplier.NONE:
                smaller.number /= NumberWithMultiplier.MIN_MULTIPLIER
                smaller.multiplier = Multiplier.million

            while bigger.multiplier > smaller.multiplier:
                smaller.number /= NumberWithMultiplier.MULTIPLIER_STEP
                smaller.multiplier += 1

        if self.multiplier > other.multiplier:
            EqualizeMultipliers(other, self)
        elif self.multiplier < other.multiplier:
            EqualizeMultipliers(self, other)

        return NumberWithMultiplier(self.number + other.number, self.multiplier)

    def __mul__(self, other):
        numberNew = self.number * other
        multiplierNew = self.multiplier

        return NumberWithMultiplier(self.number * other, self.multiplier)

    def __truediv__(self, other):
        if isinstance(other, NumberWithMultiplier):
            numberNew = self.number / other.number
            nMultiplierStepsDifference = self.multiplier.value - other.multiplier.value

            # other je veci od self nMultiplierStepsDifference * 1000 puta
            while nMultiplierStepsDifference < 0:
                numberNew /= NumberWithMultiplier.MULTIPLIER_STEP
                nMultiplierStepsDifference += 1

            return NumberWithMultiplier(numberNew, Multiplier(nMultiplierStepsDifference))
        else:
            return NumberWithMultiplier(self.number / other, self.multiplier)

    def __eq__(self, other):
        return self.number == other.number and self.multiplier == other.multiplier

    def __lt__(self, other):
        if self.multiplier < other.multiplier:
            return True

        if self.multiplier == other.multiplier:
            return self.number < other.number

        return False

    def __gt__(self, other):
        if self.multiplier > other.multiplier:
            return True

        if self.multiplier == other.multiplier:
            return self.number > other.number

        return False

    def __str__(self):
        numberString = str(self.number)
        if self.multiplier == Multiplier.NONE:
            return numberString

        return numberString + " " + str(self.multiplier)[len("Multipiler."):]


'''one = NumberWithMultiplier(1)
point5 = NumberWithMultiplier(0.5)
million = NumberWithMultiplier(1, Multiplier.Million)
billion = NumberWithMultiplier(1, Multiplier.Billion)
trillion = NumberWithMultiplier(1, Multiplier.Trillion)
millionNonNormalized = NumberWithMultiplier(1000000)
point5Million = NumberWithMultiplier(0.5, Multiplier.Million)
point5Billion = NumberWithMultiplier(0.5, Multiplier.Billion)

one_times_million = one * 1000000
one_over_million = one / million
million_over_trillion = million / trillion
trillion_over_point5Billion = trillion / point5Billion'''

PROFILES_FOLDER = "profiles"
if not os.path.exists(PROFILES_FOLDER):
    os.makedirs(PROFILES_FOLDER)

NEW_GAME = False
if NEW_GAME:
    now = datetime.now()
    profile_path = os.path.join(PROFILES_FOLDER, now.strftime("%d_%m_%Y-%H_%M_%S"))
    os.makedirs(profile_path)
else:
    profiles = os.listdir(PROFILES_FOLDER)
    profile_path = os.path.join(PROFILES_FOLDER, profiles[-1])

# firefox_options = Options()
# firefox_options.add_argument("-profile")
# firefox_options.add_argument(profile_path)

chrome_options = Options()
profile_path = os.path.abspath(profile_path)
chrome_options.add_argument(f"user-data-dir={profile_path}")

# driver = webdriver.Firefox(options=firefox_options)
driver = webdriver.Chrome(options=chrome_options)
driver.get('https://orteil.dashnet.org/cookieclicker/')
actions = ActionChains(driver)


def GetElement(xPath, wait, parent=None):
    if parent is None:
        parent = driver

    res = None
    try:
        res = parent.find_element(By.XPATH, xPath)
    except (Exception,):
        if wait:
            elementPresent = EC.presence_of_element_located((By.XPATH, xPath))
            # TODO magic number
            WebDriverWait(parent, 5).until(elementPresent)
            res = parent.find_element(By.XPATH, xPath)

    return res


def GetElements(xPath, wait, parent=None):
    if parent is None:
        parent = driver

    res = parent.find_elements(By.XPATH, xPath)

    if wait and res == []:
        elementPresent = EC.presence_of_element_located((By.XPATH, xPath))
        WebDriverWait(parent, 5).until(elementPresent)
        res = parent.find_elements(By.XPATH, xPath)

    return res


class Buyable:
    def __init__(self, element):
        self.element = element

    def Buy(self):
        elementClass = self.element.get_attribute("class")
        if "enabled" not in elementClass:
            return False

        driver.execute_script("arguments[0].scrollIntoView();", self.element)
        self.element.click()
        return True


class Building(Buyable):
    def __init__(self, name, count, price, totalCps, element):
        super().__init__(element)
        self.name = name
        self.count = count
        self.price = price
        self.totalCps = totalCps

    def Sell(self):
        pass

    def GetProfitability(self):
        if self.count == 0:
            return NumberWithMultiplier(0)

        gain = self.totalCps / self.count
        return gain / self.price


class Upgrade(Buyable):
    def __init__(self, amount, price, element):
        super().__init__(element)
        self.amount = amount
        self.price = price


class BuildingUpgrade(Upgrade):
    def __init__(self, amount, price, building, element):
        super().__init__(amount, price, element)
        self.building = building

    def GetProfitability(self):
        gain = self.building.totalCps * self.amount
        return gain / self.price


class CpsUpgrade(Upgrade):
    def __init__(self, amount, price, element):
        super().__init__(amount, price, element)

    def GetProfitability(self):
        # TODO referenca na cps?
        global cps
        gain = cps * self.amount
        return gain / self.price


buildings = []
upgrades = []
bank = NumberWithMultiplier()
cps = NumberWithMultiplier()


def UpdateBuildings(buildingDescriptions, productElements):
    global buildings
    buildings = []

    if len(buildingDescriptions) != len(productElements):
        raise Exception

    for i in range(len(buildingDescriptions)):
        description = buildingDescriptions[i]

        price = NumberWithMultiplier.FromString(description[0])
        name = description[1]
        count = int(description[2].split(" ")[1])

        if count > 0:
            description5Split = description[5].split(" ")
            producingIndex = description5Split.index("producing")
            perIndex = description5Split.index("per")

            totalCpsArray = description5Split[producingIndex + 1:perIndex - 1]
            totalCpsString = " ".join(totalCpsArray)
            totalCps = NumberWithMultiplier.FromString(totalCpsString)
        else:
            totalCps = NumberWithMultiplier()

        buildings.append(Building(name, count, price, totalCps, productElements[i]))


def UpdateUpgrades(upgradeDescriptions, upgradeElements):
    global upgrades
    upgrades = []
    for i in range(len(upgradeDescriptions)):
        description = upgradeDescriptions[i]

        price = NumberWithMultiplier.FromString(description[0])
        description3Split = description[3].split(" ")

        if description[2] == "Cookie":
            percentageString = description3Split[-1][:-2]
            multiplier = float(percentageString) / 100

            upgrades.append(CpsUpgrade(multiplier, price, upgradeElements[i]))
        else:
            try:
                description3Split.index("efficient.")
            except (Exception,):
                continue

            buildingStringPlural = description3Split[0]
            if buildingStringPlural == "Factories":
                buildingString = "Factory"
            else:
                buildingString = buildingStringPlural[:-1]
            building = None
            for b in buildings:
                if b.name == buildingString:
                    building = b
                    break

            areIndex = description3Split.index("are")
            asIndex = description3Split.index("as")
            multiplierArray = description3Split[areIndex + 1:asIndex]
            multiplierString = " ".join(multiplierArray)
            multiplier = intMultipliers[multiplierString]

            upgrades.append(BuildingUpgrade(multiplier, price, building, upgradeElements[i]))


def CalculateChoices():
    return sorted(buildings + upgrades, key=lambda b: b.GetProfitability(), reverse=True)


UPGRADE_TOOLTIP_XPATH = "//div[@id='tooltipCrate']"
BUILDING_TOOLTIP_XPATH = f"//div[@id='tooltipBuilding']"

UPGRADES_XPATH = f"//div[@id='upgrades' and contains(@class, 'storeSection upgradeBox')]"
upgradesElement = GetElement(UPGRADES_XPATH, True)
UPGRADE_ELEMENTS_XPATH = f"//div[contains(@id, 'upgrade') and contains(@class, 'crate upgrade')]"

PRODUCTS_XPATH = f"//div[@id='products' and contains(@class, 'storeSection')]"
productsElement = GetElement(PRODUCTS_XPATH, True)
# enabled ce bit false ak nemas dovoljno za kupit
# PRODUCT_ELEMENTS_XPATH = f"//div[contains(@id, 'product') and contains(@class, 'product unlocked enabled')]"
PRODUCT_ELEMENTS_XPATH = f"//div[contains(@id, 'product') and contains(@class, 'product unlocked')]"

COOKIE_XPATH = f"//button[@id='bigCookie']"
# cookie = GetElement(COOKIE_XPATH, True)
cookie = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, COOKIE_XPATH)))


def CookieClicker():
    while True:
        # if not idle continue
        cookie.click()
        time.sleep(1000 / 60 / 1000)


# driver.execute_script("debugger;")
# res = driver.execute_script("return Game;")

# driver.execute_cdp_cmd("Debugger.enable", {})  # Enable the Debugger domain
# driver.execute_cdp_cmd("Debugger.pause", {})  # Pause JavaScript execution

# driver.execute_script("debugger;")

def pause_js_execution():
    # Enable the Debugger domain in Chrome DevTools Protocol
    driver.execute_cdp_cmd("Debugger.enable", {})
    # Pause JavaScript execution in the browser (non-blocking for Python)
    driver.execute_cdp_cmd("Debugger.pause", {})
    print("JavaScript execution paused.")


def resume_js_execution():
    # Resume JavaScript execution after some time
    time.sleep(2)  # Wait for 2 seconds before resuming JavaScript execution
    driver.execute_cdp_cmd("Debugger.resume", {})
    print("JavaScript execution resumed.")


#js_pause_thread = threading.Thread(target=pause_js_execution)
#js_pause_thread.start()

#js_resume_thread = threading.Thread(target=resume_js_execution)
#js_resume_thread.start()


res = driver.execute_script("return Game.Objects.Cursor.tooltip()")

# detect click -> refresh (ak kupi rucno)

'''
Object.keys(Game.UpgradesById)
    .filter(key => Game.UpgradesById[key].bought === 0 && Game.UpgradesById[key].unlocked === 1) 
    .reduce((acc, key) => {
        acc[key] = Game.UpgradesById[key];
        return acc;
    }, {});
'''

# Game.computedMouseCps -> cookies per click
# Game.cookies
# Game.cookiesPs
# Game.cookiesPsRaw

thread = Thread(target=CookieClicker)
# thread.start()

while True:
    # TODO procitaj ovo iz javascripta

    try:
        upgradeElements = GetElements(UPGRADE_ELEMENTS_XPATH, True, upgradesElement)
        productElements = GetElements(PRODUCT_ELEMENTS_XPATH, True, productsElement)
    except (Exception,):
        continue

    print("_________________________________")

    TITLE_XPATH = f"//div[@id='cookies' and @class='title']"
    titleElement = GetElement(TITLE_XPATH, True)
    titleElementText = str(titleElement.text)
    titleElementText = titleElementText.replace("\n", " ")
    titleElementTextSplit = titleElementText.split(" ")

    cookiesIndex = titleElementTextSplit.index("cookies")
    # TODO ovo se ponavlja, izdvoji u fju
    bankArray = titleElementTextSplit[:cookiesIndex]
    bankString = ' '.join(bankArray)
    bank = NumberWithMultiplier.FromString(bankString)

    secondIndex = titleElementTextSplit.index("second:")
    cpsArray = titleElementTextSplit[secondIndex + 1:]
    cpsString = ' '.join(cpsArray)
    cps = NumberWithMultiplier.FromString(cpsString)

    buildingDescriptions = []

    for p in productElements:
        '''
        buildingName = p.text.split('\n')[0]

        try:
            actions.move_to_element(p).perform()
        except (Exception,):
            driver.execute_script("arguments[0].scrollIntoView();", p)'''

        driver.execute_script("arguments[0].scrollIntoView();", p)
        actions.move_to_element(p).perform()

        # actions.move_to_element(p).perform()
        tooltipElement = GetElement(BUILDING_TOOLTIP_XPATH, True)

        buildingDescriptionSplit = tooltipElement.text.split('\n')
        # while buildingDescriptionSplit[1] != buildingName:
        #    actions.move_to_element(p).perform()
        #    tooltipElement = GetElement(BUILDING_TOOLTIP_XPATH, True)

        buildingDescriptions.append(buildingDescriptionSplit)

    UpdateBuildings(buildingDescriptions, productElements)

    upgradeDescriptions = []
    for u in upgradeElements:
        try:
            actions.move_to_element(u).perform()
        except (Exception,):
            try:
                driver.execute_script("arguments[0].scrollIntoView();", u)
            except (Exception,):
                print("scroll error")
                pass
            actions.move_to_element(u).perform()

        tooltipElement = GetElement(UPGRADE_TOOLTIP_XPATH, True)

        upgradeDescriptions.append(tooltipElement.text.split('\n'))

    UpdateUpgrades(upgradeDescriptions, upgradeElements)

    choices = CalculateChoices()
    boughtSomething = False
    for c in choices:
        if c.Buy():
            boughtSomething = True
            break

    if not boughtSomething:
        time.sleep(5)

    # TODO odmah kupi ostale upgrade cim imas dovoljno
    # TODO napravi uvjet kad treba refreshati kaj
    # TODO thread sa klikanjem po cookieju

    # buildings[0].Buy()
    # upgrades[0].Buy()

# statsGeneral
# statsButton
# nakon par sekundi neaktivnosti pocni klikat i opet odi u stats menu
