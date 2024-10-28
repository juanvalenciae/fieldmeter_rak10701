#!/bin/sh /etc/rc.common

USE_PROCD=1
START=89

start_service() {
    deveui=8888888888883333 # Replace this field depending on your device eui
    app_name=fieldmeter # Replace this value by the application name set in the rak built-in server
    procd_open_instance fieldmeter
    procd_set_param command /usr/bin/python3 "/root/fieldmeter.py"
    procd_append_param command "application/$app_name/device/$deveui/rx" # Replace application and device eui according
    procd_append_param command "application/$app_name/device/$deveui/tx"
    procd_close_instance
}
