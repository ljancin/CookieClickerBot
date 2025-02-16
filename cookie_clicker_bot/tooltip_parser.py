from html.parser import HTMLParser

from cookie_clicker_bot.numbers import BigNumberFromString, ZERO_BIG_NUMBER


class TootlipParser(HTMLParser):
    data = []
    lastClass = None

    count = 0
    price = 0
    totalCps = ZERO_BIG_NUMBER

    def Reset(self):
        self.data = []
        self.lastClass = None
        self.count = 0
        self.totalCps = ZERO_BIG_NUMBER

    def Get(self):
        return self.count, self.price, self.totalCps

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            self.data = []
            self.lastClass = None

        if len(attrs) == 0:
            return

        attr0 = attrs[0]
        if attr0[0] == "class":
            self.lastClass = attr0[1]

    def handle_endtag(self, tag):
        if (tag == "div" or tag == "span") and len(self.data) > 0:
            data = ''.join(self.data)

            if "price" in self.lastClass:
                priceString = self.data[0]
                self.price = BigNumberFromString(priceString)
                return

            elif "producing" in data:
                dataSplit = data.split(" ")

                self.count = int(dataSplit[0])

                producingIndex = dataSplit.index("producing")
                if "cookies" in dataSplit:
                    cookiesIndex = dataSplit.index("cookies")
                elif "cookie" in dataSplit:
                    cookiesIndex = dataSplit.index("cookie")
                else:
                    raise Exception

                totalCpsArray = dataSplit[producingIndex + 1:cookiesIndex]
                totalCpsString = " ".join(totalCpsArray)
                self.totalCps = BigNumberFromString(totalCpsString)

    def handle_data(self, data):
        if self.lastClass is not None and ("price" in self.lastClass or self.lastClass == "descriptionBlock"):
            self.data.append(data)
