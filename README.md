A bot which plays the browser version of Cookie Clicker: https://orteil.dashnet.org/cookieclicker/ 

Only English is supported.

# Requirements
* Python 3.10
* Google Chrome

# Install requirements and run
```
pip install -r requrements.txt
python main.py
```

# Toggle clicking
Since the bot's continuous clicking on the cookie can make interacting with the page manually impossible, 
it can be toggled by pressing the key specified in config.

# Saves
Saves are stored in the ```saves``` folder. By default, each save is denoted by its start time.
Loading saved games or starting a new game can be controlled through the config file.

# Config
Path: `/cookie_clicker_bot/config.json`

## `game`
Section which determines whether the game will be loaded or started anew.
### `type`
Possible values:
* `"new"`: loads last saved game. Creates a new save if none exist.
* `"last"`: starts a new game every time.
* `"save"`: loads a save with the specified name.

Default value is `"last"`.


### `save`
If `type` is `save`, determines the saved game from the `saves` folder which will be loaded.
Example: `"11_01_2025-19_23_47"`



## `max_wait_time` 
Maximum wait time in seconds for a buyable (building or upgrade). 
If the wait time for a buyable is greater than this value, the bot will not wait until it can afford it, 
but it will consider other buyables. If there are no buyables with wait time less than this value, 
the bot will just click the cookie until one is avaiable. If the value is `null`, 
the bot will always wait for a buyable which it considers most profitable. 
Note that this will sometimes result in very long waiting periods.

Default value is `null`.

## `target_clicks_per_second` 
Desired number of cookie clicks per second. The actual click rate will vary as the bot will not click 
while buying buildings and upgrades. Also note that the click rate will be limited by the fps of the browser, so setting this value to more than that will not increase the click rate. 
If the value is `null`, the bot will click as fast as possible.

Default value is `null`.

## `toggle_clicking_key` 
Key which toggles bot's clicking on the cookie.

Default value is `F4`.

## `max_buildings_missing_to_chase_achievement`

The bot will try to reach achievements given for owning a certain amount of buildings.
("Have 50/100/150/... [building]s")

This value determines how close a number of buildings needs to be to the next achievement 
so that the bot would try to reach it. Note that it will only start buying if there is 
enough cookies in bank to buy all missing buildings without waiting.
 