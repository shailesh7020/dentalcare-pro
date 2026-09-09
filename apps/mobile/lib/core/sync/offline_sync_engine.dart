import 'dart:convert';
import 'package:dio/dio.dart';
import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../storage/local_database.dart';

class OfflineSyncEngine {
  final ApiClient apiClient;
  final LocalDatabase localDb;
  bool _isSyncing = false;

  OfflineSyncEngine({required this.apiClient, required this.localDb});

  bool get isSyncing => _isSyncing;

  Future<int> processPendingMutations() async {
    if (_isSyncing) return 0;
    _isSyncing = true;

    try {
      final pending = await localDb.getPendingMutations();
      if (pending.isEmpty) return 0;

      final mutationList = pending.map((m) {
        return {
          'client_mutation_id': m['mutation_id'],
          'entity_type': m['entity_type'],
          'action': m['action'],
          'entity_id': m['entity_id'],
          'client_timestamp': m['created_at'],
          'payload': jsonDecode(m['payload_json'] as String),
        };
      }).toList();

      final response = await apiClient.dio.post(
        ApiEndpoints.syncPush,
        data: {'mutations': mutationList},
      );

      if (response.statusCode == 200) {
        for (final m in pending) {
          await localDb.removeMutation(m['mutation_id'] as String);
        }
        return mutationList.length;
      }
    } catch (_) {
      // Offline or network glitch; leave in queue
    } finally {
      _isSyncing = false;
    }
    return 0;
  }

  Future<bool> pullLatestDelta({String? sinceTimestamp}) async {
    try {
      final response = await apiClient.dio.get(
        ApiEndpoints.syncPull,
        queryParameters: sinceTimestamp != null ? {'since': sinceTimestamp} : null,
      );

      if (response.statusCode == 200) {
        final data = response.data;
        // Cache appointments
        for (final appt in data['appointments'] ?? []) {
          await localDb.cacheEntity(appt['id'], 'APPOINTMENT', appt);
        }
        // Cache patients
        for (final pat in data['patients'] ?? []) {
          await localDb.cacheEntity(pat['id'], 'PATIENT', pat);
        }
        // Cache treatments
        for (final trt in data['treatments'] ?? []) {
          await localDb.cacheEntity(trt['id'], 'TREATMENT', trt);
        }
        return true;
      }
    } catch (_) {
      // Return false if offline
    }
    return false;
  }
}
