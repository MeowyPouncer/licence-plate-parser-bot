from enum import Enum, auto
import json


STATE_FILE = 'volume/user_states.json'


class BotState(Enum):
    ACCESS_DENIED = auto()
    INITIAL = auto()
    AWAITING_NUMBER_INPUT = auto()
    VIEWING_LIST = auto()
    ADDING_TO_LIST = auto()
    AWAITING_NAME_FOR_ADD = auto()
    AWAITING_ID_FOR_ADD = auto()
    AWAITING_DELETE_CONFIRMATION = auto()
    SELECT_USER_TO_DELETE = auto()


def save_states(user_states_list):
    with open(STATE_FILE, 'w') as file:
        json.dump({user_id: state.name for user_id, state in user_states_list.items()}, file)


def load_states():
    try:
        with open(STATE_FILE, 'r+') as file:
            try:
                raw_states = json.load(file)
                return raw_states
            except json.JSONDecodeError:
                file.seek(0)
                json.dump({}, file)
                file.truncate()
                return {}
    except FileNotFoundError:
        with open(STATE_FILE, 'w') as file:
            json.dump({}, file)
        return {}


user_states = load_states()


def get_state(user_id):
    return user_states.get(str(user_id))


def set_state(user_id, state):
    user_states[str(user_id)] = state
    save_states(user_states)
