# Echo Books

沉浸式阅读器 — 支持 EPUB / PDF / PPTX，滑动翻页，Folia 风格动态背景。

## 功能

- 📖 **三种格式**：EPUB（epub.js）、PDF（pdf.js）、PPTX（JSZip 解析）
- 👆 **滑动翻页**：左右滑动切换页面，点击中心切换 UI
- 🎨 **动态背景**：从书籍封面提取主色调，阅读时背景跟随变色（Folia 风格）
- 🌗 **四种风格**：暗色 / 亮色 / 护眼 / 夜间纯黑
- 💡 **亮度调节**：20%-100% 遮罩调光
- 📱 **PWA**：可安装到 iPhone/Android 主屏幕，离线可用
- 📦 **Android APK**：内置 WebView 打包，即装即用
- 🔖 **阅读进度**：IndexedDB 持久化，自动跳回上次位置
- 📋 **目录导航**：章节列表侧滑面板

## 文件结构

```
├── echo-books.html          # 播放器本体（PWA + 三格式 + 滑动 + 亮度 + 4 风格）
├── echo_books_launcher.py   # 桌面启动器（局域网 HTTP + Chrome app 模式）
├── manifest.json            # PWA 清单
├── sw.js                    # Service Worker（离线缓存）
├── EchoBooks.apk            # Android 安装包
├── libs/                    # 依赖库（本地引用，无需 CDN）
│   ├── jszip.min.js         # PPTX 解压
│   ├── epub.min.js         # EPUB 渲染
│   ├── pdf.min.js           # PDF 渲染
│   ├── pdf.worker.min.js   # PDF Worker
│   └── icon-*.png          # PWA 图标
└── android-app/            # Android WebView APK 源码
    ├── AndroidManifest.xml
    ├── build_apk.py         # APK 构建脚本
    ├── stubs/               # Android 框架桩类
    ├── src/                 # MainActivity
    └── assets/www/          # 嵌入的 Web 资源
```

## 使用

### 方式一：浏览器

```bash
python echo_books_launcher.py
```

浏览器自动打开，拖入 EPUB/PDF/PPTX 即可阅读。

### 方式二：iOS 安装为 App

1. 运行启动器，记录显示的手机访问地址
2. iPhone Safari 打开该地址
3. 分享 → 添加到主屏幕 → 全屏独立 App

### 方式三：Android 安装 APK

将 `EchoBooks.apk` 传到手机，允许安装未知来源，点击安装即可。

## 技术

| 组件 | 技术 |
|------|------|
| UI | 纯 HTML/CSS/Canvas，零框架 |
| EPUB | epub.js 0.3.93 |
| PDF | pdf.js 3.11.174 |
| PPTX | JSZip + XML 解析 |
| 存储 | IndexedDB |
| 离线 | Service Worker |
| APK | 手写 AXML 编码器 + d8 + jarsigner |

## License

MIT