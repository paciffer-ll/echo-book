package android.app;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
public class Activity extends Context {
    public static final int RESULT_OK = -1;
    protected void onCreate(Bundle b) {}
    public void setContentView(View v) {}
    public void onBackPressed() { finish(); }
    public void finish() {}
    public void runOnUiThread(Runnable r) { r.run(); }
    public void startActivityForResult(Intent intent, int requestCode) {}
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {}
}
