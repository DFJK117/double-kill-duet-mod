# -*- coding: utf-8 -*-
import zipfile
z = zipfile.ZipFile('I:/mods.zip')
for n in z.namelist():
    low = n.lower()
    if low.endswith(('.ogg', '.wav', '.mp3')) and ('saw' in low or 'alert' in low or 'attack' in low or 'dodge' in low or 'preload' in low):
        print(n, z.getinfo(n).file_size)
