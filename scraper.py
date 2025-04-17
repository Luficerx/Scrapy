from selenium.webdriver.support import expected_conditions as ExCond
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from itertools import zip_longest
from selenium import webdriver
from time import sleep
import core, log, json, os

scraped = core.Container()

scraped.models = set()
scraped.scenes = set()

@log.log_exec
def main():
    driver = None

    try:
        match os.name:
            case "nt":
                options = webdriver.FirefoxOptions()
                options.add_argument("--headless")
                driver = webdriver.Firefox(options=options)

            case "posix":
                gecko = "/snap/bin/geckodriver"
                firefox = "/snap/bin/firefox"

                service = Service(executable_path=gecko)
                options = Options()
                options.add_argument("--headless")
                options.binary_location = firefox

                driver = webdriver.Firefox(service=service, options=options)

        waiter = WebDriverWait(driver, 10)
        driver.set_window_size(1920, 1080)
        start(driver, waiter)

    except Exception as e:
        log.error("[FATAL]")
        raise e

    finally:
        log.log(log.get_time(), pre=log.INFO)
        if driver is not None:
            driver.quit()
        
def start(driver, waiter) -> list:
    scenes_output = []
    models_output = []
    
    data: list[dict] = state.data
    
    for item in data:
        login = item.get("login", False)
        link = item["link"]
        name = item["name"]

        scenes = core.Container(**item.get("scenes", {}))
        models = core.Container(**item.get("models", {}))

        scenes.set("studio", name)

        driver.get(link)
        sleep(1.0)

        if set_login(login):
            if state.login.type == "text":
                button = button_by_text(waiter, state.login)
                button.click()
                sign_up(waiter, state.login)
                state.logged = True

            if not state.logged:
                log.error(f"COULD NOT LOG AS {state.login.user[:5]}.")
                log.error(f"RETURNING")
                return
            
        # Scenes
        log.log(name)
        page_link = link + scenes.header
        driver.get(page_link)
        element = get_element(waiter, ExCond.presence_of_element_located, scenes.nav_selector)
        pages = int(element.get_attribute(scenes.nav_attribute))
        items = scrap_scenes(driver, waiter, scenes, page_link+scenes.suffix, pages)
        scenes_output.extend(items)

        # Models
        page_link = link + models.header

        driver.get(page_link)
        element = get_element(waiter, ExCond.presence_of_element_located, models.nav_selector)
        pages = int(element.get_attribute(models.nav_attribute))
        items = scrap_models(driver, waiter, models, page_link+models.suffix, pages)
        models_output.extend(items)

        log.empty()

    if scenes_output:
        dump_data(scenes_output, state.scenes_output)
        
    if models_output:
        dump_data(models_output, state.models_output)

def dump_data(data: list[core.Container], target: str):
    serialized_data = [x.__dict__ for x in data]
    with open(target, "w") as file:
        json.dump(serialized_data, file, indent=4)

def scrap_scenes(driver, waiter, scenes: core.Container, head: str, pages: int) -> list[core.Scene]:
    pages = set_max_pages(pages, scenes)
    log.log(f"SCRAPING SCENES | PAGES: {pages}")
    scraped_scenes = []

    for i in range(pages):
        base_link = head.format(i+1) 
        driver.get(base_link)
        sleep(1.0)

        elements = get_element(waiter, ExCond.presence_of_all_elements_located, scenes.grid_selector)
        links = [element.get_attribute("href") for element in elements]

        for k, link in enumerate(links):
            try:
                driver.get(link)
                sleep(1.0)

                scene = core.Scene()
                scene.set("link", link)
                scene.set("studio", scenes.studio)

                if scenes.has("title_selector"):
                    title_element = get_element(waiter, ExCond.presence_of_element_located, scenes.title_selector)
                    scene.set("title", title_element.text)

                if scenes.has("thumbnail_selector"):
                    thumbnail_element = get_element(waiter, ExCond.presence_of_element_located, scenes.thumbnail_selector, return_value="No Thumbnail Found.")
                    scene.set("thumbnail", thumbnail_element.get_attribute("src"))

                if scenes.has("description_selector"):
                    desc_element = get_element(waiter, ExCond.presence_of_element_located, scenes.description_selector, return_value="No Description Found.")
                    scene.set("description", desc_element.text)

                if scenes.has("tags_selector"):
                    tag_elements = get_element(waiter, ExCond.presence_of_all_elements_located, scenes.tags_selector, return_value=[])
                    tags = [tag.text for tag in tag_elements]
                    scene.set("tags", tags)

                if scenes.has("stats_selector"):
                    stats_elements = get_element(waiter, ExCond.presence_of_all_elements_located, scenes.stats_selector, return_value=[])
                    stats = [stat.text for stat in stats_elements]
                    
                    if stats:
                        views = stats[0]
                        scene.set("views", views)

                        date = stats[-1]
                        if date != views:
                            scene.set("date", date)
                    
                if scenes.has("models_selector"):
                    model_elements = get_element(waiter, ExCond.presence_of_all_elements_located, scenes.models_selector, return_value=[])
                    models = [model.text for model in model_elements]
                    scene.set("models", models)

                if scenes.has("download_button_selector"):
                    scene_has_download(waiter, scenes, scene, link)
                
                scraped_scenes.append(scene)

                if state.LOG:
                    log.success(scene.link)

            except Exception as e:
                log.error(link)

                if state.LOG_EXCEPTION:
                    log.log(e)

    log.log("SCENES:", len(scraped_scenes))
    return scraped_scenes

