# -*- coding: utf-8 -*-
"""从 QT v2.2 (Kade 遗产) 包提取锯子/警告素材，重命名为 DK 前缀，部署三处。

来源：qt_psyched-up-edition_v22_0832a/assets/shared/images/hazard/qt-port/
  * sawkillanimation2.png/xml   -> dk_saw.png/xml   （锯子：idle + 19 moving 帧）
  * attack_alert_NEW.png/xml    -> dk_alert.png/xml （警告：single/double/triple/quad × 6 帧）
  * alert-vignette.png          -> dk_alert_vignette.png
音效 -> <mod>/sounds/hazard/
  sawbladeHit / alert / alertDouble / alertTriple / alertQuadruple / dodge01

帧名规则（engine addAnimationByPrefix 用）：
  锯子：dkSaw_idle  / dkSaw_move0000..0018
  警告：dkAlert_single0000..0005 / dkAlert_double... / dkAlert_triple... / dkAlert_quad...
"""
import os, shutil, hashlib
import xml.etree.ElementTree as ET
from PIL import Image

SRC = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/qt_psyched-up-edition_v22_0832a'
HAZ = os.path.join(SRC, 'assets/shared/images/hazard')
QT_IMG = os.path.join(HAZ, 'qt-port')
QT_SND = os.path.join(SRC, 'assets/shared/sounds/hazard')

GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images'
ROOTS = [
    r'E:/UST_work/dk_miku/DK_Dual/images',
    r'E:/UST_work/dk_miku/DK_Miku/images',
    GAME,
]
SND_ROOTS = [
    r'E:/UST_work/dk_miku/DK_Dual/sounds',
    r'E:/UST_work/dk_miku/DK_Miku/sounds',
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/sounds',
]

OLD_NEW = {
    'kb_attack_animation_kill_idle': 'dkSaw_idle',
    'kb_attack_animation_kill_moving': 'dkSaw_move',
    'kb_attack_animation_alert-single': 'dkAlert_single',
    'kb_attack_animation_alert-double': 'dkAlert_double',
    'kb_attack_animation_alert-triple': 'dkAlert_triple',
    'kb_attack_animation_alert-quad': 'dkAlert_quad',
}


def build_atlas(src_png, src_xml, out_png, out_xml, image_path):
    im = Image.open(src_png).convert('RGBA')
    root = ET.parse(src_xml).getroot()
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<TextureAtlas imagePath="%s">' % image_path]
    n = 0
    for s in root.findall('SubTexture'):
        name = s.get('name', '')
        newname = None
        for old, new in OLD_NEW.items():
            if name.startswith(old):
                suffix = name[len(old):]
                newname = new + suffix
                break
        if not newname:
            continue
        attrs = dict(s.attrib)
        attrs['name'] = newname
        a = ' '.join('%s="%s"' % (k, v) for k, v in attrs.items())
        lines.append('  <SubTexture %s/>' % a)
        n += 1
    lines.append('</TextureAtlas>')
    return '\n'.join(lines), n


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    os.makedirs(GAME, exist_ok=True)
    # 图集 -> 临时生成，再复制到三处
    saw_xml, ns = build_atlas(
        os.path.join(QT_IMG, 'sawkillanimation2.png'),
        os.path.join(QT_IMG, 'sawkillanimation2.xml'),
        'dk_saw.png', 'dk_saw.xml', 'dk_saw.png')
    alert_xml, na = build_atlas(
        os.path.join(QT_IMG, 'attack_alert_NEW.png'),
        os.path.join(QT_IMG, 'attack_alert_NEW.xml'),
        'dk_alert.png', 'dk_alert.xml', 'dk_alert.png')
    print('saw frames=%d  alert frames=%d' % (ns, na))

    # 图集文件映射 (源文件 -> 目标文件名, 或 (内容, 目标文件名))
    atlas_files = [
        (os.path.join(QT_IMG, 'sawkillanimation2.png'), 'dk_saw.png', 'copy'),
        (saw_xml, 'dk_saw.xml', 'text'),
        (os.path.join(QT_IMG, 'attack_alert_NEW.png'), 'dk_alert.png', 'copy'),
        (alert_xml, 'dk_alert.xml', 'text'),
        (os.path.join(HAZ, 'inhuman-port/alert-vignette.png'), 'dk_alert_vignette.png', 'copy'),
    ]
    for rd in ROOTS:
        os.makedirs(rd, exist_ok=True)
        for src, name, kind in atlas_files:
            dst = os.path.join(rd, name)
            if kind == 'copy':
                shutil.copyfile(src, dst)
            else:
                open(dst, 'w', encoding='utf-8').write(src)
            print('  IMG %s  %s' % (md5(dst), dst))

    # 音效
    sounds = ['sawbladeHit.ogg', 'alert.ogg', 'alertDouble.ogg',
              'alertTriple.ogg', 'alertQuadruple.ogg', 'dodge01.ogg']
    for rd in SND_ROOTS:
        os.makedirs(rd, exist_ok=True)
        for s in sounds:
            src = os.path.join(QT_SND, s)
            if not os.path.exists(src):
                print('  WARN missing sound', s)
                continue
            dst = os.path.join(rd, s)
            shutil.copyfile(src, dst)
            print('  SND %s  %s' % (md5(dst), dst))
    print('DONE')


if __name__ == '__main__':
    main()
