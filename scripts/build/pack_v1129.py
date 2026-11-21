import zipfile, hashlib, os

SRC_ZIP = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.28_GODplus_20261117.zip'
NEW_VOICE = r'C:/Users/Administrator/Desktop/67-autosave_原音质.ogg'
OUT = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.29_GODplus_20261118.zip'
TARGET = 'DK_Duet/songs/double-kill-miku/Voices.ogg'

new_voice = open(NEW_VOICE, 'rb').read()
new_md5 = hashlib.md5(new_voice).hexdigest()
print('new voice', len(new_voice), new_md5)

zin = zipfile.ZipFile(SRC_ZIP, 'r')
names = zin.namelist()
assert TARGET in names, 'target voice not found in base zip'

n = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename == TARGET:
            zout.writestr(item, new_voice)
        else:
            zout.writestr(item, zin.read(item.filename))
        n += 1
zin.close()

# 验证
z = zipfile.ZipFile(OUT)
bad = z.testzip()
assert bad is None, 'CRC fail: ' + str(bad)
assert len(z.namelist()) == n
voice = z.read(TARGET)
assert hashlib.md5(voice).hexdigest() == new_md5
print('OUT', OUT)
print('items', n, 'size', os.path.getsize(OUT), 'CRC OK', 'md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
print('voice in zip', len(voice), hashlib.md5(voice).hexdigest())
