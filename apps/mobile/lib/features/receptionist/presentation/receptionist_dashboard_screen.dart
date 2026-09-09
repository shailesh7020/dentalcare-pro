import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/sync/offline_sync_engine.dart';
import '../../common/offline_banner.dart';
import 'fast_patient_registration_screen.dart';
import 'mobile_billing_screen.dart';
import 'qr_checkin_scanner_screen.dart';

class ReceptionistDashboardScreen extends StatefulWidget {
  final OfflineSyncEngine syncEngine;
  final ApiClient apiClient;

  const ReceptionistDashboardScreen({
    super.key,
    required this.syncEngine,
    required this.apiClient,
  });

  @override
  State<ReceptionistDashboardScreen> createState() => _ReceptionistDashboardScreenState();
}

class _ReceptionistDashboardScreenState extends State<ReceptionistDashboardScreen> {
  final List<Map<String, dynamic>> _waitingQueue = [
    {'name': 'Vikram Seth', 'doctor': 'Dr. N. Shah', 'status': 'WAITING', 'time': '10 mins'},
    {'name': 'Pooja Iyer', 'doctor': 'Dr. M. Iyer', 'status': 'IN_TRIAGE', 'time': '4 mins'},
    {'name': 'Ankit Verma', 'doctor': 'Dr. N. Shah', 'status': 'WAITING', 'time': 'Just arrived'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Front Desk Reception', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          OfflineBanner(
            syncEngine: widget.syncEngine,
            onSyncComplete: () => setState(() {}),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Quick Front Desk Actions
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => QRCheckinScannerScreen(apiClient: widget.apiClient)),
                        ),
                        icon: const Icon(Icons.qr_code_scanner),
                        label: const Text('QR Check-In'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF0D9488),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => FastPatientRegistrationScreen(apiClient: widget.apiClient)),
                        ),
                        icon: const Icon(Icons.person_add_alt),
                        label: const Text('Add Patient'),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // Reception Stats Grid
                Row(
                  children: [
                    _buildDeskStat('18', 'Total Today', Colors.blue),
                    const SizedBox(width: 10),
                    _buildDeskStat('3', 'In Waiting', Colors.orange),
                    const SizedBox(width: 10),
                    _buildDeskStat('12', 'Completed', Colors.green),
                  ],
                ),
                const SizedBox(height: 24),

                // Waiting Queue
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Live Waiting Room Queue', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    Text('${_waitingQueue.length} Patients', style: const TextStyle(color: Colors.grey, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 12),
                ..._waitingQueue.map((patient) {
                  return Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: const CircleAvatar(
                        backgroundColor: Color(0xFFE2E8F0),
                        child: Icon(Icons.person, color: Color(0xFF475569)),
                      ),
                      title: Text(patient['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('${patient['doctor']} • Waiting ${patient['time']}'),
                      trailing: IconButton(
                        icon: const Icon(Icons.receipt_long, color: Color(0xFF0D9488)),
                        tooltip: 'Collect Payment / Invoice',
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => MobileBillingScreen(patientName: patient['name'], apiClient: widget.apiClient),
                          ),
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDeskStat(String count, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(count, style: TextStyle(color: color, fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.black87)),
          ],
        ),
      ),
    );
  }
}
