package com.echo.books;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;

// 顶层类（不要做成 MainActivity 的内部类：内部类会触发 javac 生成匿名合成类 MainActivity$1，
// 其 InnerClasses 的 inner_name 为 null，会让 d8/R8 8.2.2-dev 在写 DEX 时崩溃）。
// ValueCallback 用 raw（见桩类注释）。
public class EchoChromeClient extends WebChromeClient {
    public static final int FILE_REQ = 1001;
    private final Activity activity;
    private ValueCallback fileCallback;

    public EchoChromeClient(Activity activity) {
        this.activity = activity;
    }

    @Override
    public boolean onShowFileChooser(WebView wv, ValueCallback callback, FileChooserParams params) {
        if (fileCallback != null) { fileCallback.onReceiveValue(null); }
        fileCallback = callback;
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        try {
            activity.startActivityForResult(Intent.createChooser(intent, "选择书籍"), FILE_REQ);
        } catch (Exception e) {
            fileCallback = null;
            return false;
        }
        return true;
    }

    public void onFileResult(int resultCode, Intent data) {
        if (fileCallback == null) { return; }
        Uri[] results = null;
        if (resultCode == Activity.RESULT_OK && data != null) {
            String s = data.getDataString();
            if (s != null) { results = new Uri[]{ Uri.parse(s) }; }
        }
        fileCallback.onReceiveValue(results);
        fileCallback = null;
    }
}
