import datetime, sys

FINE  = "[✓]"
NOTE  = "[•]"
INFO  = "[-]"
ERROR = "[✗]"

def log(*args, pre="[•]", **kwargs):
    print(pre, *args, **kwargs)

def no_nl_log(*args):
    """Print's text without newline and suffix"""
    print(*args, end="")

def no_pref(*args):
    """Print's text without suffix"""
    print(*args)

def success(*args):
    print(FINE, *args)

def error(*args):
    print(ERROR, *args)

def log_time(pre=NOTE):
    """Prints the current timestamp"""
    log(f"{datetime.datetime.now().time().strftime("%H:%M:%S")}", pre=pre)

def log_result(iterable: list, *args, **kwargs):
    if iterable:
        line = "\n".join(iterable)
        print(line, *args, **kwargs)

def get_time():
    """Returns the current timestamp"""
    now = datetime.datetime.now()
    return f"{now.time().strftime("%H:%M:%S")}"

def empty():
    """Prints an emtpy string"""
    print("")

def progress(current, total, length=10):
    percent = current / total
    filled = int(length * percent)
    bar = '=' * filled + ' ' * (length - filled)
    print(f"\r[{bar}]", end='')

def log_exec(fn):
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = fn(*args, **kwargs)
        end = datetime.datetime.now()

        duration = end - start
        
        s = duration.total_seconds()
        hours = int(s // 3600)
        minutes = int((s % 3600) // 60)
        seconds = int(s % 60)
        milliseconds = int(duration.microseconds / 1000)
        log(f"PROGRAM TOOK {hours:d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d} TO FINISH.")

        return result
    
    return wrapper
