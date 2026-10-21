package android.webkit;
import android.content.Context;
import android.view.View;
public class WebView extends View {
    public WebView(Context c) { super(c); }
    public WebSettings getSettings() { return new WebSettings(); }
    public void setWebViewClient(WebViewClient c) {}
    public void setWebChromeClient(WebChromeClient c) {}
    public void loadUrl(String url) {}
    public boolean canGoBack() { return false; }
    public void goBack() {}
    public void addJavascriptInterface(Object o, String name) {}
}
