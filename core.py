from typing import Any
import log, json, pprint

class Container:
    def __init__(self, **kwargs):
        for (k, v) in kwargs.items():
            if type(v) is list:
                v = tuple(v)

            setattr(self, k, v)
    
    def __iter__(self):
        return iter(self.__dict__.values())
    
    def set(self, key: str, value: Any):
        setattr(self, key, value)
    
    def has(self, key: str) -> bool:
        return hasattr(self, key)

    def log(self):
        pprint.pprint(self.__dict__)
        log.empty()

class Scene(Container): pass
        
class Model(Container): pass

class StateClass:
    LOG_EXCEPTION = False
    LOG = False

    MIN_PAGES = None
    INPUT = None

    SCRAPED = 0
    SUCCEED = 0
    FAILED = 0

    data: list[dict] = []

    logged = False
    login: Container = None

    def has(self, key: str) -> bool:
        return hasattr(self, key)

state = StateClass()
logging = []

def load_config() -> StateClass:
    """Loads the data from `config.json` and returns an `StateClass` instance with the data"""

    with open("src/config.json", "r") as fl:
        config = json.load(fl)
    
    for key in config:
        match key:
            case "-l" | "log" as value:
                state.LOG = config[value]
                if state.LOG:
                    logging.append("SITES")

            case "-le" | "exception" as value:
                state.LOG_EXCEPTION = config[value]
                if state.LOG_EXCEPTION:
                    logging.append("EXCEPTIONS")
                
            case "-msp" | "min_scenes_pages" as value:
                state.min_scenes_pages = config[value]

            case "-mmp" | "min_models_pages" as value:
                state.min_models_pages = config[value]

            case "-so" | "scenes_output" as value:
                state.scenes_output = config[value]

            case "-mo" | "models_output" as value:
                state.models_output = config[value]
            
            case "-f" | "file" as value:
                with open(config[value], "r") as fl:
                    state.data = json.load(fl)

            case "-do" | "dump_output" as value:
                state.OUTPUT_FILE = config[value]
    
    log.log("CONFIG LOADED")

    if logging:
        log.log("LOGGING", f"[{(', '.join(logging))}]")

    log.empty()
    return state