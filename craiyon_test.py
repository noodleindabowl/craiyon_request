#!/usr/bin/env python
#
# Copyright (C) 2022 noodleindabowl.
#
# This file is part of craiyon_request, an automation script for
# querying www.craiyon.com.
# License: BSD-3-Clause.

"""testing script for the craiyon_request module"""
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

import craiyon_request


if __name__ == "__main__":
    serv = Service(executable_path=Path.joinpath(Path.cwd(), "geckodriver"))
    opts = Options()
    opts.headless = True
    driver = webdriver.Firefox(service=serv, options=opts)
    driver.set_window_rect(0, 0, 1280, 720)

    craiyon_request.generate_image(driver, "balls", logger=print).show()
