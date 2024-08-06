import os
import logging


def init_test_log(name, level=logging.DEBUG, writemode="w"):
    log_dir = os.path.join("tests/logs", os.path.dirname(name))
    os.makedirs(log_dir, exist_ok=True)
    log = logging.getLogger(name)
    handler = logging.FileHandler(os.path.join(log_dir, f"{os.path.basename(name)}.log"), mode=writemode)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s", datefmt="%d/%m/%Y %H:%M:%S"))
    handler.setLevel(level)
    log.addHandler(handler)
    log.setLevel(level)
    log.info(f"Starting {name}")
    return log
