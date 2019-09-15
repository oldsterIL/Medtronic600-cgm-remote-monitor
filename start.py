#!/usr/bin/python

import datetime
import json
import re
import subprocess
import sys
import time

from decoding import read_minimed_next24

import RPi.GPIO as GPIO
import pytz
import serial

ser = serial.Serial('/dev/ttyAMA0',115200)
ser.flushInput()

power_key = 4

def get_wifi_signal ():
    # Return Wi-Fi Level (0-100)
    bashCommand = "/sbin/iw dev wlan0 link"
    signal_re = re.compile(u'signal: -(\d+)')
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE).stdout.read().splitlines()
    for out in process:
        signal_dBm = signal_re.search(out)
        if signal_dBm:
            signal_level = (100 - int(signal_dBm.group(1))) * 2
            if signal_level > 100:
                signal_level = 100
            return signal_level
    return 0

def get_gsm_level():
    # Return GSM Level (0-5)
    CSQ_REGEX = re.compile(u'\+CSQ:\s*(\d+),')

    GSMLevel = 0
    send_at('AT','OK',1)
    answer = send_at('AT+CSQ','OK',1)
    csq = CSQ_REGEX.search(answer)
    if csq:
        GSMLevel_dBm = 112 - (int(csq.group(1)) * 2)
        if GSMLevel_dBm > 0 and GSMLevel_dBm <= 75:
            GSMLevel = 5
        if GSMLevel_dBm > 75 and GSMLevel_dBm <= 85:
            GSMLevel = 4
        if GSMLevel_dBm > 85 and GSMLevel_dBm <= 95:
            GSMLevel = 3
        if GSMLevel_dBm > 95 and GSMLevel_dBm <= 105:
            GSMLevel = 2
        if GSMLevel_dBm > 105:
            GSMLevel = 1
    return GSMLevel

def get_cpu_temp():
    # Return CPU temperature
    bashCommand = "cat /sys/class/thermal/thermal_zone0/temp"
    cpu_temp = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE).stdout.read().splitlines()
    for out in cpu_temp:
        return float(out) / 1000
    return 0

def send_at(command,back,timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.1 )
        rec_buff = ser.read(ser.inWaiting())
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(command + ' ERROR')
            print(command + ' back:\t' + rec_buff.decode())
            return 0
        else:
            return rec_buff.decode()

def get_gps_position():

    gps = {}
    send_at('AT', 'OK', 1)
    send_at('AT+CGNSPWR=1','OK',1)

    gps_regexp = re.compile(u'\+CGNSINF:\s*(\d+),')
    for x in range(6):
        answer = send_at('AT+CGNSINF','+CGNSINF: ',1)
        gps_data = gps_regexp.search(answer)
        if int(gps_data.group(1)) == 1:
            gps_regexp = re.compile(u'\+CGNSINF:\s*(.*)')
            gps_data = gps_regexp.search(answer)
            gps = gps_data.group(1).split(",")
            break
        time.sleep(1)
    return gps



def power_on(power_key):
    print('SIM7600X is starting:')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key,GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key,GPIO.HIGH)
    time.sleep(2)
    GPIO.output(power_key,GPIO.LOW)
    time.sleep(2)
    ser.flushInput()
    print('SIM7600X is ready')

def power_down(power_key):
    print('SIM7600X is loging off:')
    GPIO.output(power_key,GPIO.HIGH)
    time.sleep(3)
    GPIO.output(power_key,GPIO.LOW)
    time.sleep(2)
    print('Good bye')


def pumpDownload(mt):
    status = mt.getPumpStatus()

    sensorBGL = round((status.sensorBGL / 18.016), 1)
    SensorBGLDate = status.sensorBGLTimestamp.strftime("%d-%m-%Y %H:%M:%S")
    BGLtrend = status.trendArrow

    if sensorBGL >= 42:
        sensorBGL = "Unknown"

    if SensorBGLDate == "01-01-1970 04:00:00":
        BGLtrend = "Unknown trend"
        sensorBGL = "Unknown"
        SensorBGLDate = time.strftime("%d-%m-%Y %H:%M:%S")

    out_data['CONTUR']['ActiveInsulin'] = status.activeInsulin
    out_data['CONTUR']['SensorBGL'] = sensorBGL
    out_data['CONTUR']['SensorBGLDate'] = SensorBGLDate
    out_data['CONTUR']['BGLtrend'] = BGLtrend
    out_data['CONTUR']['CurrentBasalRate'] = status.currentBasalRate
    out_data['CONTUR']['TempBasalRate'] = status.tempBasalRate
    out_data['CONTUR']['TempBasalPercentage'] = status.tempBasalPercentage
    out_data['CONTUR']['TempBasalMinutesRemaining'] = status.tempBasalMinutesRemaining
    out_data['CONTUR']['UnitsRemaining'] = status.insulinUnitsRemaining
    out_data['CONTUR']['Battery'] = status.batteryLevelPercentage

if __name__ == '__main__':

    out_data = {
        'RPI': {
        },
        'GPS': {
        },
        'CONTUR': {
        }
    }
    read_minimed_next24.downloadPumpSession(pumpDownload)

    gps = get_gps_position()
    if int(gps[1]) == 1:
        out_data['GPS']['Datetime'] = datetime.datetime.strptime(str(gps[2]), '%Y%m%d%H%M%S.%f').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Samara')).strftime('%Y-%m-%d %H:%M:%S')
        out_data['GPS']['Latitude'] = float("{0:.6f}".format(float(gps[3])))
        out_data['GPS']['Longitude'] = float("{0:.6f}".format(float(gps[4])))
        out_data['GPS']['Altitude'] = float("{0:.3f}".format(float(gps[5])))
        out_data['GPS']['Speed'] = float("{0:.2f}".format(float(gps[6])))
        #out_data['GPS']['Course'] = float("{0:.2f}".format(float(gps[7])))

        GPS_Satellites = gps[14]
        if GPS_Satellites:
            out_data['GPS']['GPS_Satellites'] = int(GPS_Satellites)
        else:
            out_data['GPS']['GPS_Satellites'] =0

        GNSS_Satellites = gps[15]
        if GNSS_Satellites:
            out_data['GPS']['GNSS_Satellites'] = int(GNSS_Satellites)
        else:
            out_data['GPS']['GNSS_Satellites'] =0

        GLONASS_Satellites = gps[16]
        if GLONASS_Satellites:
            out_data['GPS']['GLONASS_Satellites'] = int(GLONASS_Satellites)
        else:
            out_data['GPS']['GLONASS_Satellites'] =0


    out_data['RPI']['CPU_temperature'] = float("{0:.1f}".format(get_cpu_temp()))
    out_data['RPI']['WiFi_Level'] = get_wifi_signal()
    out_data['RPI']['GSM_Level'] = get_gsm_level()


    with open("/tmp/data_zabbix.txt", 'w') as f:
        f.write('"Zabbix server" contur ' + json.dumps(out_data))

    ser.close()
    sys.exit(0)