def scrap_models(driver, waiter, models: core.Container, head: str, pages: int) -> list[core.Model]:
    pages = set_max_pages(pages, models)

    log.log(f"SCRAPING MODELS | PAGES: {pages}")
    scraped_models = []

    for i in range(pages):
        base_link = head.format(i+1) 
        driver.get(base_link)
        sleep(1.0)

        elements = get_element(waiter, ExCond.presence_of_all_elements_located, models.grid_selector)
        links = [element.get_attribute("href") for element in elements]

        for link in links:
            try:
                driver.get(link)
                sleep(1.0)

                model = core.Model()

                if models.has("name_selector"):
                    name_element = get_element(waiter, ExCond.presence_of_element_located, models.name_selector)
                    name = name_element.text
                    model.set("model", name)

                if models.has("photo_selector"):
                    photo_element = get_element(waiter, ExCond.presence_of_element_located, models.photo_selector)
                    photo = photo_element.get_attribute("src")
                    model.set("photo", photo)

                if models.has("network_selector"):
                    network_elements = get_element(waiter, ExCond.presence_of_all_elements_located, models.network_selector)
                    networks = [network.text for network in network_elements]
                    model.set("network", networks)

                if models.has("stats_selector"):
                    stat_elements = get_element(waiter, ExCond.presence_of_all_elements_located, models.stats_selector)
                    stats = make_pairs([stat.text for stat in stat_elements])
                    model.set("stats", dict(swap_pairs(stats)))

                if models.has("tags_selector"):
                    tag_elements = get_element(waiter, ExCond.presence_of_all_elements_located, models.tags_selector)
                    tags = [tag.text for tag in tag_elements]
                    model.set("tags", tags)

                scraped_models.append(model)

            except Exception as e:
                log.error(link)

                if state.LOG_EXCEPTION:
                    log.no_nl_log(e)

    log.log("MODELS:", len(scraped_models))
    return scraped_models

def set_login(data: dict | bool):
    if not data:
        return False
    
    state.login = core.Container(**data)
    return True

def sign_up(waiter: WebDriverWait, blob: core.Container):
    waiter.until(ExCond.element_to_be_clickable(blob.user_selector)).send_keys(blob.user)
    waiter.until(ExCond.element_to_be_clickable(blob.password_selector)).send_keys(blob.password)
    waiter.until(ExCond.element_to_be_clickable(blob.signin_selector)).click()
    sleep(1.0)

def get_element(waiter, expect, selector: tuple[str, str], return_value=None) -> object | list[object]:
    if return_value is not None:
        try:
            value = waiter.until(expect(selector))
            return value
        
        except:
            return return_value
    
    return waiter.until(expect(selector))

def button_by_text(waiter: WebDriverWait, blob: core.Container):
    items = waiter.until(ExCond.presence_of_all_elements_located(blob.selector))
    
    for item in items:
        if item.text.strip() == blob.target:
            return item

def scene_has_download(waiter, scenes: core.Scene, scene: core.Container, link: str):
    """NOTE: Wrapper to handle if the download button could not be found"""
    try:
        button = get_element(waiter, ExCond.presence_of_element_located, scenes.download_button_selector)
        button.click()
        sleep(2.0)

        buttons = get_element(waiter, ExCond.presence_of_all_elements_located, scenes.targets_selector)
        download_buttons = dict([(x.text, x.get_attribute("href")) for x in buttons])
        scene.set("links", download_buttons)

    except Exception as e:
        if state.LOG_EXCEPTION:
            log.error("'Download' not found: ", link)
        
        return
    
def make_pairs(iterable) -> list[tuple]:
    return list(zip_longest(iterable[::2], iterable[1::2], fillvalue="NaN"))

def set_max_pages(pages, blob: core.Container) -> int:
    if blob.has("min_pages"):
        result = min(blob.min_pages, pages)

    elif state.has("min_scenes_pages"):
        result = min(state.min_scenes_pages, pages)

    else:
        log.error("No minimum pages set, returning 1")
        return 1

    return result

def swap_pairs(iterable) -> list[tuple]:
    new = []

    for (k, v) in iterable:
        match v:
            case "Scenes" | "Scenes Duration" | "Photos" | "Scene Views":
                new.append((v, k))

            case _: pass

    return new

if __name__ == "__main__":
    log.log(log.get_time(), pre=log.INFO)
    state = core.load_config()

    main()