package android.app;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
public class Activity extends Context {
    protected void onCreate(Bundle b) {}
    public void setContentView(View v) {}
    public void onBackPressed() { finish(); }
    public void finish() {}
}
