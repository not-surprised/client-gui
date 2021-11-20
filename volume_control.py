from ctypes import POINTER, cast
import comtypes
from comtypes import CLSCTX_ALL

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, EDataFlow, ERole


class MyAudioUtilities(AudioUtilities):
    @staticmethod
    def GetSpeaker(id=None):
        device_enumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
        if id is not None:
            speakers = device_enumerator.GetDevice(id)
        else:
            speakers = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
        return speakers


def setVolume(targetVolume, outputDevice):
    devices = MyAudioUtilities.GetSpeakers()

    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(targetVolume/100, None)
    print("volume.GetMasterVolumeLevel(): %s" % volume.GetMasterVolumeLevelScalar())


def getVolume(outputDevice):
    devices = MyAudioUtilities.GetSpeakers()

    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    print("volume.GetMasterVolumeLevel(): %s" % round(volume.GetMasterVolumeLevelScalar()*100))
    return volume.GetMasterVolumeLevelScalar()*100


async def printAllDevices():
    mixer_output = None

    devicelist = MyAudioUtilities.GetAllDevices()

    for device in devicelist:
        if "Speaker" in str(device):
            print(device)

def main():
    mixer_output = None

    devicelist = MyAudioUtilities.GetAllDevices()

    for device in devicelist:
        if "Speakers (Realtek(R) Audio)" in str(device) and "Speaker" in str(device):
            mixer_output = device

    devices = MyAudioUtilities.GetSpeaker(mixer_output.id)
    print(devices)

    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    print("volume.GetMute(): %s" % volume.GetMute())
    print("volume.GetMasterVolumeLevel(): %s" % volume.GetMasterVolumeLevel())
    print("volume.GetVolumeRange(): (%s, %s, %s)" % volume.GetVolumeRange())
    print("volume.SetMasterVolumeLevel()")
    volume.SetMasterVolumeLevelScalar(0.3, None)
    print("volume.GetMasterVolumeLevel(): %s" % volume.GetMasterVolumeLevelScalar())



if __name__ == "__main__":
    #main()
    #setVolume(100, "Speakers (Realtek(R) Audio)")
    getVolume("Speakers (Realtek(R) Audio)")
    #printAllDevices()