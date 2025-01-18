from BigNumber.BigNumber import BigNumber

from cookie_clicker_bot.numbers import ZERO_BIG_NUMBER
from cookie_clicker_bot.scripts import Scripts
import time

BUILDING_TOOLTIP_XPATH = "//div[@id='tooltipBuilding']"
UPGRADE_TOOLTIP_XPATH = "//div[@id='tooltipCrate']"
WAIT_AFTER_HOVER = 0.1

BUILDING_PRICE_MULTIPLIER = 1.15
CURSOR_BASE_CPS = 0.1


class Buyable:
    hover_before_buy = False

    def __init__(self, cookie_clicker, name, gain, price, elementId):
        self.cookie_clicker = cookie_clicker
        self.name = name
        self.gain = gain
        self.price = price
        self.elementId = elementId

    def buy(self):
        XPATH = f"//div[@id='{self.elementId}']"
        element = self.cookie_clicker.manager.get_element(XPATH, True)

        try:
            element_class = element.get_attribute("class")
        except (Exception,):
            return False

        if "enabled" not in element_class:
            return False

        self.cookie_clicker.manager.execute_script(Scripts.SCROLL_INTO_VIEW, element)

        # if an upgrade is in the second row or below
        # wait a bit for the upgrades panel to expand
        # TODO bug, hovers on buildings?
        if self.hover_before_buy:
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
        self.cookie_clicker.bank -= self.price
        self.cookie_clicker.cps += self.gain

    def can_buy(self):
        return self.cookie_clicker.bank >= self.price

    def get_profitability(self):
        return self.gain / self.price

    def time_to_buy(self):
        # TODO does this need to be calculated in update and instead of a getter just read from a member variable?
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

        # gain = how much cps one building generates
        self.count += 1
        self.total_cps += self.gain
        self.gain = self.total_cps / self.count

        self.price *= BUILDING_PRICE_MULTIPLIER

    def sell(self):
        pass


class Upgrade(Buyable):
    hover_before_buy = True

    def __init__(self, cookie_clicker, name, gain, price, elementId):
        super().__init__(cookie_clicker, name, gain, price, elementId)

    def buy_simulation(self):
        super().buy_simulation()

        self.cookie_clicker.upgrades.remove(self)


class BuildingUpgradeMultiplier(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, building, elementId):
        self.building = building
        self.amount = amount

        super().__init__(cookie_clicker, name, building.total_cps * amount, price, elementId)

    def copy(self, cookie_clicker):
        building = cookie_clicker.get_building(self.building.name)
        return BuildingUpgradeMultiplier(cookie_clicker, self.name, self.amount, self.price, building, None)

    def buy_simulation(self):
        super().buy_simulation()

        self.building.total_cps *= (self.amount + 1)
        if self.building.count != 0:
            self.building.gain = self.building.total_cps / self.building.count



class BuildingUpgradeAmount(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, building, elementId):
        self.building = building
        self.amount = amount

        super().__init__(cookie_clicker, name, amount, price, elementId)

    def copy(self, cookie_clicker):
        building = cookie_clicker.get_building(self.building.name)
        return BuildingUpgradeMultiplier(cookie_clicker, self.name, self.amount, self.price, building, None)

    def buy_simulation(self):
        super().buy_simulation()

        self.building.total_cps += self.amount
        if self.building.count != 0:
            self.building.gain = self.building.total_cps / self.building.count


class CompositeBuildingUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, buildings, elementId):
        self.buildings = buildings
        self.amount = amount

        gain = ZERO_BIG_NUMBER
        for b in buildings:
            gain += b.total_cps * BigNumber(amount)

        super().__init__(cookie_clicker, name, gain, price, elementId)

    def copy(self, cookie_clicker):
        buildings = []
        for b in self.buildings:
            buildings.append(cookie_clicker.get_building(b.name))

        return CompositeBuildingUpgrade(cookie_clicker, self.name, self.amount, self.price, buildings, None)

    def buy_simulation(self):
        super().buy_simulation()

        for b in self.buildings:
            if b.count == 0:
                continue

            b.total_cps *= (self.amount + 1)
            if b.count != 0:
                b.gain = b.total_cps / b.count


class CpsUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, amount, price, elementId):
        super().__init__(cookie_clicker, name, cookie_clicker.cps * amount, price, elementId)

        self.amount = amount

    def copy(self, cookie_clicker):
        return CpsUpgrade(cookie_clicker, self.name, self.amount, self.price, None)

    def buy_simulation(self):
        super().buy_simulation()

        # TODO                                  does cps upgrade affect clicking?
        for b in self.cookie_clicker.buildings + [self.cookie_clicker.clicking]:
            if b.count == 0:
                continue

            b.total_cps *= self.amount
            b.gain = b.total_cps / b.count


class OtherUpgrade(Upgrade):
    def __init__(self, cookie_clicker, name, price, elementId):
        super().__init__(cookie_clicker, name, 0, price, elementId)

    def get_profitability(self):
        return 0
