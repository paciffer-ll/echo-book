"""
Echo Books APK 构建脚本
编译 Java 桩 → DEX → AXML 编码 → 打包签名对齐 → EchoBooks.apk
"""
import struct, os, zipfile, subprocess, sys, shutil
from pathlib import Path
import xml.etree.ElementTree as ET

APP = Path(__file__).parent
BASE = APP.parent
JDK = BASE / 'jdk'
BT  = BASE / 'bt'
OUT = APP / 'build'
APK_OUT = BASE / 'EchoBooks.apk'

ANDROID_NS = 'http://schemas.android.com/apk/res/android'
FRAMEWORK_ATTRS = {
    'versionCode': 0x0101021b, 'versionName': 0x0101021c,
    'name': 0x01010003, 'label': 0x01010001,
    'allowBackup': 0x01010280, 'exported': 0x01010010,
    'configChanges': 0x010100f1, 'debuggable': 0x0101000f,
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
        d = s.encode('utf-8'); u16 = len(s); u8 = len(d)
        if u8 < 0x80: hdr = struct.pack('BB', u8, u16)
        else: hdr = struct.pack('BBBB', (u8>>8)|0x80, u8&0xFF, (u16>>8)|0x80, u16&0xFF)
        return hdr + d + b'\x00'

    def _pool(self):
        offs, enc, off = [], b'', 0
        for s in self.strings:
            offs.append(off); e = self._enc_str(s); enc += e; off += len(e)
        while len(enc) % 4: enc += b'\x00'
        n = len(self.strings); ss = 0x1C + n*4
        h = struct.pack('<HHIIIIII', 0x0001, 0x1C, ss+len(enc), n, 0, 0x100, 0x1C, 0)
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
        return struct.pack('<HHIIII', 0x0103, 0x10, 24, ln, 0xFFFFFFFF, name)

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
                    nsi = self._s(k.split('}')[0]); lnk = k.split('}')[-1]
                else:
                    nsi = 0xFFFFFFFF; lnk = k
                ani = self._s(lnk)
                if v.lower() in ('true','false'):
                    dt, dv, rv = self.TYPE_INT_BOOLEAN, (-1 if v.lower()=='true' else 0), 0xFFFFFFFF
                elif lnk == 'configChanges':
                    fv = 0
                    for p in v.split('|'): fv |= CONFIG_FLAGS.get(p.strip(), 0)
                    dt, dv, rv = self.TYPE_INT_HEX, fv, 0xFFFFFFFF
                elif lnk == 'versionCode':
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

def main():
    jdk, bt = find_jdk(), find_bt()
    env = {**os.environ, 'JAVA_HOME': str(jdk), 'PATH': f'{jdk/"bin"};{os.environ["PATH"]}'}
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / 'classes').mkdir(parents=True)

    javas = [str(p) for d in ['stubs','src'] for p in (APP/d).rglob('*.java')]
    run([str(jdk/'bin'/'javac.exe'), '--release', '11', '-d', str(OUT/'classes')] + javas, 'Java', env)

    run([str(jdk/'bin'/'jar.exe'), 'cf', str(OUT/'c.jar'), '-C', str(OUT/'classes'), '.'], 'JAR', env)
    run([str(bt/'d8.bat'), '--release', '--output', str(OUT), str(OUT/'c.jar')], 'DEX', env)

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

    ks = OUT / 'debug.keystore'
    if not ks.exists():
        run([str(jdk/'bin'/'keytool.exe'), '-genkeypair', '-alias', 'echokey',
             '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
             '-keystore', str(ks), '-storepass', 'android', '-keypass', 'android',
             '-dname', 'CN=Echo Books,O=Echo,C=US'], 'Keystore', env)
    run([str(jdk/'bin'/'jarsigner.exe'), '-verbose', '-sigalg', 'SHA256withRSA',
         '-digestalg', 'SHA-256', '-keystore', str(ks), '-storepass', 'android',
         '-keypass', 'android', str(unsigned), 'echokey'], 'Sign', env)

    za = bt / 'zipalign.exe'
    r = run([str(za), '-f', '-v', '4', str(unsigned), str(APK_OUT)], 'zipalign', env)
    if not r: shutil.copy(unsigned, APK_OUT); print('zipalign failed, using signed APK')
    print(f'\n=== DONE: {APK_OUT} ({APK_OUT.stat().st_size//1024} KB) ===')

if __name__ == '__main__':
    main()