function decodeUplink(input) {
    var decoded = {};
    // avoid sending Downlink ACK to integration (Cargo)
    if ((input.fPort === 1) || (input.fPort === 2)){
        var lonSign = (input.bytes[0] >> 7) & 0x01 ? -1 : 1;
        var latSign = (input.bytes[0] >> 6) & 0x01 ? -1 : 1;

        var encLat = ((input.bytes[0] & 0x3f) << 17) +
            (input.bytes[1] << 9) +
            (input.bytes[2] << 1) +
            (input.bytes[3] >> 7);

        var encLon = ((input.bytes[3] & 0x7f) << 16) +
            (input.bytes[4] << 8) +
            input.bytes[5];

        var hdop = input.bytes[8] / 10;
        var sats = input.bytes[9];

        var maxHdop = 2;
        var minSats = 5;

        if ((hdop < maxHdop) && (sats >= minSats)) {
            // Send only acceptable quality of position to mappers
            decoded.latitude = latSign * (encLat * 108 + 53) / 10000000;
            decoded.longitude = lonSign * (encLon * 215 + 107) / 10000000;
            decoded.altitude = ((input.bytes[6] << 8) + input.bytes[7]) - 1000;
            decoded.accuracy = (hdop * 5 + 5) / 10
            decoded.hdop = hdop;
            decoded.sats = sats;
        } else {
            decoded.error = "Need more GPS precision (hdop must be <" + maxHdop +
                " & sats must be >= " + minSats + ") current hdop: " + hdop + " & sats:" + sats;
            decoded.latitude = latSign * (encLat * 108 + 53) / 10000000;
            decoded.longitude = lonSign * (encLon * 215 + 107) / 10000000;
            decoded.altitude = ((input.bytes[6] << 8) + input.bytes[7]) - 1000;
            decoded.accuracy = (hdop * 5 + 5) / 10
            decoded.hdop = hdop;
            decoded.sats = sats;
        }
        return {data: decoded};
    }
    return {data: null};
}
