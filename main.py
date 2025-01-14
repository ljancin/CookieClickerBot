import numpy as np

from cookie_clicker_bot.cookie_clicker import CookieClicker, CLICK_SEGMENT_DURATION


def sort_by_profitability(buyables):
    return sorted(buyables, key=lambda b: b.get_profitability(), reverse=True)


def sort_by_price(buyables):
    return sorted(buyables, key=lambda b: b.price, reverse=True)


# TODO ratio gain / price / time to buy istead of just gain / price?

def get_best_buy(cookie_clicker):
    buyables = cookie_clicker.get_evaluable_buyables()

    if len(buyables) == 0:
        return None
    if len(buyables) == 1:
        return cookie_clicker.get_buyable(buyables[0].name)

    buyables_sorted = sort_by_profitability(buyables)
    best_ratio_buyable = buyables_sorted[0]

    if best_ratio_buyable.can_buy():
        return cookie_clicker.get_buyable(best_ratio_buyable.name)

    gains = [best_ratio_buyable.gain]
    time_to_buy_best_ratio_buyable = best_ratio_buyable.time_to_buy()

    # n-th profitable buyable which will be waited for if it can't be bought
    for wait_for_index in range(len(buyables) - 1):
        cookie_clicker_copy = cookie_clicker.simulation_copy()
        start_cps = cookie_clicker_copy.cps

        # buyables without best_buy
        buyables_wait_for = cookie_clicker_copy.get_evaluable_buyables()[1:]
        buyables_wait_for_sorted = sort_by_profitability(buyables_wait_for)
        buyables_wait_for_sorted_best_buy = buyables_wait_for_sorted[0]

        if buyables_wait_for_sorted_best_buy.can_buy():
            wait_for_buyable = buyables_wait_for_sorted_best_buy
        else:
            wait_for_buyable = buyables_wait_for_sorted[wait_for_index]

        elapsed_time = 0
        while elapsed_time < time_to_buy_best_ratio_buyable:
            if wait_for_buyable.can_buy():
                wait_for_buyable.buy_simulation()

                # TODO check if there evaluable buyables are empty!
                buyables_wait_for = cookie_clicker_copy.get_evaluable_buyables()[1:]
                buyables_wait_for_sorted = sort_by_profitability(buyables_wait_for)
                buyables_wait_for_sorted_best_buy = buyables_wait_for_sorted[0]

                if buyables_wait_for_sorted_best_buy.can_buy():
                    wait_for_buyable = buyables_wait_for_sorted_best_buy
                else:
                    wait_for_buyable = buyables_wait_for_sorted[wait_for_index]

            else:
                time_to_buy_wait_for_buyable = wait_for_buyable.time_to_buy()

                elapsed_time += time_to_buy_wait_for_buyable
                cookie_clicker_copy.bank += cookie_clicker_copy.cps * time_to_buy_wait_for_buyable

        gains.append(cookie_clicker_copy.cps - start_cps)

    best_gain_index = np.argmax(gains)

    best_buy = cookie_clicker.get_buyable(buyables_sorted[best_gain_index].name)

    if best_buy.can_buy():
        return best_buy

    # original_best_buy = best_buy
    best_buy_time_to_buy_original = best_buy.time_to_buy()

    cheaper_buyables = []
    buyables_sorted_by_price = sort_by_price(buyables)
    for i in range(len(buyables_sorted_by_price)):
        if buyables_sorted_by_price[i] == best_buy:
            cheaper_buyables = buyables_sorted_by_price[i + 1:]
            break

    most_saved_time = 0
    for cheaper_buyable in cheaper_buyables:
        cookie_clicker_copy = cookie_clicker.simulation_copy()

        best_buy_simulation = cookie_clicker_copy.get_buyable(best_buy.name)
        cheaper_buyable_simulation = cookie_clicker_copy.get_buyable(cheaper_buyable.name)

        if not cheaper_buyable_simulation.can_buy():
            continue

        cheaper_buyable_simulation.buy_simulation()

        best_buy_time_to_buy_after_cheaper_buy = best_buy_simulation.time_to_buy()

        saved_time = best_buy_time_to_buy_original - best_buy_time_to_buy_after_cheaper_buy

        if saved_time > most_saved_time:
            most_saved_time = saved_time
            best_buy = cheaper_buyable

    # if most_saved_time > 0:
    #    print(f"saving {most_saved_time} by buying {best_buy.name} instead of waiting for {original_best_buy.name}")

    return best_buy


# TODO stop clicking for x seconds after used double or triple clicks
#  set double click threshold and x in config

# TODO what happens at the legacy screen?

# TODO save log to save folder
def main():
    cookie_clicker = CookieClicker()
    cookie_clicker.start()

    next_buy = None
    n_buffs_previous = 0

    while True:
        # TODO research upgrades
        evaluable_buyables = cookie_clicker.get_evaluable_buyables()

        # if there is no next buy, don't click on cookie but directly go determine what the best buy is
        if next_buy is not None or len(evaluable_buyables) == 0:
            click_segment_duration = CLICK_SEGMENT_DURATION
            if next_buy is not None:
                click_segment_duration = min(CLICK_SEGMENT_DURATION, next_buy.time_to_buy())
            cookie_clicker.click(click_segment_duration)

        # determined in click(), not update(), that's why it's checked before update
        if cookie_clicker.avg_clicks_per_second == 0:
            continue

        if cookie_clicker.click_golden_cookie():
            next_buy = None

        cookie_clicker.update_periodic()

        n_buffs = cookie_clicker.n_buffs
        if n_buffs_previous != n_buffs:
            next_buy = None
        n_buffs_previous = n_buffs

        if next_buy is not None and cookie_clicker.bank < next_buy.price:
            continue

        cookie_clicker.update_for_calculations()

        # TODO pursue building number achievements
        #   if you can afford it, if there are 3/5/? buildings to go
        #   for the next 100/150/... achievement
        #   buy the building

        best_upgrade_unknown = None
        if len(cookie_clicker.upgrades_unknown) > 0:
            bought_unknown = False
            for u in cookie_clicker.upgrades_unknown:
                if u.can_buy():
                    print(f"Buying other upgrade {u.name}")
                    u.buy()
                    bought_unknown = True
                    break

            if bought_unknown:
                next_buy = None
                continue

            best_upgrade_unknown = cookie_clicker.upgrades_unknown[0]

        if next_buy is None:
            best_buy = get_best_buy(cookie_clicker)
            if best_buy is None:
                continue
        else:
            best_buy = next_buy

        time_to_buy = best_buy.time_to_buy()
        if time_to_buy == 0:
            print(f"Buying {best_buy.name}")
            best_buy.buy()
            next_buy = None

        else:
            if best_upgrade_unknown is None or best_buy.price < best_upgrade_unknown.price:
                next_buy = best_buy
            else:
                next_buy = best_upgrade_unknown
                time_to_buy = best_upgrade_unknown.time_to_buy()

            if next_buy is not None and cookie_clicker.building_for_number_achievement is not None:
                cookie_clicker.building_for_number_achievement.buy()
                print(f"Buying {cookie_clicker.building_for_number_achievement.name} for achievement")
                # ?
                #next_buy = None
            else:
                print(f"Waiting for {next_buy.name}, ETA: {time_to_buy}")


if __name__ == "__main__":
    main()
