class ApiEndpoints {
  static const String baseUrl = 'https://api.dentalcarepro.local/api/v1';

  // Auth
  static const String login = '/auth/login';
  static const String refresh = '/auth/refresh';
  static const String logout = '/auth/logout';
  static const String me = '/users/me';

  // Mobile Core
  static const String registerDevice = '/mobile/devices/register';
  static const String unregisterDevice = '/mobile/devices';
  static const String syncPull = '/mobile/sync/pull';
  static const String syncPush = '/mobile/sync/push';
  static const String digitalSignatures = '/mobile/signatures';
  static const String clinicalMedia = '/mobile/media/upload';
  static const String patientMedia = '/mobile/media/patient';
  static const String aiAssist = '/mobile/ai/assist';

  // Clinical & Practice
  static const String appointments = '/appointments';
  static const String patients = '/patients';
  static const String odontogram = '/odontogram';
  static const String treatments = '/treatments';
  static const String prescriptions = '/prescriptions';
  static const String billing = '/billing';
  static const String portal = '/portal';
}
