import json
import os
from datetime import datetime

from pynput.keyboard import Key

SAVES_FOLDER = "saves"
SAVE_DATE_FORMAT = "%d_%m_%Y-%H_%M_%S"

GAME = "game"
TYPE = "type"
NEW = "new"
LAST = "last"
SAVE = "save"
MAX_WAIT_TIME = "max_wait_time"
TARGET_CLICK_PER_SECOND = "target_clicks_per_second"
TOGGLE_CLICKING_KEY = "toggle_clicking_key"
MAX_BUILDINGS_MISSING_TO_CHASE_ACHIEVEMENT = "max_buildings_missing_to_chase_achievement"

CONFIG_PATH = "config.json"
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

            if TOGGLE_CLICKING_KEY in self.config:
                key_string = self.config[TOGGLE_CLICKING_KEY].lower()

                if hasattr(Key, key_string):
                    self.toggle_clicking_key = getattr(Key, key_string)
                else:
                    self.toggle_clicking_key = key_string

            if MAX_BUILDINGS_MISSING_TO_CHASE_ACHIEVEMENT in self.config:
                self.max_buildings_missing_to_chase_achievement = self.config[
                    MAX_BUILDINGS_MISSING_TO_CHASE_ACHIEVEMENT]
            else:
                self.max_buildings_missing_to_chase_achievement = 0
