#!/usr/bin/python3
"""Usage:
    fieldmeter.py [options] SUB_TOPIC PUB_TOPIC

Options:
    -h --help                       Show this message
    -t --tls                        Use TLS/SSL for mqtt connections
    -b URL --broker=URL             Set the broker url [default: 127.0.0.1]
    -P PORT --port=PORT             Select the broker port [default: 1883]
    -u USER --username=USER         Set the username [default: user]
    -p PASSWD --password=PASSWD     Set username password [default: 1234]
    --pub-qos=QOS                   Select Subscriber QOS [default: 0]
    --sub-qos=QOS                   Select Subscriber QOS [default: 1]
    -o FILE --output=FILE           Set output file [default: /dev/stdout]

Environment:
    FIELDMETER_BROKER_IP
        overwrite Broker ip address
    FIELDMETER_USER
        overwrite username
    FIELDMETER_PASSWD
        overwrite password
"""

import json
from math import pi, sin, cos, acos
import warnings
from datetime import datetime
from paho.mqtt.client import Client, MQTTMessage
from lib.docopt import docopt
from sys import stderr, stdout
from os import environ
from base64 import b64encode, b64decode

global sequence_id
sequence_id = 0

warnings.filterwarnings("ignore", category=SyntaxWarning)

def printlog(*args, **kwargs):
    now = datetime.now()
    print("%s:" % now.isoformat(), *args, file=stderr, **kwargs)
    pass

def distance(lat1, lon1, lat2, lon2):
    if (lat1 == lat2) and (lon1 == lon2): return 0;

    rad_lat1 = pi * lat1 / 180
    rad_lat2 = pi * lat2 / 180
    theta = lon1 - lon2
    rad_theta = pi * theta / 180
    dist = sin(rad_lat1) * sin(rad_lat2) + cos(rad_lat1) * cos(rad_lat2) * cos(rad_theta)
    if (dist > 1):
        dist = 1
    dist = acos(dist)
    dist = dist * 180 / pi
    dist = dist * 60 * 1.1515
    dist = dist * 1.609344
    return dist

def get_response_payload(up_payload: dict, seq_id: int = sequence_id) -> str:
    n_hostspots = len(up_payload["rxInfo"])
    if n_hostspots <= 0:
        min_rssi = 0
        max_rssi = 0
        max_dist = 0
        min_dist = 0
    else:
        rssi_values = [x['rssi'] for x in up_payload["rxInfo"]]

        try:
            gw_locs = [x for x in up_payload["rxInfo"]
                       if "source" not in x["location"].keys()]

            dists_values = [distance(x["location"]["latitude"],
                                     x["location"]["longitude"],
                                     up_payload["object"]["latitude"],
                                     up_payload["object"]["longitude"])
                            for x in gw_locs]

        except Exception as e:
            printlog("Error %s: %s" % (e, json.dumps(up_payload)))

        max_rssi = int(max(max(rssi_values) + 200, 0))
        min_rssi = int(max(min(rssi_values) + 200, 0))
        #printlog(f"{json.dumps(up_payload)=}")
        if len(dists_values) > 0:
            max_dist = max(int(min(dists_values) * 1000 / 250), 1)
            min_dist = max(int(max(dists_values) * 1000 / 250), 1)
        else:
            max_dist = min_dist = 1

    bytes_list = [
            seq_id % 255,
            min_rssi,
            max_rssi,
            min_dist,
            max_dist,
            n_hostspots
            ]
    out_bytes = bytes(bytes_list)
    printlog("downlink payload: %s" % out_bytes.hex())
    return out_bytes

def on_message_decorator(func, pub_topic: str, qos: int=0, *args):
    return func(*args)

def on_connect(_, userdata, conn_flags, reason_code):
    printlog("connect event %s" % reason_code)
    pass

def on_subscribe(client, userdata, mid, reason_code):
    printlog("subscribe event %s" % reason_code)
    pass

