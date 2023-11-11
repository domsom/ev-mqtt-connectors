#!/usr/bin/env python

import json
import paho.mqtt.client as paho  # pip install paho-mqtt
import time
import logging
import sys
from pyze.api import Gigya, Kamereon, Vehicle

from config import *
from secrets import *


FREQUENCY = 600  # sec
EXCEPTION_DELAY = 300


def getSocRange(gigya):

    k = Kamereon(api_key=KAMEREON_API_KEY, gigya=gigya, country='DE')
    v = Vehicle(ZOE_VIN, k)

    b = v.battery_status()
    soc = b['batteryLevel']
    remaining_range = b['batteryAutonomy']

    logging.info("Zoe API: soc: {}%, range: {}km".format(soc, remaining_range))

    return soc, remaining_range


def update(gigya):
    soc, remaining_range = getSocRange(gigya)

    zoe = {'soc': soc, 'range': remaining_range}

    mqttc.publish(topic=ZOE_MQTT_PREFIX, payload=json.dumps(zoe), qos=0, retain=True)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    mqttc = paho.Client('zoe-connector', clean_session=True)
    # mqttc.enable_logger()

    try:
        g = Gigya(api_key=GIGYA_API_KEY)
        g.login(ZOE_ZE_USERNAME, ZOE_ZE_PASSWORD)  # You should only need to do this once
        g.account_info()  # Retrieves and caches person ID
    except Exception:
        logging.exception("Exception during Gigya login, sleeping 30s")
        time.sleep(30)
        raise

    mqttc.connect(BROKER_HOST, BROKER_PORT, 60)
    logging.info("Connected to {}:{}".format(BROKER_HOST, BROKER_PORT))

    exception_counter = 0

    mqttc.loop_start()
    while True:
        try:
            update(g)
            time.sleep(FREQUENCY)
        except KeyboardInterrupt:
            logging.warning("Keyboard interruption")
            break
        except Exception:
            exception_counter = exception_counter + 1
            if exception_counter > 24:
                logging.exception("Exception occured in main loop too many times ({exception_counter}), giving up....")
                raise
            else:
                logging.exception(f"Exception occured in main loop, retrying after {EXCEPTION_DELAY} sec")

            time.sleep(EXCEPTION_DELAY)

    mqttc.disconnect()
    mqttc.loop_stop()  # waits, until DISCONNECT message is sent out
    logging.info("Disconnected from to {}:{}".format(BROKER_HOST, BROKER_PORT))

