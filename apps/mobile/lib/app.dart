import 'package:flutter/material.dart';
import 'core/api/api_client.dart';
import 'core/auth/biometric_service.dart';
import 'core/notifications/push_notification_service.dart';
import 'core/storage/local_database.dart';
import 'core/storage/secure_storage.dart';
import 'core/sync/offline_sync_engine.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';

class DentalCareApp extends StatefulWidget {
  final SecureStorageService secureStorage;
  final LocalDatabase localDb;
  final ApiClient apiClient;
  final OfflineSyncEngine syncEngine;
  final BiometricService biometricService;
  final PushNotificationService pushService;

  const DentalCareApp({
    super.key,
    required this.secureStorage,
    required this.localDb,
    required this.apiClient,
    required this.syncEngine,
    required this.biometricService,
    required this.pushService,
  });

  @override
  State<DentalCareApp> createState() => _DentalCareAppState();
}

class _DentalCareAppState extends State<DentalCareApp> {
  ThemeMode _themeMode = ThemeMode.system;

  void toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DentalCare Pro',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: _themeMode,
      home: LoginScreen(
        secureStorage: widget.secureStorage,
        apiClient: widget.apiClient,
        biometricService: widget.biometricService,
        syncEngine: widget.syncEngine,
        onToggleTheme: toggleTheme,
      ),
    );
  }
}
