package com.generadoruml.mobile;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.util.Log;
import android.webkit.*;
import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;
import androidx.webkit.JavaScriptReplyProxy;
import org.json.JSONObject;
import android.util.Base64;
import java.util.Collections;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MainActivity extends Activity {
    private static final String TAG = "UMLMobile";
    private WebView web;
    private PermissionRequest pendingPermissionReq;
    private ValueCallback<Uri[]> files;
    private byte[] exportBytes;
    private JavaScriptReplyProxy exportReply;
    private void finishExport(String status) {
        if(exportReply!=null)exportReply.postMessage(status);
        exportReply=null;exportBytes=null;
    }

    private boolean local(Uri uri) {
        return uri != null && "https".equals(uri.getScheme()) && "appassets.androidplatform.net".equals(uri.getHost());
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        WebViewAssetLoader.AssetsPathHandler assets = new WebViewAssetLoader.AssetsPathHandler(this);
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/", path -> {
                    String cleanPath = path.isEmpty() ? "index.html" : path;
                    WebResourceResponse res = assets.handle(cleanPath);
                    if (res == null && cleanPath.endsWith(".gz")) {
                        String noGz = cleanPath.substring(0, cleanPath.length() - 3);
                        res = assets.handle(noGz);
                    }
                    return res;
                })
                .build();
        web = new WebView(this);
        setContentView(web);

        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);

        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
                return loader.shouldInterceptRequest(req.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                return !local(req.getUrl());
            }
        });

        ServiceWorkerController.getInstance().setServiceWorkerClient(new ServiceWorkerClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebResourceRequest req) {
                return loader.shouldInterceptRequest(req.getUrl());
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onConsoleMessage(ConsoleMessage cm) {
                Log.i("UMLConsole", cm.message() + " [" + cm.sourceId() + ":" + cm.lineNumber() + "]");
                return true;
            }

            @Override public void onPermissionRequest(PermissionRequest req) {
                runOnUiThread(() -> {
                    Log.i(TAG, "onPermissionRequest origin=" + req.getOrigin() + " resources=" + Arrays.toString(req.getResources()));
                    if (!local(req.getOrigin())) {
                        Log.w(TAG, "Denied permission for non-local origin: " + req.getOrigin());
                        req.deny();
                        return;
                    }
                    List<String> granted = new ArrayList<>();
                    List<String> needed = new ArrayList<>();
                    for (String resource : req.getResources()) {
                        if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) {
                            if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                                granted.add(resource);
                            } else {
                                needed.add(android.Manifest.permission.RECORD_AUDIO);
                            }
                        } else if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                            if (checkSelfPermission(android.Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                                granted.add(resource);
                            } else {
                                needed.add(android.Manifest.permission.CAMERA);
                            }
                        }
                    }

                    if (!needed.isEmpty()) {
                        Log.i(TAG, "Requesting Android runtime permissions: " + needed);
                        if (pendingPermissionReq != null) pendingPermissionReq.deny();
                        pendingPermissionReq = req;
                        requestPermissions(needed.toArray(new String[0]), 41);
                    } else if (!granted.isEmpty()) {
                        Log.i(TAG, "Granting requested resources: " + granted);
                        req.grant(granted.toArray(new String[0]));
                    } else {
                        Log.w(TAG, "No recognizable resources requested, denying");
                        req.deny();
                    }
                });
            }

            @Override public void onPermissionRequestCanceled(PermissionRequest req) {
                if (pendingPermissionReq == req) pendingPermissionReq = null;
            }

            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (files != null) files.onReceiveValue(null);
                files = callback;
                try {
                    startActivityForResult(params.createIntent(), 42);
                } catch (Exception e) {
                    Log.e(TAG, "Failed to start file chooser intent", e);
                    files.onReceiveValue(null);
                    files = null;
                }
                return true;
            }
        });

        if(WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(web,"UMLFiles",Collections.singleton("https://appassets.androidplatform.net"),
                (view,message,origin,mainFrame,reply)->{
                    if(!mainFrame||!local(origin))return;
                    if(exportReply!=null){reply.postMessage("busy");return;}
                    try {
                        String raw=message.getData();
                        if(raw==null||raw.length()>45000000){reply.postMessage("too-large");return;}
                        JSONObject request=new JSONObject(raw);
                        byte[] bytes=Base64.decode(request.getString("data"),Base64.DEFAULT);
                        if(bytes.length>32*1024*1024){reply.postMessage("too-large");return;}
                        String name=request.getString("name").replaceAll("[\\/:*?<>|]","_");
                        String mime=request.optString("type","application/octet-stream");
                        exportBytes=bytes;exportReply=reply;
                        Intent save=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                        save.addCategory(Intent.CATEGORY_OPENABLE);save.setType(mime);
                        save.putExtra(Intent.EXTRA_TITLE,name);
                        startActivityForResult(save,43);
                    } catch(Exception error){if(exportReply!=null)finishExport("error");else reply.postMessage("error");}
                });
        }
        web.loadUrl("https://appassets.androidplatform.net/index.html?view=mobile");
    }

    @Override public void onRequestPermissionsResult(int request, String[] names, int[] grants) {
        super.onRequestPermissionsResult(request, names, grants);
        if (request == 41 && pendingPermissionReq != null) {
            List<String> grantedResources = new ArrayList<>();
            for (int i = 0; i < names.length; i++) {
                if (grants[i] == PackageManager.PERMISSION_GRANTED) {
                    if (android.Manifest.permission.RECORD_AUDIO.equals(names[i])) {
                        grantedResources.add(PermissionRequest.RESOURCE_AUDIO_CAPTURE);
                    }
                    if (android.Manifest.permission.CAMERA.equals(names[i])) {
                        grantedResources.add(PermissionRequest.RESOURCE_VIDEO_CAPTURE);
                    }
                }
            }
            if (!grantedResources.isEmpty()) {
                Log.i(TAG, "Android permissions granted, returning to WebView: " + grantedResources);
                pendingPermissionReq.grant(grantedResources.toArray(new String[0]));
            } else {
                Log.w(TAG, "Android permissions denied by user");
                pendingPermissionReq.deny();
            }
            pendingPermissionReq = null;
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if(request==43 && exportReply!=null) {
            if(result!=RESULT_OK||data==null||data.getData()==null){finishExport("cancelled");return;}
            final Uri destination=data.getData();final byte[] bytes=exportBytes;
            new Thread(()->{
                String status="saved";
                try(OutputStream output=getContentResolver().openOutputStream(destination,"w")) {
                    if(output==null)throw new java.io.IOException();
                    output.write(bytes);
                }catch(Exception error){status="error";}
                final String outcome=status;runOnUiThread(()->finishExport(outcome));
            }).start();
            return;
        }
        if (request == 42 && files != null) {
            files.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result, data));
            files = null;
        }
    }

    @Override protected void onDestroy() {
        if (pendingPermissionReq != null) pendingPermissionReq.deny();
        if (files != null) files.onReceiveValue(null);
        web.destroy();
        super.onDestroy();
    }
}
