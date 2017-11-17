#!/usr/bin/env python

import argparse
import json
import logging
import nest
import nest.utils
import os
import sys
import time

import paho.mqtt.client as mqtt

LOG = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument('--client-id',
                   default=os.environ.get('NEST_CLIENT_ID'))
    p.add_argument('--client-secret',
                   default=os.environ.get('NEST_CLIENT_SECRET'))
    p.add_argument('--pin',
                   default=os.environ.get('NEST_AUTHORIZATION_PIN'))
    p.add_argument('--location',
                   default=os.environ.get('NEST_LOCATION'))
    p.add_argument('--interval', '-i',
                   default=os.environ.get('NEST_POLL_INTERVAL', 60),
                   type=int)
    p.add_argument('--topic',
                   default=os.environ.get('NEST_TOPIC_PREFIX', 'sensor'))
    p.add_argument('--mqtt-server', '-s',
                   default=os.environ.get('NEST_MQTT_SERVER'))
    p.add_argument('--token-cache', '-c',
                   default=os.environ.get('NEST_TOKEN_CACHE', '.napi_tokens'))
    p.add_argument('--token', '-t',
                   default=os.environ.get('NEST_ACCESS_TOKEN'))

    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level='INFO')

    LOG.info('authenticating to nest api')
    napi = nest.Nest(client_id=args.client_id,
                     client_secret=args.client_secret,
                     access_token_cache_file=args.token_cache,
                     access_token=args.token)

    if napi.authorization_required:
        if args.pin:
            LOG.info('requesting access token')
            napi.request_token(args.pin)
        else:
            LOG.error('api requires authorization')
            sys.exit(1)

    LOG.info('connecting to mqtt broker')
    mq = mqtt.Client()
    mq.loop_start()
    mq.connect(args.mqtt_server)

    while True:
        for therm in napi.thermostats:
            if therm.structure._serial != args.location:
                continue

            if therm.temperature_scale == 'F':
                temp = nest.utils.f_to_c(therm.temperature)
                target = nest.utils.f_to_c(therm.target)
            else:
                temp = therm.temperature
                target = therm.target

            hvac_state = ['off', 'heating', 'cooling'].index(
                therm.hvac_state)

            topic = '{}/nest/{}'.format(
                args.topic, therm.device_id)
            sample = {
                'sensor_id': therm.device_id,
                'sensor_type': 'nest',
                'location': therm.name.lower(),
                'temperature': temp,
                'temperature_target': target,
                'humidity': therm.humidity,
                'hvac_state': hvac_state,
            }

            LOG.info('sending on %s sample %s', topic, sample)
            msg = json.dumps(sample)
            mq.publish(topic, msg)

        time.sleep(args.interval)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
