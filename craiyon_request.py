#!/usr/bin/env python
#
# Copyright (C) 2022 noodleindabowl.
#
# This file is part of craiyon_request, an automation script for
# querying www.craiyon.com.
# License: BSD-3-Clause.

"""An automation script for querying www.craiyon.com"""
import io as _io

from selenium.webdriver.common.by import By as _By
from selenium.webdriver.support.wait import WebDriverWait as _WebDriverWait
from selenium.webdriver.support import expected_conditions as _EC
from selenium.common.exceptions import (
    WebDriverException as _WebDriverException,
    TimeoutException as _TimeoutException,
    StaleElementReferenceException as _StaleElementReferenceException,
    )
from PIL import (
    Image as _Image,
    UnidentifiedImageError as _UnidentifiedImageError,
    )

# default parameters
DEFAULTS = {
    "logger": None,
    "find_wait": 5,
    "find_wait_frequency": 0.5,
    "generation_wait": 120,
    "generation_wait_frequency": 1,
}

# website data
CRAIYON_URL = "https://www.craiyon.com/"
APP_CONTAINER_SELECTOR = "#app"
PROMPT_SELECTOR = "#prompt"
GENERATE_BUTTON_SELECTOR = "#app button"
RESULT_IMAGES_SELECTOR = "#app div > img"
AD_PLAYER_SELECTOR = "#aniplayer"


# custom errors

class CraiyonGeneralError(Exception):
    """Generic errors caller doesn't need to react to"""

class CraiyonAcessError(Exception):
    """Error requesting the page"""

class CraiyonFindError(Exception):
    """Error finding an element in the DOM"""

class CraiyonNoResultError(Exception):
    """Error timing out while waiting for image result to appear in the DOM"""

class CraiyonBadImageError(Exception):
    """Error trying to read screenshot of image result"""


def generate_image(driver, query, **options):
    """return PIL image object of the result of query"""
    # parse options
    for key, value in DEFAULTS.items():
        if key not in options:
            options[key] = value
    logger = options["logger"]

    # access website
    if logger:
        logger(f"Accessing {CRAIYON_URL}...")
    try:
        driver.get(CRAIYON_URL)
    except _WebDriverException:
        raise CraiyonAcessError(f"couldn't acess {CRAIYON_URL}") from None

    # find needed elements
    if logger:
        logger("Preparing to submit your query...")
    try:
        prompt = get_element_presence(driver, PROMPT_SELECTOR,
            options["find_wait"], options["find_wait_frequency"])
        generate_button = get_element_presence(driver, GENERATE_BUTTON_SELECTOR,
            options["find_wait"], options["find_wait_frequency"])
        ad_player = get_element_presence(driver, AD_PLAYER_SELECTOR,
            options["find_wait"], options["find_wait_frequency"])
    except _TimeoutException:
        raise CraiyonFindError(
            "timed out while finding needed element") from None

    # remove ad player from the DOM
    driver.execute_script("arguments[0].remove();", ad_player)
    # submit
    if logger:
        logger("Submitting your query...")
    try:
        # enter prompt
        prompt.clear()
        prompt.send_keys(query)
        # submit query
        generate_button.click()
    except _StaleElementReferenceException:
        raise CraiyonGeneralError(
            "needed element disappeared from the DOM!") from None

    # wait for images to generate
    if logger:
        logger("Waiting for results to generate...")
    try:
        # wait for generated image visiblity
        get_element_visibility(driver, RESULT_IMAGES_SELECTOR,
            options["generation_wait"], options["generation_wait_frequency"])
        # wait for generated image container visiblity
        app_container = get_element_visibility(driver, APP_CONTAINER_SELECTOR,
            options["find_wait"], options["find_wait_frequency"])
    except _TimeoutException:
        raise CraiyonNoResultError("timed out finding results") from None

    # perpare result
    if logger:
        logger("Preparing the results...")
    # screenshot the page
    screenshot_bytes = driver.get_full_page_screenshot_as_png()
    try:
        screenshot_object = _Image.open(_io.BytesIO(screenshot_bytes))
    except _UnidentifiedImageError:
        raise CraiyonBadImageError("screenshot couldn't be opened") from None
    # crop to app container
    # app_box -> (top, left, bottom, right)
    app_rect = app_container.rect
    app_box = (
        app_rect["x"],
        app_rect["y"],
        app_rect["x"] + app_rect["width"],
        app_rect["y"] + app_rect["height"],
    )
    app_screenshot = screenshot_object.crop(app_box)
    return app_screenshot

def get_element_presence(driver, selector, timeout, frequency):
    """wait until finding specified element in the DOM"""
    wait_args = { "driver": driver,
                  "timeout": timeout,
                  "poll_frequency": frequency }
    condition = _EC.presence_of_element_located((
        _By.CSS_SELECTOR, selector))
    return _WebDriverWait(**wait_args).until(condition)

def get_element_visibility(driver, selector, timeout, frequency):
    """wait until specified element becomes visible"""
    wait_args = { "driver": driver,
                  "timeout": timeout,
                  "poll_frequency": frequency }
    condition = _EC.visibility_of_element_located((
        _By.CSS_SELECTOR, selector))
    return _WebDriverWait(**wait_args).until(condition)
