import numpy as np

from cookie_clicker_bot.cookie_clicker import CookieClicker, CLICK_SEGMENT_DURATION
from cookie_clicker_bot.numbers import ZERO_BIG_NUMBER


def sort_by_profitability(buyables):
    return sorted(buyables, key=lambda b: b.get_profitability(), reverse=True)

# TODO if waiting for a long time for some buyable
# is it worth it to buy some currently available ones and boost cps
# so that the final time to the expensive one would actually be lesser
# than if you just waited?

def get_best_buy(cookie_clicker):
    cookie_clicker_copy = cookie_clicker.simulation_copy()
    buyables = cookie_clicker_copy.buildings + cookie_clicker_copy.upgrades

    if len(buyables) == 1:
        return cookie_clicker.get_buyable(buyables[0].name)

    buyables_sorted = sort_by_profitability(buyables)
    best_ratio_buyable = buyables_sorted[0]

    if best_ratio_buyable.can_buy():
        return cookie_clicker.get_buyable(best_ratio_buyable.name)

    gains = [best_ratio_buyable.gain]
    time_to_buy_best_ratio_buyable = best_ratio_buyable.time_to_buy()

    for wait_for_index in range(1, len(buyables)):
        cookie_clicker_copy = cookie_clicker.simulation_copy()
        start_cps = cookie_clicker_copy.cps

        buyables_wait_for = cookie_clicker_copy.buildings + cookie_clicker_copy.upgrades
        buyables_wait_for_sorted = sort_by_profitability(buyables_wait_for)
        wait_for_buyable = buyables_wait_for_sorted[wait_for_index]

        # TODO tu pokupuj sve kaj se da prije nego cekas na waitFor?

        elapsed_time = 0
        while elapsed_time < time_to_buy_best_ratio_buyable:
            if wait_for_buyable.can_buy():
                wait_for_buyable.buy_simulation()

                buyables_wait_for = cookie_clicker_copy.buildings + cookie_clicker_copy.upgrades
                buyables_wait_for_sorted = sort_by_profitability(buyables_wait_for)
                wait_for_buyable = buyables_wait_for_sorted[wait_for_index]

            else:
                time_to_buy_wait_for_buyable = wait_for_buyable.time_to_buy()
                elapsed_time += time_to_buy_wait_for_buyable

        gains.append(cookie_clicker_copy.cps - start_cps)

    best_gain_index = np.argmax(gains)

    return cookie_clicker.get_buyable(buyables_sorted[best_gain_index].name)


def main():
    cookie_clicker = CookieClicker()
    cookie_clicker.start()

    next_buy = None
    last_message = None

    while True:
        # if there is no next buy don't click but determine what the best buy is
        if next_buy is not None or len(cookie_clicker.buildings) == 0:
            click_segment_duration = CLICK_SEGMENT_DURATION
            if next_buy is not None:
                click_segment_duration = min(CLICK_SEGMENT_DURATION, next_buy.time_to_buy())
            cookie_clicker.click(click_segment_duration)

        if cookie_clicker.avg_clicks_per_second == 0:
            continue

        if cookie_clicker.click_golden_cookie():
            next_buy = None

        cookie_clicker.update()

        if next_buy is not None and cookie_clicker.bank < next_buy.price:
            continue

        best_upgrade_unknown = None
        if len(cookie_clicker.upgrades_unknown) > 0:
            bought_unknown = False
            for u in cookie_clicker.upgrades_unknown:
                if u.can_buy():
                    last_message = f"Buying other upgrade {u.name}"
                    print(last_message)

                    u.buy()
                    bought_unknown = True
                    break

            if bought_unknown:
                next_buy = None
                continue

            best_upgrade_unknown = cookie_clicker.upgrades_unknown[0]

        best_buy = get_best_buy(cookie_clicker)

        time_to_buy = best_buy.time_to_buy()
        if time_to_buy == 0:
            last_message = f"Buying {best_buy.name}"
            print(last_message)

            best_buy.buy()
            next_buy = None

        else:
            if best_upgrade_unknown is None or best_buy.price < best_upgrade_unknown.price:
                next_buy = best_buy
            else:
                next_buy = best_upgrade_unknown
                time_to_buy = best_upgrade_unknown.time_to_buy()

            current_message = f"Waiting for {next_buy.name}, ETA: {time_to_buy}"
            if current_message != last_message:
                last_message = current_message
                print(last_message)


if __name__ == "__main__":
    main()
