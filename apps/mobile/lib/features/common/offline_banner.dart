import 'package:flutter/material.dart';
import '../../core/sync/offline_sync_engine.dart';

class OfflineBanner extends StatelessWidget {
  final OfflineSyncEngine syncEngine;
  final VoidCallback onSyncComplete;

  const OfflineBanner({
    super.key,
    required this.syncEngine,
    required this.onSyncComplete,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.amber.shade700,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.cloud_off, color: Colors.white, size: 20),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Offline Mode – changes queued locally',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
            ),
          ),
          TextButton(
            onPressed: () async {
              await syncEngine.processPendingMutations();
              onSyncComplete();
            },
            style: TextButton.styleFrom(
              backgroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            ),
            child: const Text('Sync', style: TextStyle(color: Colors.amber, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
