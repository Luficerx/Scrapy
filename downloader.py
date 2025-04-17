import re, os, json
import requests
import log

DATE_PATTERN = r"([a-zA-Z]*)\s([0-9]*),\s(.*)"

OUTPUT_PREFIX = "H:/Porn/"
PREFIXES =[
    "Jan", "Feb", "Mar",
    "Apr", "May", "Jun",
    "Jul", "Aug", "Sep",
    "Oct", "Nov", "Dec"
    ]

def split_date(date: str, fmt="YMD") -> tuple[str, str, str]:
    """
    date: `str` - date in the format `'Jan 0, 2069'`

    fmt: `str` - one of `'YMD'` `'DMY'` `'MDY'`
    """

    content = re.match(DATE_PATTERN, date)
    month_name, day, year = content.groups()
    month = None

    for (i, pref) in enumerate(PREFIXES, start=1):
        if month_name == pref:
            month = str(i)
            break
    
    if month is None:
        raise Exception(f"Could not find {month_name!r} in {content.groups()!r}")

    if len(month) == 1:
        month = f"0{month}"

    if len(day) == 1:
        day = f"0{day}"

    match fmt:
        case "YMD":
            return (year, month, day)
        
        case "DMY":
            return (day, month, year)
        
        case "MDY":
            return (month, day, year)
        
        case _ as value:
            log.error(f"Invalid case {value}, returning 'YMD'")
            return (year, month, day)

def format_date(date: str):
    result = "-".join(split_date(date))
    return result

def make_file_name(*args) -> str:
    file_name = " - ".join(args)
    return file_name

def download_scenes(data: list[dict]):
    # log.log("LOADING: 'src/scenes.json'")

    for item in data:
        date = format_date(item["date"])
        studio = item["studio"]
        title = item["title"]
        links = item["links"]

        for (quality, link) in links.items():
            scene_title = make_file_name(studio, date, title, f"[{quality}]")
            file_name = f"{scene_title}.mp4"
            
            base_path = os.path.join(OUTPUT_PREFIX, studio)
            os.makedirs(base_path, exist_ok=True)
            path = os.path.join(base_path, file_name)

            if os.path.exists(path):
                log.log("EXISTS:", title, quality)
                continue
            
            with open(path, "wb") as fl:

                try:
                    response = requests.get(link, stream=True)
                    response.raise_for_status()

                    size = int(response.headers.get('content-length', 0))

                    if size == 0:
                        log.error("File with size 0")
                        fl.write(response.content)

                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                fl.write(chunk)
                                downloaded += len(chunk)
                                print(f"\r{downloaded/size*100:.1f} % | {title} {quality}", end='')

                        log.empty()

                except:
                    pass
                
            break

    
if __name__ == "__main__":
    with open("src/scenes.json", "r") as fl:
        scraped_scenes = json.load(fl)
    
    download_scenes(scraped_scenes)