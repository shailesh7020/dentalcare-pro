import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'app.dart';
import 'core/api/api_client.dart';
import 'core/auth/biometric_service.dart';
import 'core/notifications/push_notification_service.dart';
import 'core/storage/local_database.dart';
import 'core/storage/secure_storage.dart';
import 'core/sync/offline_sync_engine.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final secureStorage = SecureStorageService();
  final savedServerUrl = await secureStorage.getServerUrl();
  final localDb = LocalDatabase();
  final apiClient = ApiClient(secureStorage: secureStorage, initialBaseUrl: savedServerUrl);
  final syncEngine = OfflineSyncEngine(apiClient: apiClient, localDb: localDb);
  final biometricService = BiometricService();
  final pushService = PushNotificationService(apiClient: apiClient);

  runApp(
    DentalCareApp(
      secureStorage: secureStorage,
      localDb: localDb,
      apiClient: apiClient,
      syncEngine: syncEngine,
      biometricService: biometricService,
      pushService: pushService,
    ),
  );
}
