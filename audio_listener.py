import asyncio


async def is_playing_audio():
    proc = await asyncio.create_subprocess_exec('IsWindowsPlayingSound.exe', stdout=asyncio.subprocess.DEVNULL)
    await proc.communicate()
    result = proc.returncode
    return result == 1


async def main():
    while True:
        print(await is_playing_audio())
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