def payload_decode(payload: bytes):
    out = dict()
    lon_sign = -1 if ((payload[0] >> 7) & 0x1) else 1
    lat_sign = -1 if ((payload[0] >> 6) & 0x1) else 1

    enc_lat = ((payload[0] & 0x3f) << 17) + \
              (payload[1] << 9) + \
              (payload[2] << 1) + \
              (payload[3] >> 7)

    enc_lon = ((payload[3] & 0x3f) << 16) + \
              (payload[4] << 8) + \
              (payload[5])

    hdop = payload[8] / 10
    sats = payload[9]

    max_hdop = 2
    min_sats = 5

    if (hdop < max_hdop) and (sats >= min_sats):
        out["latitude"] = lat_sign * (enc_lat * 108 + 53) / 10000000
        out["longitude"] = lon_sign * (enc_lon * 215 + 107) / 10000000
        out["altitude"] = ((payload[6] << 8) + payload[7]) - 1000
        out["accuracy"] = (hdop * 5 + 5) / 10
        out["hdop"] = hdop
        out["sats"] = sats
    else:
        out["error"] = "Need more GPS precision (hdop must be < %d " \
                       "& sats must be >= %d) current hdop: %d & sats: %d" \
                       % (max_hdop, min_sats, hdop, sats)
        out["latitude"] = lat_sign * (enc_lat * 108 + 53) / 10000000
        out["longitude"] = lon_sign * (enc_lon * 215 + 107) / 10000000
        out["altitude"] = ((payload[6] << 8) + payload[7]) - 1000
        out["accuracy"] = (hdop * 5 + 5) / 10
        out["hdop"] = hdop
        out["sats"] = sats
    return out

def on_message_creator(pub_topic: str, pub_qos: int = 0, fp = stdout):
    def on_message(client: Client, _, msg: MQTTMessage):
        msg_string = msg.payload.decode("utf-8")
        try:

            json_data = json.loads(msg_string)
            if json_data["fPort"] != 1: return

            data_bytes = b64decode(json_data["data"])
            decoded_payload = payload_decode(data_bytes)

            metadata_keys = ["fCnt", "fPort", "adr", "data"]
            metadata = list(json_data[i] for i in metadata_keys)
            metadata.append(json.dumps(decoded_payload))

            json_data["object"] = decoded_payload

            printlog("message event: fCnt=%d fPort=%d adr=%s data_encode=%s obj=%s" % tuple(metadata))
            #json.dump(json_data, stdout, indent=2)
            msg_payload = b64encode(get_response_payload(json_data)).decode()
            mqtt_response = {"confirmed": False,
                             "data": msg_payload,
                             "fPort": 2,
                             "devEui": json_data["deviceInfo"]["devEui"]}
            client.publish(
                    pub_topic,
                    json.dumps(mqtt_response),
                    qos=pub_qos,
                    )

        except json.JSONDecodeError:
            printlog("error: unable to decode '%s'", msg_string)
    return on_message

if __name__ == "__main__":
    args = docopt(str(__doc__), version="0.1")

    broker_ip = args["--broker"] if not environ.get("FIELDMETER_BROKER_IP") else str(environ.get("FIELDMETER_BROKER_IP"))
    broker_port = int(args["--port"])
    username = args["--username"] if not environ.get("FIELDMETER_USER") else str(environ.get("FIELDMETER_USER"))
    passwd = args["--password"] if not environ.get("FIELDMETER_PASSWD") else str(environ.get("FIELDMETER_PASSWD"))
    sub_qos = int(args["--sub-qos"])
    pub_qos = int(args["--pub-qos"])
    out_file = stdout if args["--output"] else open(args["--output"], "a")

    mqttc = Client()
    if args["--tls"]:
        mqttc.tls_set()
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.on_message = on_message_creator(args["PUB_TOPIC"], pub_qos, out_file)

    mqttc.username_pw_set(username, passwd)
    mqttc.connect(broker_ip, broker_port)
    mqttc.subscribe(args["SUB_TOPIC"], qos = sub_qos)

    try:
        mqttc.loop_forever()
    except KeyboardInterrupt:
        printlog("key interrupt event, bye")
    finally:
        out_file.close()
