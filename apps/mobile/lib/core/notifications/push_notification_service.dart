import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../api/api_client.dart';
import '../api/endpoints.dart';

class PushNotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotif = FlutterLocalNotificationsPlugin();
  final ApiClient apiClient;

  PushNotificationService({required this.apiClient});

  Future<void> initialize() async {
    final settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      final token = await _fcm.getToken();
      if (token != null) {
        await _registerDeviceToken(token);
      }
    }

    _fcm.onTokenRefresh.listen((newToken) {
      _registerDeviceToken(newToken);
    });

    const initSettingsAndroid = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettingsIOS = DarwinInitializationSettings();
    const initSettings = InitializationSettings(android: initSettingsAndroid, iOS: initSettingsIOS);
    await _localNotif.initialize(initSettings);

    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _showLocalNotification(message);
    });
  }

  Future<void> _registerDeviceToken(String token) async {
    try {
      await apiClient.dio.post(
        ApiEndpoints.registerDevice,
        data: {
          'device_token': token,
          'device_type': 'ANDROID',
          'device_name': 'Mobile Client',
          'biometric_enabled': true,
        },
      );
    } catch (_) {}
  }

  Future<void> _showLocalNotification(RemoteMessage message) async {
    const androidDetails = AndroidNotificationDetails(
      'dentalcare_channel',
      'Clinical Alerts',
      importance: Importance.max,
      priority: Priority.high,
    );
    const details = NotificationDetails(android: androidDetails);
    await _localNotif.show(
      DateTime.now().millisecond,
      message.notification?.title ?? 'DentalCare Alert',
      message.notification?.body ?? '',
      details,
    );
  }
}
