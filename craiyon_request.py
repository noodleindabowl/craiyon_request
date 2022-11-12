#!/usr/bin/env python
#
# Copyright (C) 2022 noodleindabowl.
#
# This file is part of craiyon_request, an automation script for
# querying www.craiyon.com.
# License: BSD-3-Clause.

"""An automation script for querying www.craiyon.com"""
import io
import base64
import math

from arsenic.errors import (
    ArsenicTimeout,
    StaleElementReference,
)
from PIL import (
    Image,
    UnidentifiedImageError,
)


# necessary data
APP_CONTAINER_SELECTOR = "#app"
PROMPT_SELECTOR = "#prompt"
GENERATE_BUTTON_SELECTOR = "#app button"
RESULT_IMAGES_SELECTOR = "#app div > img"
AD_SELECTORS = ["#videoplayer", "#craiyon_adhesion"]
IMAGES_NUM = 9
IMAGES_COLUMNS = 3

# overrideable defaults
DEFAULTS = {
    "find_wait": 5,
    "generation_wait": 120,
}

# js to remove specified elements from the DOM
# arguments: [elments to remove...]
JS_REMOVE_ELEMENTS = """
for (const arg of arguments) {
    elem = document.querySelector(arg)
    if (elem) {
        elem.remove();
    }
}
"""

# custom errors

class CraiyonGeneralError(Exception):
    """Generic errors caller doesn't need to react to"""

class CraiyonFindError(Exception):
    """Error finding an element in the DOM"""

class CraiyonNoResultError(Exception):
    """Error timing out while waiting for image result to appear in the DOM"""

class CraiyonBadImageError(Exception):
    """Error trying to read screenshot of image result"""


async def generate_image(session, query, **options):
    """return PIL image object of the result of query"""
    # parse options
    for key, val in DEFAULTS.items():
        if key not in options:
            options[key] = val

    # find needed elements
    try:
        prompt = await session.wait_for_element(
            options["find_wait"], PROMPT_SELECTOR)
        generate_button = await session.wait_for_element(
            options["find_wait"], GENERATE_BUTTON_SELECTOR)
    except ArsenicTimeout:
        raise CraiyonFindError(
            "timed out while finding needed element!") from None

    # remove ads from the DOM if they exist
    await session.execute_script(JS_REMOVE_ELEMENTS, AD_SELECTORS)
    try:
        session.wait_for_element_gone(options["find_wait"], AD_SELECTORS)
    except ArsenicTimeout:
        raise CraiyonGeneralError(
            "couldn't remove AD's from the DOM!") from None

    # submit query
    try:
        await prompt.clear()
        await prompt.send_keys(query)
        await generate_button.click()
    except StaleElementReference:
        raise CraiyonGeneralError(
            "needed element disappeared from the DOM!") from None

    # wait for one of the images to generate then wait for app container
    try:
        await session.wait_for_element(
            options["generation_wait"], RESULT_IMAGES_SELECTOR)
        await session.wait_for_element(
            options["find_wait"], APP_CONTAINER_SELECTOR)
    except ArsenicTimeout:
        raise CraiyonNoResultError("timed out finding results!") from None

    # find all images
    try:
        image_elements = await session.wait(
            options["find_wait"],
            lambda: get_generated_images(session),
            CraiyonFindError)
    except ArsenicTimeout:
        raise CraiyonNoResultError("got uncomplete list of results!") from None

    # decode image sources and turn them into pillow image objects
    query_images = []
    for i in range(IMAGES_NUM):
        image_source = await image_elements[i].get_attribute("src")
        if not isinstance(image_source, str):
            raise CraiyonGeneralError(
                "couldn't find source of image!") from None
        image_bytes = base64.b64decode(image_source.split(",", 1)[1])
        try:
            query_images.append(Image.open(io.BytesIO(image_bytes)))
        except UnidentifiedImageError:
            raise CraiyonBadImageError(
                "image couldn't be opened!") from None

    # return a grid of the results
    return grid_pics(query_images, IMAGES_COLUMNS,
        query_images[0].width, query_images[0].height)


async def get_generated_images(session):
    """return list of generated images"""
    image_elements = await session.get_elements(RESULT_IMAGES_SELECTOR)
    if len(image_elements) != IMAGES_NUM:
        raise CraiyonFindError from None
    return image_elements


def grid_pics(images, columns, width, height):
    """return a grid of passed images"""
    length = len(images)
    result_size = width*columns, math.ceil(length/columns)*height
    result = Image.new("RGB", result_size, "white")
    # lay all images on the grid
    for i in range(length):
        x, y = i%columns*width, i//columns*height
        result.paste(images[i], (x, y))
    return result
