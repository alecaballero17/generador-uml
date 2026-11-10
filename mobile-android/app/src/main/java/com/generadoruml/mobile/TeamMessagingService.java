package com.generadoruml.mobile;

import android.app.*;
import android.content.*;
import android.os.Build;
import android.content.pm.PackageManager;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

public class TeamMessagingService extends FirebaseMessagingService {
    public static void createChannel(Context context) {
        NotificationChannel channel = new NotificationChannel("uml_updates", "Actualizaciones del equipo", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("Cambios, acuerdos y respuestas de IA del proyecto");
        channel.enableVibration(true);
        context.getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }
    @Override public void onNewToken(String token) {
        getSharedPreferences("uml_push", MODE_PRIVATE).edit().putString("token", token).apply();
        // The authenticated project screen registers this refreshed token on its next connection.
    }
    @Override public void onMessageReceived(RemoteMessage message) {
        createChannel(this);
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;
        RemoteMessage.Notification data = message.getNotification();
        if (data == null) return;
        Intent open = new Intent(this, MainActivity.class);
        open.putExtra("project", message.getData().get("room"));
        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int id = (message.getData().getOrDefault("room", "uml")).hashCode();
        PendingIntent pending = PendingIntent.getActivity(this, id, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification notice = new Notification.Builder(this, "uml_updates")
            .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(data.getTitle())
            .setContentText(data.getBody()).setAutoCancel(true).setContentIntent(pending).build();
        getSystemService(NotificationManager.class).notify(id, notice);
    }
}
