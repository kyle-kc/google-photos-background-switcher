import argparse
import logging
import sys
from ctypes import windll
from hashlib import md5
from os import listdir, unlink, makedirs
from os.path import exists, join, isfile, islink, isdir, abspath
from random import randint, choice
from shutil import rmtree
from time import sleep, time
from winreg import OpenKey, HKEY_CURRENT_USER, KEY_SET_VALUE, SetValueEx, REG_SZ

from selenium import webdriver
from selenium.webdriver import FirefoxProfile, FirefoxOptions, ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

LOG_FILE = "log"
DOWNLOAD_DIRECTORY = "downloaded-image"
WALLPAPER_REGISTRY_KEY = r"Control Panel\Desktop"
TEMPORARY_FILE_EXTENSIONS = ('.part', '.tmp', '.crdownload')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("log"),
        *([logging.StreamHandler(sys.stdout)] if sys.stdout and sys.stdout.isatty() else [])
    ]
)


def get_dom_hash(driver):
    return md5(driver.execute_script("return document.body.innerHTML;").encode('utf-8')).hexdigest()


def get_number_of_page_downs(driver):
    actions = ActionChains(driver)
    stable_count = 0
    previous_hash = get_dom_hash(driver)

    for i in range(100):
        actions.send_keys(Keys.PAGE_DOWN).perform()
        sleep(0.1)
        new_hash = get_dom_hash(driver)

        if new_hash == previous_hash:
            stable_count += 1
            if stable_count >= 3:
                return i
        else:
            stable_count = 0
            previous_hash = new_hash

    raise RuntimeError(f"Did not reach the end of the page after 100 attempts.")


def scroll_n_times(driver, n):
    actions = ActionChains(driver)
    for _ in range(n):
        actions.send_keys(Keys.PAGE_DOWN).perform()
        sleep(0.1)


def initialize_download_directory():
    logging.info("Initializing download directory...")
    if exists(DOWNLOAD_DIRECTORY):
        for filename in listdir(DOWNLOAD_DIRECTORY):
            file_path = join(DOWNLOAD_DIRECTORY, filename)
            if isfile(file_path) or islink(file_path):
                unlink(file_path)
            elif isdir(file_path):
                rmtree(file_path)
    else:
        makedirs(DOWNLOAD_DIRECTORY)
    logging.info("Download directory initialized.")


def wait_for_download():
    logging.info("Downloading...")

    start_time = time()
    downloaded_file = None
    while time() - start_time < 60:
        filenames = listdir(DOWNLOAD_DIRECTORY)

        if downloaded_file:
            if not any(
                    filename.endswith(TEMPORARY_FILE_EXTENSIONS)
                    for filename in filenames
            ):
                logging.info(f"Downloaded image {downloaded_file}.")
                return downloaded_file

        else:
            for filename in filenames:
                if not filename.endswith(TEMPORARY_FILE_EXTENSIONS):
                    file_path = join(DOWNLOAD_DIRECTORY, filename)
                    if exists(file_path):
                        downloaded_file = file_path
        sleep(1)

    raise TimeoutError("Download did not complete within the timeout period.")


def set_as_wallpaper(image_path: str):
    logging.info(f"Setting {image_path} as wallpaper...")
    with OpenKey(HKEY_CURRENT_USER, WALLPAPER_REGISTRY_KEY, 0, KEY_SET_VALUE) as key:
        SetValueEx(key, "WallpaperStyle", 0, REG_SZ, "10")
        SetValueEx(key, "TileWallpaper", 0, REG_SZ, "0")
    windll.user32.SystemParametersInfoW(20, 0, abspath(image_path), 3)
    logging.info(f"Wallpaper set.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set random Google Photos album image as wallpaper.")
    parser.add_argument(
        "--firefox-profile",
        type=str,
        required=True,
        help="Path to the Firefox profile directory"
    )
    parser.add_argument(
        "--album-url",
        type=str,
        required=True,
        help="URL of the Google Photos album"
    )
    args = parser.parse_args()
    logging.info(
        f"Starting Google Photos Background Switcher with Firefox profile path {args.firefox_profile} and album URL {args.album_url}.")

    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.profile = FirefoxProfile(args.firefox_profile)

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)

    try:
        initialize_download_directory()

        driver.get(args.album_url)

        total_number_of_page_downs = get_number_of_page_downs(driver)
        logging.info(f"Estimated total PAGE_DOWNs to bottom of page: {total_number_of_page_downs}")

        number_of_page_downs = randint(0, total_number_of_page_downs)
        logging.info(f"Scrolling randomly {number_of_page_downs} times...")
        driver.get(args.album_url)
        scroll_n_times(driver, number_of_page_downs)
        sleep(2)

        images = driver.find_elements(By.CSS_SELECTOR, ".rtIMgb.fCPuz.nV0gYe")

        choice(images).find_element(By.CSS_SELECTOR, "div[role = 'checkbox']").click()

        actions = ActionChains(driver)
        actions.key_down(Keys.SHIFT).key_down("d").release().perform()

        image_path = wait_for_download()

        set_as_wallpaper(image_path)

    finally:
        driver.quit()
