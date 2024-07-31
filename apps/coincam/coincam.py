from badge import oled,btn,battery,wlan,readConfig
from uikit import selectVList,inputAlphanumeric,msgBox
from time import sleep_ms,localtime
from micropython import const

import os
import machine
import gc

import uasyncio as asyncio
import aioble
import bluetooth

import random
import struct

TIMEOUT_MS = 5000

_ADV_TYPE_MANUFACTURER = const(0xFF)
_FUJIFILM_ID = const(0x04D8)
_FUJIFILM_TYPE_TOKEN = const(0x02)

_FUJIFILM_CHR_CONFIGURE  = const(0x5022)
_FUJIFILM_GEOTAG_UPDATE  = const(0x5042)

_FUJIFILM_SVC_PAIR_UUID = bluetooth.UUID("91f1de68-dff6-466e-8b65-ff13b0f16fb8")
_FUJIFILM_CHR_PAIR_UUID = bluetooth.UUID("aba356eb-9633-4e60-b73f-f52516dbd671")
_FUJIFILM_CHR_IDEN_UUID = bluetooth.UUID("85b9163e-62d1-49ff-a6f5-054b4630d4a1")

_FUJIFILM_SVC_CONF_UUID = bluetooth.UUID("4c0020fe-f3b6-40de-acc9-77d129067b14")
_FUJIFILM_CHR_IND1_UUID = bluetooth.UUID("a68e3f66-0fcc-4395-8d4c-aa980b5877fa")
_FUJIFILM_CHR_IND2_UUID = bluetooth.UUID("bd17ba04-b76b-4892-a545-b73ba1f74dae")
_FUJIFILM_CHR_NOT1_UUID = bluetooth.UUID("f9150137-5d40-4801-a8dc-f7fc5b01da50")
_FUJIFILM_CHR_NOT2_UUID = bluetooth.UUID("ad06c7b7-f41a-46f4-a29a-712055319122")
_FUJIFILM_CHR_IND3_UUID = bluetooth.UUID("049ec406-ef75-4205-a390-08fe209c51f0")

_FUJIFILM_SVC_SHUTTER_UUID = bluetooth.UUID("6514eb81-4e8f-458d-aa2a-e691336cdfac")
_FUJIFILM_CHR_SHUTTER_UUID = bluetooth.UUID("7fcf49c6-4ff0-4777-a03d-1a79166af7a8")

_FUJIFILM_SVC_GEOTAG_UUID = bluetooth.UUID("3b46ec2b-48ba-41fd-b1b8-ed860b60d22b")
_FUJIFILM_CHR_GEOTAG_UUID = bluetooth.UUID("0f36ec14-29e5-411a-a1b6-64ee8383f090")

FUJIFILM_SHUTTER_CMD = [0x01, 0x00]
FUJIFILM_SHUTTER_PRESS = [0x02, 0x00]
FUJIFILM_SHUTTER_RELEASE = [0x00, 0x00]
FUJIFILM_SHUTTER_FOCUS = [0x03, 0x00]

coin_name = readConfig()['name']
print("Badge Name: " + coin_name)

async def fuji_shutter_press(shutter_characteristic):
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_CMD), True, timeout_ms=TIMEOUT_MS)
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_PRESS), True, timeout_ms=TIMEOUT_MS)

async def fuji_shutter_release(shutter_characteristic):
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_CMD), True, timeout_ms=TIMEOUT_MS)
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_RELEASE), True, timeout_ms=TIMEOUT_MS)

async def fuji_shutter_focus(shutter_characteristic):
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_CMD), True, timeout_ms=TIMEOUT_MS)
    await shutter_characteristic.write(bytes(FUJIFILM_SHUTTER_FOCUS), True, timeout_ms=TIMEOUT_MS)

async def find_fuji_camera():
    # Scan for 5 seconds, in active mode, with very low interval/window (to
    # maximise detection rate).
    scanresult_names = []
    scanresult_dev_tok = []
    oled.fill(0)
    oled.fill_rect(0,0,128,9,1)
    oled.hctext('Fuji Scan',1,0)
    oled.hctext('Scanning...',30,1)
    oled.show()
	
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            for i in result.manufacturer():
                if i[0] == _FUJIFILM_ID and result.name() not in scanresult_names and result.name() is not None:
                    mToken = [e for e in i[1][1:]]
                    print("Found Fuji Camera - {} mToken: {}".format(result.name(), "".join("%02x" % e for e in mToken)))
                    scanresult_names.append(result.name())
                    scanresult_dev_tok.append((result.device, mToken))

    if len(scanresult_names) > 0:
        sel = 0
        while sel != -1:
            sel = selectVList('Scan Results', scanresult_names, sel, 1)
            if sel == -1:
                await main_menu()
            sleep_ms(300)
            return scanresult_names[sel], scanresult_dev_tok[sel][0], scanresult_dev_tok[sel][1]
    else:        
        oled.fill(0)
        oled.fill_rect(0,0,128,9,1)
        oled.hctext('Scan Results',1,0)
        oled.hctext('No Camera Found',30,1)
        oled.show()
        sleep_ms(2000)
        return None, None, None        

async def fuji_connect(device, name):
    try:
        print(f"Connecting to {device}, name: {name}")
        oled.fill(0)
        oled.hctext('Connecting to',10,1)
        oled.hctext(name,25,1)
        oled.show()
        connection = await device.connect()
        return connection
    except asyncio.TimeoutError:
        print("Timeout trying to connect to camera")
        oled.fill(0)
        oled.hctext('Connection',10,1)
        oled.hctext('Timeout',25,1)
        oled.show()
        sleep_ms(2000)
        return None

