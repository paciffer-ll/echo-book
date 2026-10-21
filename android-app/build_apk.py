"""
Echo Books APK 构建脚本
编译 Java 桩 → DEX → AXML 编码 → 打包签名对齐 → EchoBooks.apk
"""
import struct, os, zipfile, subprocess, sys, shutil, re
from pathlib import Path
import xml.etree.ElementTree as ET

APP = Path(__file__).parent
BASE = APP.parent
JDK = BASE / 'jdk'
BT  = BASE / 'bt'
OUT = APP / 'build'
APK_OUT = BASE / 'EchoBooks.apk'
WWW = APP / 'assets' / 'www'
# 需要从根目录同步进 APK 的单文件资源
SYNC_FILES = ['echo-books.html', 'manifest.json', 'sw.js']

ANDROID_NS = 'http://schemas.android.com/apk/res/android'
FRAMEWORK_ATTRS = {
    'versionCode': 0x0101021b, 'versionName': 0x0101021c,
    'name': 0x01010003, 'label': 0x01010001,
    'allowBackup': 0x01010280, 'exported': 0x01010010,
    'configChanges': 0x010100f1, 'debuggable': 0x0101000f,
    'minSdkVersion': 0x0101020c, 'targetSdkVersion': 0x01010270,
    'maxSdkVersion': 0x01010271,
}
CONFIG_FLAGS = {'orientation': 0x0010, 'screenSize': 0x0400, 'keyboardHidden': 0x0020}

class AxmlWriter:
    TYPE_STRING = 0x03
    TYPE_INT_DEC = 0x10
    TYPE_INT_HEX = 0x11
    TYPE_INT_BOOLEAN = 0x12

    def __init__(self):
        self.strings, self.si = [], {}
        self.chunks = []

    def _s(self, s):
        if s not in self.si: self.si[s] = len(self.strings); self.strings.append(s)
        return self.si[s]

    def _enc_str(self, s):
        d = s.encode('utf-8'); charSize = len(s); byteSize = len(d)
        def enc16(v):
            if v < 0x80: return struct.pack('B', v)
            return struct.pack('BB', ((v >> 8) | 0x80), v & 0xFF)
        # Android UTF-8 字符串池条目：charSize 在前、byteSize 在后，各自变长编码
        return enc16(charSize) + enc16(byteSize) + d + b'\x00'

    def _pool(self):
        offs, enc, off = [], b'', 0
        for s in self.strings:
            offs.append(off); e = self._enc_str(s); enc += e; off += len(e)
        while len(enc) % 4: enc += b'\x00'
        n = len(self.strings)
        stringsStart = 0x1C + n*4          # 头部 + 偏移数组之后才是字符串数据
        size = stringsStart + len(enc)
        h = struct.pack('<HHIIIIII', 0x0001, 0x1C, size, n, 0, 0x100, stringsStart, 0)
        return h + b''.join(struct.pack('<I', o) for o in offs) + enc

    def _rmap(self):
        ids = [FRAMEWORK_ATTRS.get(s, 0) for s in self.strings]
        sz = 8 + len(ids)*4
        return struct.pack('<HHI', 0x0180, 8, sz) + b''.join(struct.pack('<I', i) for i in ids)

    def _ns_start(self, p, u, ln):
        return struct.pack('<HHIIIII', 0x0100, 0x10, 24, ln, 0xFFFFFFFF, p, u)
    def _ns_end(self, p, u, ln):
        return struct.pack('<HHIIIII', 0x0101, 0x10, 24, ln, 0xFFFFFFFF, p, u)

    def _start(self, name, attrs, ln):
        body = b''
        for ns, nm, rv, dt, dv in attrs:
            body += struct.pack('<IIIHBBi', ns, nm, rv, 8, 0, dt, dv)
        ac = len(attrs)
        total = 16 + 20 + ac*20
        h = struct.pack('<HHI', 0x0102, 0x10, total) + struct.pack('<II', ln, 0xFFFFFFFF)
        b = struct.pack('<IIHHHHHH', 0xFFFFFFFF, name, 0x14, 0x14, ac, 0, 0, 0)
        return h + b + body

    def _end(self, name, ln):
        # 结束元素：节点头(16) + ns(4) + name(4) = 24 字节
        return struct.pack('<HHIIIII', 0x0103, 0x10, 24, ln, 0xFFFFFFFF, 0xFFFFFFFF, name)

    def encode(self, xml_path):
        root = ET.parse(xml_path).getroot()
        pi, ui = self._s('android'), self._s(ANDROID_NS)
        ln = 1
        self.chunks.append(self._ns_start(pi, ui, ln))
        def proc(el):
            nonlocal ln
            tag = el.tag.split('}')[-1]
            ni = self._s(tag)
            attrs = []
            for k, v in el.attrib.items():
                if '}' in k:
                    nsi = self._s(k.split('}')[0][1:]); lnk = k.split('}')[-1]
                else:
                    nsi = 0xFFFFFFFF; lnk = k
                ani = self._s(lnk)
                if v.lower() in ('true','false'):
                    dt, dv, rv = self.TYPE_INT_BOOLEAN, (-1 if v.lower()=='true' else 0), 0xFFFFFFFF
                elif lnk == 'configChanges':
                    fv = 0
                    for p in v.split('|'): fv |= CONFIG_FLAGS.get(p.strip(), 0)
                    dt, dv, rv = self.TYPE_INT_HEX, fv, 0xFFFFFFFF
                elif lnk in ('versionCode','minSdkVersion','targetSdkVersion','maxSdkVersion'):
                    dt, dv, rv = self.TYPE_INT_DEC, int(v), 0xFFFFFFFF
                else:
                    vi = self._s(v); dt, dv, rv = self.TYPE_STRING, vi, vi
                attrs.append((nsi, ani, rv, dt, dv))
            self.chunks.append(self._start(ni, attrs, ln)); ln += 1
            for c in el: proc(c)
            self.chunks.append(self._end(ni, ln)); ln += 1
        proc(root)
        self.chunks.append(self._ns_end(pi, ui, ln))
        body = self._pool() + self._rmap() + b''.join(self.chunks)
        return struct.pack('<HHI', 0x0003, 8, 8+len(body)) + body

