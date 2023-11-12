#!/usr/bin/env python

import json
import paho.mqtt.client as paho  # pip install paho-mqtt
import time
import logging
import sys
from pyze.api import Gigya, Kamereon, Vehicle

from config import *
from secrets import *


FREQUENCY_ACTIVE = 600
FREQUENCY_INACTIVE = 3600
EXCEPTION_DELAY = 300

_ACTIVE_STATES = [0.3, 0.4, 1.0] # see https://github.com/jamesremuscat/pyze/blob/c359492287ce1a5462b8b3e7ddca11919bbf04a4/src/pyze/api/kamereon.py#L370


def getSocRange(gigya):

    k = Kamereon(api_key=KAMEREON_API_KEY, gigya=gigya, country='DE')
    v = Vehicle(ZOE_VIN, k)

    b = v.battery_status()
    soc = b['batteryLevel']
    remaining_range = b['batteryAutonomy']
    charging_status = b['chargingStatus']
    plug_status = b['plugStatus']

    logging.info("Zoe API: soc: {}%, range: {}km".format(soc, remaining_range))

    return soc, remaining_range, charging_status, plug_status


def update(gigya):
    soc, remaining_range, charging_status, plug_status = getSocRange(gigya)

    zoe = {'soc': soc, 'range': remaining_range}

    mqttc.publish(topic=ZOE_MQTT_PREFIX, payload=json.dumps(zoe), qos=0, retain=True)

    return charging_status


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
            charging_status = update(g)
            if (charging_status in _ACTIVE_STATES):
                time.sleep(FREQUENCY_ACTIVE)
            else:
                time.sleep(FREQUENCY_INACTIVE)
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

