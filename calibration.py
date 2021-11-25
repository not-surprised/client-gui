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

async def brightness(client, brightnessPointsFirst, brightnessPointsSecond):
    sensorValue = await client.get_brightness()

    slope, xa, ya = getSlope(brightnessPointsFirst, brightnessPointsSecond)
    setBrightnessTo = slope * sensorValue + getYint(slope, xa, ya)

    if abs(getBrightness() - setBrightnessTo) > 3:
        if setBrightnessTo < 0:
            setBrightnessTo = 0
        elif setBrightnessTo > 100:
            setBrightnessTo = 100
        print(f"brightness: {sensorValue}, {setBrightnessTo}")
        setBrightness(setBrightnessTo)


async def volume(client, volumePointsFirst, volumePointsSecond):
    sensorValue = await client.get_volume()

    slope, xa, ya = getSlope(volumePointsFirst, volumePointsSecond)
    setVolumeTo = slope * sensorValue + getYint(slope, xa, ya)

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

async def main():
    client = NsBleClient()
    await client.discover_and_connect()


    brightnessPoints = [] #[[1, 2], [3, 4]]
    volumePoints = [] #[[2,3], [3, 5]]
    numberOfPoints = 2

    for i in range(numberOfPoints):
        flag = 0
        while flag != 'Y':
            flag = input("Are you ready to collect a point? (Y/N)")
        brightnessPoints.append(await getBrightnessPoint(client))
        volumePoints.append(await getVolumePoint(client))

    brightnessPoints.sort(key=firstElement)
    volumePoints.sort(key=firstElement)

    brightnessPointsFirst = listOfFirst(brightnessPoints)
    brightnessPointsSecond = listOfSecond(brightnessPoints)

    volumePointsFirst = listOfFirst(volumePoints)
    volumePointsSecond = listOfSecond(volumePoints)

    while True:
        await brightness(client, brightnessPointsFirst, brightnessPointsSecond)
        await asyncio.sleep(1)
        await volume(client, volumePointsFirst, volumePointsSecond)
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())