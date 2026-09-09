import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _storage = FlutterSecureStorage();

  static const _keyAccessToken = 'access_token';
  static const _keyRefreshToken = 'refresh_token';
  static const _keyUserRole = 'user_role';
  static const _keyUserId = 'user_id';
  static const _keyClinicId = 'clinic_id';
  static const _keyBiometricEnabled = 'biometric_enabled';

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required String userRole,
    required String userId,
    String? clinicId,
  }) async {
    await _storage.write(key: _keyAccessToken, value: accessToken);
    await _storage.write(key: _keyRefreshToken, value: refreshToken);
    await _storage.write(key: _keyUserRole, value: userRole);
    await _storage.write(key: _keyUserId, value: userId);
    if (clinicId != null) {
      await _storage.write(key: _keyClinicId, value: clinicId);
    }
  }

  Future<String?> getAccessToken() => _storage.read(key: _keyAccessToken);
  Future<String?> getRefreshToken() => _storage.read(key: _keyRefreshToken);
  Future<String?> getUserRole() => _storage.read(key: _keyUserRole);
  Future<String?> getUserId() => _storage.read(key: _keyUserId);
  Future<String?> getClinicId() => _storage.read(key: _keyClinicId);

  Future<bool> isBiometricEnabled() async {
    final val = await _storage.read(key: _keyBiometricEnabled);
    return val == 'true';
  }

  Future<void> setBiometricEnabled(bool enabled) =>
      _storage.write(key: _keyBiometricEnabled, value: enabled.toString());

  Future<void> clearAll() => _storage.deleteAll();
}