def run(cmd, desc, env=None):
    print(f'\n=== {desc} ===')
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.stdout: print(r.stdout[:800])
    if r.stderr: print(r.stderr[:800])
    print(f'Exit: {r.returncode}')
    return r.returncode == 0

def find_jdk():
    for d in JDK.iterdir():
        if (d / 'bin' / 'javac.exe').exists(): return d
    sys.exit('JDK not found')

def find_bt():
    for d in BT.iterdir():
        if (d / 'aapt2.exe').exists(): return d
    sys.exit('build-tools not found')

def sync_assets():
    """把根目录最新的 Web 资源同步进 APK 资产目录，避免打进旧副本"""
    WWW.mkdir(parents=True, exist_ok=True)
    for name in SYNC_FILES:
        src = BASE / name
        if src.exists():
            shutil.copy2(src, WWW / name)
            print(f'[sync] {name} ({src.stat().st_size} bytes) -> assets/www/')
        else:
            print(f'[sync] 警告：根目录缺少 {name}，跳过')
    src_libs = BASE / 'libs'
    dst_libs = WWW / 'libs'
    if src_libs.exists():
        dst_libs.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in src_libs.rglob('*'):
            if f.is_file():
                rel = f.relative_to(src_libs)
                target = dst_libs / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target); n += 1
        print(f'[sync] libs/ -> assets/www/libs/ （{n} 个文件）')
    else:
        print('[sync] 警告：根目录缺少 libs/，跳过')

