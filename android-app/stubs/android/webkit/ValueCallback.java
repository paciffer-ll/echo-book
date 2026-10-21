package android.webkit;
// 注意：故意用非泛型(raw)桩。真机框架的 ValueCallback<T> 会在运行时覆盖它，
// 方法重写按描述符(erasure)匹配，raw 不影响重写成立；
// 且避免 javac 生成泛型 Signature 属性触发 d8/R8 8.2.2-dev 的内部崩溃。
public interface ValueCallback {
    void onReceiveValue(Object value);
}
