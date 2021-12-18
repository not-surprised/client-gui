from __future__ import annotations
import re
from datetime import datetime, timedelta

import PySimpleGUIQt as sg

import brightness_control
import volume_control
import audio_listener
from serialization import *
from calibration import *
from logger import Logger


# https://docs.microsoft.com/en-us/windows/win32/api/endpointvolume/nn-endpointvolume-iaudioendpointvolume

monitors = brightness_control.getMonitors()
num_displays = 1
num_audio = 1


def font(size: int):
    return 'Consolas' + ' ' + str(size)


sg.theme("Dark")
header_font = font(24)
body_font = font(14)
small_body_font = font(10)


def make_window():
    full_size = (1000, 760)  # width, height

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
                        [sg.Checkbox("Enable !surprised", key=key + '.enabled',
                                     enable_events=True, font=small_body_font, size=(23, 1.75))]]
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
                        [sg.Checkbox("Enable !surprised", key=key + '.enabled',
                                     enable_events=True, font=small_body_font, size=(23, 1.25))],
                        [sg.Checkbox("Is speaker", key=key + '.speaker',
                                     enable_events=True, font=small_body_font)]]
        device_unit = [[sg.Column(image_col, element_justification='c'), sg.Column(settings_col)]]
        right_col.append([sg.Column(device_unit)])

    calibrate_button1 = sg.Button('Calibrate display', font=body_font, size=(300, 70), button_color=("#dedede", "#3f618a"))
    calibrate_button2 = sg.Button('Calibrate audio', font=body_font, size=(300, 70), button_color=("#dedede", "#3f618a"))

    debug_editor = sg.Multiline('', key='debug', font=small_body_font, size=(800, 100))
    clear_button = sg.Button('Clear', font=small_body_font, size=(160, 40), button_color=("#dedede", "#c74d42"))
    debug_apply = sg.Button("Apply calibration data", key='debug.apply', font=small_body_font, size=(300, 40))
    log_button = sg.Button('View logs', key='debug.logs', font=small_body_font, size=(160, 40))

    button_container = [[sg.Stretch(), calibrate_button1, sg.Text('\t'), calibrate_button2, sg.Stretch()],
                        [debug_editor],
                        [sg.Stretch(), clear_button, sg.Stretch(), debug_apply, sg.Stretch(), log_button, sg.Stretch()]]

    layout = [[sg.Stretch(),
               sg.Column(left_col, element_justification='c'),
               sg.Stretch(),
               sg.Stretch(),
               sg.Column(right_col, element_justification='c'),
               sg.Stretch()],
              [sg.Column(button_container, element_justification='c')]]
    scrollable = [[sg.Column(layout, size=full_size, scrollable=True)]]
    window = sg.Window("!surprised", scrollable, size=full_size, icon="logo.png",
                       resizable=False, disable_minimize=True)
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
        brightness_control.setBrightness(value)
    elif prefix == 'audio':
        value = values[event]
        volume_control.setVolume(value)
    else:
        return False

    no_refresh_until[event] = datetime.now() + timedelta(milliseconds=500)
    return True


async def auto_adjust(client, enabled, brightness_points, volume_points):

    async def adjust(points, fn):
        if len(points) >= 2:
            points.sort(key=firstElement)
            x = listOfFirst(points)
            y = listOfSecond(points)
            await fn(client, x, y)

    tasks = []
    if enabled['display0.enabled']:
        tasks.append(adjust(brightness_points, brightness))
    if enabled['audio0.enabled']:
        tasks.append(adjust(volume_points, volume))

    await asyncio.gather(*tasks)


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
            value = brightness_control.getBrightness2(i)
            slider.update(value)
    for i in range(num_audio):
        key = "audio" + str(i)
        if should_refresh(key):
            slider = window[key]
            value = volume_control.getVolume()
            slider.update(value)


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


async def calibrate(client, brightness_points, volume_points, enabled):
    if brightness_points is not None:
        add_point(brightness_points, await getBrightnessPoint(client))
    if volume_points is not None:
        add_point(volume_points, await getVolumePoint(client))


def deserialize_calibration():
    try:
        brightness_points, volume_points, enabled = deserialize()
    except:
        brightness_points = []
        volume_points = []
        enabled = {'display0.enabled': False, 'audio0.enabled': False, 'audio0.speaker': False}

    return brightness_points, volume_points, enabled


async def run():
    async def connect():
        nonlocal client
        _client = NsBleClient()
        await _client.discover_and_connect()
        client = _client

    def apply_changes():
        data = (brightness_points, volume_points, enabled)
        serialize(data)
        window['debug'].update(repr(data))
        for key in enabled:
            window[key].update(enabled[key])

    async def auto_adjust_safe():
        nonlocal client
        if client is not None:
            try:
                if enabled['audio0.speaker']:
                    is_playing_audio = await audio_listener.is_playing_audio()
                    if is_playing_audio:
                        await client.pause_volume()
                        print('Pausing volume update')
                await auto_adjust(client, enabled, brightness_points, volume_points)
            except OSError or BleakError:
                client = None
                asyncio.ensure_future(connect())
                raise

    logger = Logger()
    logger.attach()
    client: NsBleClient | None = None
    asyncio.ensure_future(connect())

    brightness_points, volume_points, enabled = deserialize_calibration()

    window = make_window()
    tray = make_tray()
    is_new_window = True
    no_refresh_until = {}
    auto_adjust_future = asyncio.ensure_future(asyncio.sleep(0))

    while True:
        await asyncio.sleep(0.01)

        if auto_adjust_future.done() and client is not None:
            auto_adjust_future = asyncio.ensure_future(asyncio.gather(
                auto_adjust_safe(),
                asyncio.sleep(0.5)))

        event, values = read(window, tray, 200)
        update_slider_text(window, values)

        if event in ['debug.apply']:
            try:
                brightness_points, volume_points, enabled = eval(values['debug'])
                assert(list == type(brightness_points) == type(volume_points))
                assert(dict == type(enabled))
                apply_changes()
            except Exception as e:
                sg.PopupError(e)
        if event in ['debug.logs']:
            sg.PopupScrolled(logger.get(), size=(120, 50))

        elif not check_slider_changes(event, values, no_refresh_until):
            refresh_values(window, no_refresh_until)

        if is_new_window:
            is_new_window = False
            apply_changes()

        if event != sg.TIMEOUT_EVENT:
            print(event, values)
            if window is not None:
                if event in [sg.WIN_CLOSED]:
                    window.close()
                    window = None
                if event in ["Calibrate display"] and client is not None:
                    await calibrate(client, brightness_points, None, enabled)
                    apply_changes()
                    show_popup()
                if event in ["Calibrate audio"] and client is not None:
                    await calibrate(client, None, volume_points, enabled)
                    apply_changes()
                    show_popup()
                if event in ["Clear"]:
                    if show_confirmation():
                        brightness_points = []
                        volume_points = []
                        apply_changes()
                if event in values and type(values[event]) == bool:
                    enabled[event] = values[event]
                    apply_changes()
            else:
                if event in ["Configure", sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED]:
                    window = make_window()
                    is_new_window = True
                    continue
            if event in ["Exit"]:
                break

    tray.close()
    if window is not None:
        window.close()


if __name__ == "__main__":
    from singleton import SingleInstance
    me = SingleInstance()
    asyncio.run(run())
