from BigNumber.BigNumber import BigNumber

from cookie_clicker_bot.scripts import Scripts
import time

BUILDING_TOOLTIP_XPATH = "//div[@id='tooltipBuilding']"
UPGRADE_TOOLTIP_XPATH = "//div[@id='tooltipCrate']"
WAIT_AFTER_HOVER = 0.1

CURSOR_BASE_CPS = 0.1
BUILDING_PRICE_MULTIPLIER = 1.15


class Buyable:
    def __init__(self, cookie_clicker, name, gain, price, elementId):
        self.cookie_clicker = cookie_clicker
        self.name = name
        self.gain = gain
        self.price = price
        self.elementId = elementId

    def buy(self):
        XPATH = f"//div[@id='{self.elementId}']"
        element = self.cookie_clicker.manager.get_element(XPATH, True)

        element_class = element.get_attribute("class")
        if "enabled" not in element_class:
            return False

        self.cookie_clicker.manager.execute_script(Scripts.SCROLL_INTO_VIEW, element)

        try:
            element.click()
            return True
        except (Exception,):
            return False

    def buy_simulation(self):
        self.cookie_clicker.bank -= self.price
        self.cookie_clicker.cps += self.gain

    def can_buy(self):
        return self.cookie_clicker.bank >= self.price

    def get_profitability(self):
        return self.gain / self.price

    def time_to_buy(self):
        if self.price <= self.cookie_clicker.bank:
            return 0

        missing = self.price - self.cookie_clicker.bank
        return float(missing / self.cookie_clicker.cps)


class Building(Buyable):
    def __init__(self, cookie_clicker, name, count, price, total_cps, elementId):
        if count == 0:
            if name == "Cursor":
                gain = BigNumber(CURSOR_BASE_CPS)
            else:
                gain = BigNumber(cookie_clicker.base_cps_dict[name]["baseCps"])
        else:
            gain = total_cps / count

        super().__init__(cookie_clicker, name, gain, price, elementId)

        self.count = count
        self.total_cps = total_cps

    def copy(self, cookie_clicker):
        return Building(cookie_clicker, self.name, self.count, self.price, self.total_cps, None)

    def buy_simulation(self):
        super().buy_simulation()

        self.price *= BUILDING_PRICE_MULTIPLIER

    def sell(self):
        pass

    def get_profitability(self):
        return super().get_profitability()


class Upgrade(Buyable):
    def __init__(self, cookie_clicker, name, gain, price, elementId):
        super().__init__(cookie_clicker, name, gain, price, elementId)

    def copy(self, cookie_clicker):
        return Upgrade(cookie_clicker, self.name, self.gain, self.price, None)

    def buy(self):
        XPATH = f"//div[@id='{self.elementId}']"
        element = self.cookie_clicker.manager.get_element(XPATH, True)

        try:
            elementClass = element.get_attribute("class")
        except (Exception,):
            return False

        if "enabled" not in elementClass:
            return False

        self.cookie_clicker.manager.execute_script(Scripts.SCROLL_INTO_VIEW, element)

        # TODO extract this
        try:
            self.cookie_clicker.manager.move_to_element(element)

            self.cookie_clicker.manager.wait_until_present(UPGRADE_TOOLTIP_XPATH)

            time.sleep(WAIT_AFTER_HOVER)

        except (Exception,):
            pass

        try:
            element.click()
            return True
        except (Exception,):
            return False

    def buy_simulation(self):
        super().buy_simulation()

        if self in self.cookie_clicker.upgrades:
            self.cookie_clicker.upgrades.remove(self)
        elif self in self.cookie_clicker.upgrades_unknown:
            self.cookie_clicker.upgrades_unknown.remove(self)
        else:
            raise


class BuildingUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, building, elementId):
        super().__init__(cookie_clicker, name, building.total_cps * amount, price, elementId)


class CompositeBuildingUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, buildings, elementId):
        gain = BigNumber(0)
        for b in buildings:
            gain += b.total_cps * BigNumber(amount)

        super().__init__(cookie_clicker, name, gain, price, elementId)


class CpsUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, elementId):
        super().__init__(cookie_clicker, name, cookie_clicker.cps * amount, price, elementId)


class OtherUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, price, elementId):
        super().__init__(cookie_clicker, name, 0, price, elementId)

    def get_profitability(self):
        return 0
