from __future__ import annotations

import sys
import math
import asyncio
import time
import random

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError


class NsBleClient:

    MANUFACTURER_DATA = {0xffff: b'$tZuFTNvsLGt9U^gsCM!t8$@Fd6'}

    SERVICE_UUID = '00000000-b1b6-417b-af10-da8b3de984be'
    BRIGHTNESS_UUID = '00000001-b1b6-417b-af10-da8b3de984be'
    VOLUME_UUID = '00000002-b1b6-417b-af10-da8b3de984be'
    PAUSE_VOLUME_UUID = '10000001-b1b6-417b-af10-da8b3de984be'

    LUX_TO_NITS = 1 / math.pi

    @staticmethod
    def encode(string: str) -> bytes:
        return string.encode('utf-8')

    @staticmethod
    def decode(byte_array: bytearray) -> str:
        return byte_array.decode('utf-8')

    async def find_device(self) -> BLEDevice:
        print('Discovering devices...')
        async with BleakScanner() as scanner:

            start_time = time.time()
            future = asyncio.Future()
            detected = set()

            def detection_callback(device: BLEDevice, data: AdvertisementData):
                if device.address not in detected:
                    detected.add(device.address)
                    print(' ', device)
                    if data.manufacturer_data == self.MANUFACTURER_DATA:
                        time_used = time.time() - start_time
                        print(f'Device found after {time_used:.2f} s')
                        future.set_result(device)

            scanner.register_detection_callback(detection_callback)
            return await future

    def __init__(self):
        self.brightness = 0
        self.volume = 0
        self.device = None
        self.client: BleakClient | None = None
        self.service = None
        self.ready = False
        self.brightness_characteristic = None
        self.volume_characteristic = None
        self.pause_characteristic = None

    @property
    def is_connected(self):
        return self.ready and self.client is not None and self.client.is_connected

    async def discover_and_connect(self):
        self.device = await self.find_device()
        print(f'Connecting to device {self.device.address}...')

        self.client = BleakClient(self.device)
        await self.client.connect()
        print('Connected. Getting services...')
        # note: due to a bug in Windows connection will fail if we pair with the device
        #       so never try to pair with it
        services = await self.client.get_services()
        self.service = services.get_service(self.SERVICE_UUID)
        print('Got services.')

        for c in self.service.characteristics:
            print()
            print(c.uuid, c.description)
            byte_array = await self.client.read_gatt_char(c)
            print('Read:', self.decode(byte_array))

            if c.uuid == self.BRIGHTNESS_UUID:
                self.brightness_characteristic = c
            if c.uuid == self.VOLUME_UUID:
                self.volume_characteristic = c
            if c.uuid == self.PAUSE_VOLUME_UUID:
                self.pause_characteristic = c

        self.ready = True

    async def subscribe(self, fn_brightness, fn_volume, fn_disconnect):
        def make_callback(fn, initial):
            fn(initial, initial)
            previous = initial

            def callback(_, raw):
                nonlocal previous
                value = float(self.decode(raw))
                fn(value, previous)
                previous = value

            return callback

        self.client.set_disconnected_callback(fn_disconnect)

        async def subscribe(characteristic, fn_callback, fn_initial):
            await self.client.start_notify(
                characteristic,
                make_callback(fn_callback, await fn_initial()))

        await asyncio.gather(
            subscribe(self.brightness_characteristic, fn_brightness, self.get_brightness),
            subscribe(self.volume_characteristic, fn_volume, self.get_volume),
        )

    async def get_brightness(self):
        raw = await self.client.read_gatt_char(self.brightness_characteristic)
        value = self.decode(raw)
        return float(value)

    async def get_volume(self):
        raw = await self.client.read_gatt_char(self.volume_characteristic)
        value = self.decode(raw)
        return float(value)

    async def pause_volume(self, previous_volume):
        await self.client.write_gatt_char(self.pause_characteristic, self.encode(str(previous_volume)))


class NsDummyClient:
    async def discover_and_connect(self):
        await asyncio.sleep(0)

    async def get_brightness(self):
        await asyncio.sleep(0.2)
        # returns brightness in lux
        return random.uniform(1, 20000)

    async def get_volume(self):
        await asyncio.sleep(0.1)
        # unknown unit
        return random.uniform(0, 1)

    async def pause_volume(self):
        await asyncio.sleep(0.1)
