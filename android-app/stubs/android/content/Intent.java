package android.content;
import android.net.Uri;
public class Intent {
    public static final String ACTION_GET_CONTENT = "android.intent.action.GET_CONTENT";
    public static final String CATEGORY_OPENABLE = "android.intent.category.OPENABLE";
    public Intent() {}
    public Intent(String action) {}
    public Intent setType(String type) { return this; }
    public Intent addCategory(String category) { return this; }
    public Uri getData() { return null; }
    public String getDataString() { return null; }
    public static Intent createChooser(Intent target, CharSequence title) { return new Intent(); }
}
