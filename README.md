# Field Meter MQTT Client

## Usage

```
Usage:
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
```

## Run the script on the gateway

Use scp to copy `main.py` and `lib/docopt.py` on the RAK gateway as follows:

```
scp -O main.py root@<gw_ip>:/root
scp -Or lib root@<gw_ip>:/root
```
