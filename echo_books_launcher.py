"""Echo Books 启动器 — iOS PWA 模式
绑定 0.0.0.0 让 iPhone 从局域网访问，自动显示本机 IP 地址。
1. 在电脑上运行这个脚本
2. 在 iPhone Safari 里输入显示的地址
3. Safari → 分享 → 添加到主屏幕 → 变成全屏 App
"""
import http.server, os, subprocess, threading, time, socket, ipaddress

HERE = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)
    def log_message(self, *a): pass
    # SW 需要正确的 MIME type
    def guess_type(self, path):
        t = super().guess_type(path)
        if path.endswith('.js'):
            return 'application/javascript'
        return t

def get_local_ip():
    """获取本机局域网 IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def find_browser():
    for p in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.isfile(p): return p
    return None

def main():
    port = 8888
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{port}/echo-books.html"
    localhost_url = f"http://127.0.0.1:{port}/echo-books.html"

    srv = http.server.HTTPServer(('0.0.0.0', port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║          Echo Books 已启动                       ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  电脑访问: {localhost_url}")
    print(f"║  手机访问: {url}")
    print("║                                                  ║")
    print("║  iPhone 安装步骤:                                ║")
    print("║  1. 确保手机和电脑在同一 WiFi                     ║")
    print(f"║  2. Safari 打开上面的手机地址                     ║")
    print("║  3. 底部分享按钮 → 添加到主屏幕                   ║")
    print("║  4. 桌面出现 Echo Books 图标，点开即全屏 App      ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  按 Ctrl+C 退出                                   ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    exe = find_browser()
    if exe:
        subprocess.Popen([exe, f"--app={localhost_url}", "--window-size=1000,760",
                          "--disable-extensions", "--no-default-browser-check"])

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        srv.shutdown()
        print("\n已退出")

if __name__ == "__main__":
    main()