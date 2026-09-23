import 'package:dio/dio.dart';
import '../storage/secure_storage.dart';
import 'endpoints.dart';

class ApiClient {
  late final Dio dio;
  final SecureStorageService secureStorage;

  ApiClient({required this.secureStorage, String? initialBaseUrl}) {
    final effectiveBaseUrl = initialBaseUrl ?? ApiEndpoints.baseUrl;
    dio = Dio(
      BaseOptions(
        baseUrl: effectiveBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await secureStorage.getAccessToken();
          if (token != null && !options.headers.containsKey('Authorization')) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          if (error.response?.statusCode == 401) {
            final refreshed = await _attemptTokenRefresh();
            if (refreshed) {
              final token = await secureStorage.getAccessToken();
              error.requestOptions.headers['Authorization'] = 'Bearer $token';
              final retryResponse = await dio.fetch(error.requestOptions);
              return handler.resolve(retryResponse);
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  void setBaseUrl(String url) {
    final cleanUrl = url.trim().endsWith('/') ? url.trim().substring(0, url.trim().length - 1) : url.trim();
    dio.options.baseUrl = cleanUrl;
  }

  String get baseUrl => dio.options.baseUrl;

  Future<bool> _attemptTokenRefresh() async {
    try {
      final refreshToken = await secureStorage.getRefreshToken();
      if (refreshToken == null) return false;

      final response = await Dio().post(
        '${dio.options.baseUrl}${ApiEndpoints.refresh}',
        data: {'refresh_token': refreshToken},
      );

      if (response.statusCode == 200) {
        final newAccessToken = response.data['access_token'];
        final newRefreshToken = response.data['refresh_token'] ?? refreshToken;
        final role = await secureStorage.getUserRole() ?? 'DENTIST';
        final userId = await secureStorage.getUserId() ?? '';
        final clinicId = await secureStorage.getClinicId();

        await secureStorage.saveTokens(
          accessToken: newAccessToken,
          refreshToken: newRefreshToken,
          userRole: role,
          userId: userId,
          clinicId: clinicId,
        );
        return true;
      }
    } catch (_) {
      await secureStorage.clearAll();
    }
    return false;
  }
}
