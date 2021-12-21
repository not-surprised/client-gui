call .\venv\Scripts\activate.bat
pyinstaller -w -n !surprised -i logo.ico -y ^
  --add-data logo.ico;. ^
  --add-data monitor_image.png;. ^
  --add-data speaker_image.png;. ^
  --add-data IsWindowsPlayingSound.exe;. ^
  main.py
