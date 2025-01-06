from BigNumber.BigNumber import BigNumber
from enum import Enum, auto

ZERO_BIG_NUMBER = BigNumber(0)
INFINITY = float("inf")

int_multipliers = {
    "twice": 2,
    "three times": 3,
    "four times": 4,
    "five times": 5,
}


# key == 1000 ^ value
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


def BigNumberFromString(value):
    if isinstance(value, int) or isinstance(value, float):
        return BigNumber(value)

    value = value.replace(",", '')
    valueSplit = value.split(" ")

    if len(valueSplit) == 1:
        return BigNumber(value)

    number = valueSplit[0]
    multiplier = Multiplier[valueSplit[1]]

    numberBigNumber = BigNumber(number)
    multiplierBigNumber = BigNumber(1000) ** multiplier.value
    return numberBigNumber * multiplierBigNumber
