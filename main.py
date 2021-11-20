from __future__ import annotations
import re
from datetime import datetime, timedelta
import asyncio

import PySimpleGUIQt as sg
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from volume_control import *
from brightness_control import *
from bluetooth_test_client import *
from serialization import *
from calibration import *


# https://docs.microsoft.com/en-us/windows/win32/api/endpointvolume/nn-endpointvolume-iaudioendpointvolume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))


monitors = sbc.list_monitors()
num_displays = len(monitors)
num_audio = 1


def font(size: int):
    return 'Consolas' + ' ' + str(size)


sg.theme("Dark")
header_font = font(24)
body_font = font(14)
small_body_font = font(10)


def make_window():
    full_size = (1000, 700)  # width, height

    monitor_image = "monitor_image.png"
    speaker_image = "speaker_image.png"

    left_col = [[sg.Image(monitor_image)], [sg.Text("\nDisplays\n", font=header_font)]]

    for i in range(num_displays):
        key = 'display' + str(i)
        image_col = [[sg.Text("\n", font=font(2))],
                     [sg.Text("Display\n", font=body_font)]]
        settings_col = [[sg.Text("\n", font=font(6))],
                        [sg.Slider(range=(0, 100), orientation='h', key=key,
                                   disabled=False, enable_events=True),
                         sg.Text("", key=key + '.text', font=small_body_font)],
                        [sg.Checkbox("Enable !surprised", key=key + '.enabled', enable_events=True, font=small_body_font, size=(23, 1.75))]]
        device_unit = [[sg.Column(image_col, element_justification='c'), sg.Column(settings_col)]]
        left_col.append([sg.Column(device_unit)])

    right_col = [[sg.Image(speaker_image)], [sg.Text("\nAudio\n", font=header_font)]]

    for i in range(num_audio):
        key = 'audio' + str(i)
        image_col = [[sg.Text("\n", font=font(2))],
                     [sg.Text("Speaker\n", font=body_font)]]
        settings_col = [[sg.Text("\n", font=font(6))],
                        [sg.Slider(range=(0, 100), orientation='h', key=key,
                                   disabled=False, enable_events=True),
                         sg.Text("", key=key + '.text', font=small_body_font)],
                        [sg.Checkbox("Enable !surprised", key=key + '.enabled', enable_events=True, font=small_body_font, size=(23, 1.25))],
                        [sg.Checkbox("Is speaker", key=key + '.speaker', enable_events=True, font=small_body_font)]]
        device_unit = [[sg.Column(image_col, element_justification='c'), sg.Column(settings_col)]]
        right_col.append([sg.Column(device_unit)])

    calibrate_button = sg.Button('Calibrate', font=body_font, size=(160, 70), button_color=("#dedede", "#3f618a"))
    clear_button = sg.Button('Clear', font=body_font, size=(160, 70), button_color=("#dedede", "#c74d42"))

    button_container = [[sg.Stretch(), clear_button, sg.Text("\t"), calibrate_button, sg.Stretch()]]

    layout = [[sg.Stretch(),
               sg.Column(left_col, element_justification='c'),
               sg.Stretch(),
               sg.Stretch(),
               sg.Column(right_col, element_justification='c'),
               sg.Stretch()],
              [sg.Column(button_container, element_justification='c')]]
    scrollable = [[sg.Column(layout, size=full_size, scrollable=True)]]
    window = sg.Window("!surprised", scrollable, size=full_size, icon="logo.png", resizable=False, disable_minimize=True)
    return window


def make_tray():
    menu = ['', ['&Configure', '---', 'E&xit']]
    tooltip = '!surprised'
    tray = sg.SystemTray(menu, tooltip=tooltip, filename="logo.png")
    return tray


def show_popup():
    choice, _ = sg.Window('Success!',
                          [[sg.Text('\nCalibration Successful!\n', font=small_body_font)]],
                          disable_minimize=True, resizable=False, icon="logo.png", size=(250, 150))\
        .read(close=True)


