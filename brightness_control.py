import screen_brightness_control as sbc

def setBrightness(brightness):
    # current_brightness = sbc.get_brightness(0)
    # sbc.fade_brightness(brightness, start=current_brightness)
    sbc.set_brightness(brightness)

def setBrightness2(brightness, monitor):
    # current_brightness =sbc.get_brightness()
    # monitors = sbc.list_monitors()
    # sbc.set_brightness(brightness, display=monitors[monitor])
    sbc.set_brightness(brightness, monitor)

def getBrightness():
    return sbc.get_brightness(0)

def getBrightness2(monitor):
    return sbc.get_brightness(monitor)

def getMonitors():
    monitors = sbc.list_monitors()
    return monitors

# monitors = getMonitors()
# print(monitors)
# brightness = getBrightness()
# print(brightness)
# setBrightness(brightness - 20)
# # setBrightness2(brightness + 20, 0)