def bump_version():
    """自动递增 AndroidManifest.xml 的 versionCode，让每次构建都能被识别为新版（可覆盖升级）"""
    mf = APP / 'AndroidManifest.xml'
    text = mf.read_text(encoding='utf-8')
    m = re.search(r'android:versionCode="(\d+)"', text)
    if not m:
        print('[version] 警告：未找到 android:versionCode，跳过递增'); return
    old = int(m.group(1)); new = old + 1
    text = text.replace(f'android:versionCode="{old}"', f'android:versionCode="{new}"', 1)
    mf.write_text(text, encoding='utf-8')
    print(f'[version] versionCode {old} -> {new}')

def main():
    jdk, bt = find_jdk(), find_bt()
    env = {**os.environ, 'JAVA_HOME': str(jdk), 'PATH': f'{jdk/"bin"};{os.environ["PATH"]}'}
    # 每次构建前先同步最新资源并递增版本号
    sync_assets()
    bump_version()
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / 'classes').mkdir(parents=True)

    javas = [str(p) for d in ['stubs','src'] for p in (APP/d).rglob('*.java')]
    run([str(jdk/'bin'/'javac.exe'), '--release', '11', '-d', str(OUT/'classes')] + javas, 'Java', env)

    run([str(jdk/'bin'/'jar.exe'), 'cf', str(OUT/'c.jar'), '-C', str(OUT/'classes'), '.'], 'JAR', env)
    run([str(bt/'d8.bat'), '--release', '--output', str(OUT), str(OUT/'c.jar')], 'DEX', env)
    if not (OUT / 'classes.dex').exists():
        sys.exit('DEX 生成失败，终止构建（不会产出坏 APK）')

    axml = AxmlWriter().encode(APP / 'AndroidManifest.xml')
    (OUT / 'AndroidManifest.xml').write_bytes(axml)
    print(f'AXML: {len(axml)} bytes')

    unsigned = OUT / 'unsigned.apk'
    with zipfile.ZipFile(unsigned, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / 'AndroidManifest.xml', 'AndroidManifest.xml')
        if (OUT / 'classes.dex').exists():
            zf.write(OUT / 'classes.dex', 'classes.dex')
        assets = APP / 'assets'
        if assets.exists():
            for f in assets.rglob('*'):
                if f.is_file(): zf.write(f, str(f.relative_to(APP)))
    print(f'APK: {unsigned.stat().st_size} bytes')

    # 密钥库固定保存在 android-app/ 下，不随 build 目录清空，保证以后能覆盖升级
    ks = APP / 'echo.keystore'
    if not ks.exists():
        run([str(jdk/'bin'/'keytool.exe'), '-genkeypair', '-alias', 'echokey',
             '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
             '-keystore', str(ks), '-storepass', 'android', '-keypass', 'android',
             '-dname', 'CN=Echo Books,O=Echo,C=US'], 'Keystore', env)

    # 先 zipalign 对齐，再用 apksigner 做 v1+v2+v3 签名（现代安卓要求 v2+，仅 v1 会装不上）
    za = bt / 'zipalign.exe'
    aligned = OUT / 'aligned.apk'
    if not run([str(za), '-f', '-p', '4', str(unsigned), str(aligned)], 'zipalign', env):
        shutil.copy(unsigned, aligned)

    aps = bt / 'apksigner.bat'
    ok = run([str(aps), 'sign',
              '--ks', str(ks), '--ks-key-alias', 'echokey',
              '--ks-pass', 'pass:android', '--key-pass', 'pass:android',
              '--v1-signing-enabled', 'true',
              '--v2-signing-enabled', 'true',
              '--v3-signing-enabled', 'true',
              '--out', str(APK_OUT), str(aligned)], 'apksigner sign', env)
    if not ok or not APK_OUT.exists():
        sys.exit('apksigner 签名失败，终止构建（不会产出坏 APK）')
    print(f'\n=== DONE: {APK_OUT} ({APK_OUT.stat().st_size//1024} KB) ===')

if __name__ == '__main__':
    main()