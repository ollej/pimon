#!/usr/bin/env python

import sys
import time
import requests
import signal

import scrollphat

# TODO: Input sleep time
# TODO: Input brightness

# https://mmonit.com/documentation/http-api/Methods/Status
# hash['led'] - 1=orange, 2=green, 3=gray
# filter on hash['hostname']: .*(apps)
# hash['heartbeat'] - 1=host ok 0=host dead

class PiMon:
    PIXELS = 55
    COLS = 11
    ROWS = 5

    def __init__(self, url, username, password):
        self.login(url, username, password)

    def login(self, url, username, password):
        self.url = url
        self.session = requests.session()
        self.get('/index.csp')
        credentials = {
            "z_username": username,
            "z_password": password,
            "z_csrf_protection": "off"
        }
        self.post('/z_security_check', data=credentials)

    def get(self, path):
        return self.session.get(self.url + path)

    def post(self, path, data=None):
        return self.session.post(self.url + path, data)

    def update(self):
        result = self.get("/status/hosts/list")
        status_leds = self.extract_statuses(result.json())
        return self.convert_to_matrix(status_leds)

    def extract_statuses(self, statuses):
        status_leds = []
        for status in statuses['records']:
            if status['hostname'].find("(apps)") > -1:
                status_leds.append(status['heartbeat'])
        return status_leds

    def convert_to_matrix(self, arr):
        matrix_array = self.limit_array(arr)
        counter = 0
        matrix = []
        for i in range(self.ROWS):
            row = []
            for j in range(self.COLS):
                row.append(matrix_array[counter])
                counter += 1
            matrix.append(row)
        return matrix

    def limit_array(self, arr):
        if len(arr) > self.PIXELS:
            return arr[:self.PIXELS]
        elif len(arr) < self.PIXELS:
            return arr + [0] * (self.PIXELS - len(arr))
        else:
            return arr

    def dump(self):
        print(self.update())

class PiMatrix:
    SLEEP_TIME = 20
    BRIGHTNESS = 2

    def __init__(self, matrix_updater):
        self.setup_signal_handler()
        self.matrix_updater = matrix_updater
        scrollphat.set_brightness(self.BRIGHTNESS)

    def update_matrix(self):
        matrix = self.matrix_updater.update()
        scrollphat.set_pixels(lambda x, y: matrix[y][x], True)

    def run(self):
        while True:
            self.update_matrix()
            time.sleep(self.SLEEP_TIME)

    def setup_signal_handler(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, signum, frame):
        scrollphat.clear()
        sys.exit(-1)


if len(sys.argv) != 4:
    print("\nusage: python pimon.py \"M/Monit Base URL\" \"M/Monit username\" \"M/Monit password\" \npress CTRL-C to exit\n")
    sys.exit(0)

pimon = PiMon(*sys.argv[1:])
PiMatrix(pimon).run()
#pimon.dump()

