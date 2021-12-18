from volume_control import *
from brightness_control import *
from bluetooth_test_client import *


def firstElement(arr):
    return arr[0]

async def getPoints(client):
    return [getBrightnessPoint(client), getVolumePoint(client)]

async def getBrightnessPoint(client):
    currentPCBrightness = getBrightness()
    currentRoomBrightness = await client.get_brightness()

    print(f"Brightness points: {[currentRoomBrightness, currentPCBrightness]}")
    return [currentRoomBrightness, currentPCBrightness]

async def getVolumePoint(client):
    currentPCVolume = getVolume("Speakers (Realtek(R) Audio)")
    currentRoomVolume = await client.get_volume()

    print(f"Volume points: {[currentRoomVolume, currentPCVolume]}")
    return [currentRoomVolume, currentPCVolume]


def add_point(points: list[list[float]], new: list[float]):
    points.append(new)
    points.sort(key=firstElement)


def getSlope(xList, yList):
    intX = 0
    intY = 0
    sumX = 0
    sumY = 0
    for i in xList:
        intX += i

    for i in yList:
        intY += i

    intX /= len(xList)
    intY /= len(yList)

    for i in range(len(xList)):
        sumX += ((xList[i] - intX) * (yList[i] - intY))
        sumY += ((xList[i] - intX) * (xList[i] - intX))

    slope = sumX / sumY
    return slope, intX, intY

def getYint(slope, xa, ya):
    intercept = ya - slope * xa
    return intercept


def interpolate(x, xs, ys):
    n = min(len(xs), len(ys)) - 1
    if x < xs[0]:
        i = 0
    elif xs[n] <= x:
        i = n-1
    else:
        i = 0
        for i in range(n):
            if xs[i] <= x < xs[i+1]:
                break
    x1, y1 = xs[i], ys[i]
    x2, y2 = xs[i+1], ys[i+1]
    slope = (y2 - y1) / (x2 - x1)
    return slope * (x - x1) + y1


def brightness(sensorValue, brightnessPointsFirst, brightnessPointsSecond):
    setBrightnessTo = interpolate(sensorValue, brightnessPointsFirst, brightnessPointsSecond)

    if abs(getBrightness() - setBrightnessTo) > 3:
        if setBrightnessTo < 0:
            setBrightnessTo = 0
        elif setBrightnessTo > 100:
            setBrightnessTo = 100
        print(f"brightness: {sensorValue}, {setBrightnessTo}")
        setBrightness(setBrightnessTo)


def volume(sensorValue, volumePointsFirst, volumePointsSecond):
    setVolumeTo = interpolate(sensorValue, volumePointsFirst, volumePointsSecond)

    if abs(getVolume() - setVolumeTo) > 3:
        if setVolumeTo < 0:
            setVolumeTo = 0
        elif setVolumeTo > 100:
            setVolumeTo = 100
        print(f"volume: {sensorValue}, {setVolumeTo}")
        setVolume(setVolumeTo, "Speakers (Realtek(R) Audio)")

def listOfFirst(arr):
    firstList = []
    for i in range(len(arr)):
        firstList.append(arr[i][0])

    return firstList

def listOfSecond(arr):
    secondList = []
    for i in range(len(arr)):
        secondList.append(arr[i][1])

    return secondList
