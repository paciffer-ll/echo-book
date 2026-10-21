package android.webkit;
public class WebChromeClient {
    public WebChromeClient() {}
    // ValueCallback 用 raw（见 ValueCallback 注释），避免泛型 Signature 触发 d8 崩溃
    public boolean onShowFileChooser(WebView webView, ValueCallback filePathCallback, FileChooserParams fileChooserParams) { return false; }
    public static class FileChooserParams {
        public FileChooserParams() {}
    }
}