async def connect_existing():
    cameras = open('cam.txt', 'r')
    cam_names = []
    cam_macs = []
    for line in cameras:
        cam_names.append(line.split(',', 1)[0])
        cam_macs.append(line.split(',', 1)[1].strip())
    cameras.close()
    camsel = 0
    while camsel != -1:
        camsel = selectVList('Connect To', cam_names, camsel, 1)
        sleep_ms(300)
        device = aioble.Device(0, cam_macs[camsel])
        return cam_names[camsel], device, 'mtkn'

async def main_menu():
    main_menu_items = ['New Scan', 'Connect', 'Quit']
    sel = 0
    while sel != -1:
        sel = selectVList('Fuji Remote', main_menu_items, sel, 1)
        sleep_ms(300)
        if main_menu_items[sel] == main_menu_items[0]:
            name, device, mToken = await find_fuji_camera()
            return name, device, mToken
        if main_menu_items[sel] == main_menu_items[1]:
            name, device, mToken = await connect_existing()
            return name, device, mToken
        if main_menu_items[sel] == main_menu_items[2]:
            sel = -1

async def fuji_pair(name, connection, device, mToken, newpair):
    try:
        print("Discovering pairing service")
        pair_service = await connection.service(_FUJIFILM_SVC_PAIR_UUID)
        pair_characteristic = await pair_service.characteristic(_FUJIFILM_CHR_PAIR_UUID)
        iden_characteristic = await pair_service.characteristic(_FUJIFILM_CHR_IDEN_UUID)
        
        if newpair:
            print("Writing mToken to _FUJIFILM_CHR_PAIR_UUID characteristic")
            await pair_characteristic.write(bytes(mToken), True, timeout_ms=TIMEOUT_MS)
        
        print("Writing ESP32 badge name to _FUJIFILM_CHR_IDEN_UUID characteristic")
        await iden_characteristic.write(coin_name, True, timeout_ms=TIMEOUT_MS)
        
        print("Discovering and subscribing to configure service")
        conf_service = await connection.service(_FUJIFILM_SVC_CONF_UUID)
        
        print("Subscribing to _FUJIFILM_CHR_IND1_UUID")
        ind1_characteristic = await conf_service.characteristic(_FUJIFILM_CHR_IND1_UUID)
        await ind1_characteristic.subscribe(notify=False, indicate=True)
        
        print("Subscribing to _FUJIFILM_CHR_IND2_UUID")
        ind2_characteristic = await conf_service.characteristic(_FUJIFILM_CHR_IND2_UUID)
        await ind1_characteristic.subscribe(notify=False, indicate=True)
        
        oled.fill(0)
        oled.hctext('Pairing with',10,1)
        oled.hctext(name,25,1)
        oled.show()
        await asyncio.sleep_ms(500)
        
        print("Subscribing to _FUJIFILM_CHR_NOT1_UUID")
        not1_characteristic = await conf_service.characteristic(_FUJIFILM_CHR_NOT1_UUID)
        await not1_characteristic.subscribe(notify=True, indicate=True)
        
        print("Subscribing to _FUJIFILM_CHR_NOT2_UUID")
        not2_characteristic = await conf_service.characteristic(_FUJIFILM_CHR_NOT2_UUID)
        await not2_characteristic.subscribe(notify=True, indicate=True)
        
        print("Subscribing to _FUJIFILM_CHR_IND3_UUID")
        ind3_characteristic = await conf_service.characteristic(_FUJIFILM_CHR_IND3_UUID)
        await ind1_characteristic.subscribe(notify=False, indicate=True)
        
        print("Discovering shutter service")
        shutter_service = await connection.service(_FUJIFILM_SVC_SHUTTER_UUID)
        shutter_characteristic = await shutter_service.characteristic(_FUJIFILM_CHR_SHUTTER_UUID)
        
        if newpair:
            print("Configuration complete, saving camera details")
            cameras = open('cam.txt', 'a')
            cameras.write(name)
            cameras.write(",")
            cameras.write(device.addr_hex())
            cameras.write("\n")
            cameras.close()
    
        return shutter_characteristic
        
    except asyncio.TimeoutError:
        print("Timeout discovering services/characteristics")
        oled.fill(0)
        oled.hctext('Pairing Timeout',30,1)
        oled.show()
        sleep_ms(2000)
        return None

    await asyncio.sleep_ms(1000)
    print("Configuration done")

async def app_start():
    name, device, mToken = await main_menu()
    
    while not name and not device and not mToken:
        print("Camera not found")
        name, device, mToken = await main_menu()

    connection = await fuji_connect(device, name)
    
    if connection is None:
        await app_start()
    
    if mToken == 'mtkn':
        print("Pairing with existing camera")
        shutter_characteristic = await fuji_pair(name, connection, device, mToken, False)
    else:
        shutter_characteristic = await fuji_pair(name, connection, device, mToken, True)
    
    if shutter_characteristic is None:
        await app_start()
    
    if connection.is_connected():
        actions = ['Shutter', 'Single Focus', 'Continuous Focus', 'Disconnect']
        sel = 0
        print("Paired with Fujifilm camera")
        while sel != -1:
            sel = selectVList(name, actions, sel, 1)
            sleep_ms(300)
            if actions[sel] == actions[0]:
                await fuji_shutter_press(shutter_characteristic)
                await fuji_shutter_release(shutter_characteristic)
            if actions[sel] == actions[1]:
                await fuji_shutter_focus(shutter_characteristic)
                await fuji_shutter_release(shutter_characteristic)
            if actions[sel] == actions[2]:
                await fuji_shutter_focus(shutter_characteristic)
            if actions[sel] == actions[3]:
                await connection.disconnect(timeout_ms=TIMEOUT_MS)
                return
        
    await connection.disconnect(timeout_ms=TIMEOUT_MS)

asyncio.run(app_start())
