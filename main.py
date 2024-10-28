#!/usr/bin/python3
"""Usage:
    fieldmeter.py [options] SUB_TOPIC PUB_TOPIC

Options:
    -h --help                       Show this message
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
import warnings
from datetime import datetime
from paho.mqtt.client import Client, MQTTMessage
from lib.docopt import docopt
from sys import stderr, stdout
from os import environ

global sequence_id
sequence_id = 0

warnings.filterwarnings("ignore", category=SyntaxWarning)

def printlog(*args, **kwargs):
    now = datetime.now()
    print("%s:" % now.isoformat(), *args, file=stderr, **kwargs)
    pass

def get_response_payload(up_payload: dict, seq_id: int = sequence_id) -> str:
    n_hostspots = len(up_payload["rxInfo"])
    if n_hostspots <= 0:
        min_rssi = 0
        max_rssi = 0
        max_dist = 0
        min_dist = 0
    else:
        rssi_values = [x['rssi'] for x in up_payload["rxInfo"]]
        max_rssi = max(max(rssi_values) + 200, 0)
        min_rssi = max(min(rssi_values) + 200, 0)
        max_dist = 1
        min_dist = 1

    bytes_list = [
            seq_id % 255,
            min_rssi,
            max_rssi,
            min_dist,
            max_dist,
            n_hostspots
            ]
    out_bytes = bytes(bytes_list)
    return out_bytes.hex()

def on_message_decorator(func, pub_topic: str, qos: int=0, *args):
    return func(*args)

def on_connect(_, userdata, conn_flags, reason_code):
    printlog("connect event %s" % reason_code)
    pass

def on_subscribe(client, userdata, mid, reason_code):
    printlog("subscribe event %s" % reason_code)
    pass

def on_message_creator(pub_topic: str, pub_qos: int = 0, fp = stdout):
    def on_message(client: Client, _, msg: MQTTMessage):
        msg_string = msg.payload.decode("utf-8")
        try:
            json_data = json.loads(msg_string)
            metadata_keys = ["fCnt", "fPort", "adr", "data_encode"]
            metadata = tuple(json_data[i] for i in metadata_keys) +\
                    tuple(json_data["txInfo"][i] for i in ["frequency", "dr"])
            printlog("message event: fCnt=%d fPort=%d adr=%s data_encode=%s freq=%s dr=%s" % metadata)
            #json.dump(json_data, stdout, indent=2)
            msg_payload = get_response_payload(json_data)
            mqtt_response = {"confirmed": False, "data": msg_payload, "fPort": 2}
            client.publish(
                    pub_topic,
                    json.dumps(mqtt_response),
                    qos=pub_qos,
                    )
            print(msg_payload, file=fp)

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
    out_file = open(args["--output"], "a")

    mqttc = Client()
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