def show_confirmation():
    choice, _ = sg.Window('Are you sure?',
                          [[sg.Text('\nDo you want to clear all calibration data?\n', font=small_body_font)],
                           [sg.Stretch(),
                            sg.Button('Yes', font=small_body_font, size=(100, 40), button_color=("#dedede", "#c74d42")),
                            sg.Button('No',  font=small_body_font, size=(100, 40), button_color=("#dedede", "#3f618a")),
                            sg.Stretch()]],
                          disable_minimize=True, resizable=False, icon="logo.png", size=(400, 150))\
        .read(close=True)
    return choice == 'Yes'


def read(window: sg.Window | None, tray: sg.SystemTray, timeout=100) -> tuple[str, dict | None]:
    if window is not None:
        event, values = window.read(timeout / 2)
        if event != sg.TIMEOUT_EVENT:
            return event, values
    event = tray.read(timeout / 2)
    return event, {}


def check_slider_changes(event: str, values: dict[str, int], no_refresh_until: dict[str, datetime]) -> bool:
    if not event or not values:
        return False

    prefix, i, suffix = parse_key(event)
    if suffix:
        return False
    elif prefix == 'display':
        value = values[event]
        sbc.set_brightness(value, i)
    elif prefix == 'audio':
        value = values[event]
        volume.SetMasterVolumeLevelScalar(value / 100, None)
    else:
        return False

    no_refresh_until[event] = datetime.now() + timedelta(milliseconds=500)
    return True


def refresh_values(window: sg.Window | None, no_refresh_until: dict[str, datetime]):
    def should_refresh(key):
        if key in no_refresh_until:
            if datetime.now() < no_refresh_until[key]:
                print(key)
                return False
            else:
                del no_refresh_until[key]
        return True

    if window is None:
        return
    for i in range(num_displays):
        key = "display" + str(i)
        if should_refresh(key):
            slider = window[key]
            if type(sbc.get_brightness()) == int:
                slider.update(sbc.get_brightness())
            else:
                slider.update(sbc.get_brightness()[i])
    for i in range(num_audio):
        key = "audio" + str(i)
        if should_refresh(key):
            slider = window[key]
            slider.update(volume.GetMasterVolumeLevelScalar() * 100)


def update_slider_text(window: sg.Window | None, values: dict[str, int]):
    def update(key: str):
        if key in values:
            value = values[key]
            window[key + '.text'].update(str(value) + '%')

    if window is None:
        return
    for i in range(num_displays):
        update("display" + str(i))
    for i in range(num_audio):
        update("audio" + str(i))


def parse_key(key: str) -> tuple[str, int, str]:
    match = re.match(r'^(.+)([0-9]+).?([A-Za-z]*)$', key)
    if match is not None:
        groups = match.groups()
        return groups[0], int(groups[1]), groups[2]
    else:
        return '', -1, ''


async def calibrate(client, brightness_points, volume_points):
    brightness_points.append(await getBrightnessPoint(client))
    volume_points.append(await getVolumePoint(client))
    serialize((brightness_points, volume_points))


async def run():
    client = NsDummyClient()
    await client.discover_and_connect()

    try:
        brightness_points, volume_points = deserialize()
    except:
        brightness_points = []
        volume_points = []

    window = make_window()
    tray = make_tray()
    no_refresh_until = {}
    while True:
        await asyncio.sleep(0.01)
        event, values = read(window, tray, 10)
        update_slider_text(window, values)
        if not check_slider_changes(event, values, no_refresh_until):
            refresh_values(window, no_refresh_until)
        if event != sg.TIMEOUT_EVENT:
            print(event, values)
            if window is not None:
                if event in [sg.WIN_CLOSED]:
                    window.close()
                    window = None
                if event in ["Calibrate"]:
                    await calibrate(client, brightness_points, volume_points)
                    show_popup()
                if event in ["Clear"]:
                    if show_confirmation():
                        print('boom')
            else:
                if event in ["Configure", sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED]:
                    window = make_window()
            if event in ["Exit"]:
                break

    tray.close()
    if window is not None:
        window.close()


if __name__ == "__main__":
    asyncio.run(run())
