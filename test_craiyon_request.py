#!/usr/bin/env python
#
# Copyright (C) 2022 noodleindabowl.
#
# This file is part of craiyon_request, an automation script for
# querying www.craiyon.com.
# License: BSD-3-Clause.

import asyncio
import io

from arsenic import services, browsers, start_session, stop_session
import craiyon_request

CRAIYON_URL = "https://www.craiyon.com/"
MYQUERY = "balls"
loop = asyncio.new_event_loop()
top_await = loop.run_until_complete

# webdriver options
GECKDRIVER = "./geckodriver"
LOG_FILE = "geckodriver.log"
LOG_MODE = "w"
WEBDRIVER_OPTIONS = {
    "moz:firefoxOptions": {
        "args": ["-headless"],
    }
}

# setup driver
with io.open(LOG_FILE, LOG_MODE, encoding="utf-8") as log_stream:
    service = services.Geckodriver(binary=GECKDRIVER, log_file=log_stream)
    browser = browsers.Firefox(**WEBDRIVER_OPTIONS)
    # start session
    mysession = top_await(start_session(service, browser))
    top_await(mysession.get(CRAIYON_URL));
    # make query
    try:
        pic = top_await(craiyon_request.generate_image(mysession, MYQUERY))
    finally:
        print("CLOSING SESSION")
        top_await(stop_session(mysession))

pic.show()
