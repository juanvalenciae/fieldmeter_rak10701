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

## Set-up the script on RAK gateways

Use scp to copy `main.py` and `lib/docopt.py` on the RAK gateway as follows:

```
scp -O main.py scp://root@<gw_ip>//root/fieldmeter.py
scp -Or lib scp://root@<gw_ip>//root
scp -O rak_setup.sh scp://root@<gw_ip>//etc/init.d/fieldmeter
```

With all the files are transfered execute the following command through ssh:
```
ssh root@<gw_ip>
chmod a+x /etc/init.d/fieldmeter
/etc/init.d/fieldmeter enable
/etc/init.d/fieldmeter start
```
