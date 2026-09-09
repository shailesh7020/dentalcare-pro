import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/sync/offline_sync_engine.dart';
import '../../common/offline_banner.dart';
import 'ai_health_assistant_screen.dart';
import 'appointment_booking_screen.dart';
import 'clinic_chat_screen.dart';
import 'dental_records_screen.dart';
import 'my_invoices_screen.dart';
import 'my_prescriptions_screen.dart';

class PatientHomeScreen extends StatefulWidget {
  final OfflineSyncEngine syncEngine;
  final ApiClient apiClient;

  const PatientHomeScreen({
    super.key,
    required this.syncEngine,
    required this.apiClient,
  });

  @override
  State<PatientHomeScreen> createState() => _PatientHomeScreenState();
}

class _PatientHomeScreenState extends State<PatientHomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Dental Hub', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => ClinicChatScreen(apiClient: widget.apiClient)),
            ),
          ),
        ],
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
                // Next Appointment Countdown Banner
                Card(
                  color: const Color(0xFF0F172A),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('NEXT VISIT', style: TextStyle(color: Colors.tealAccent, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1)),
                            Chip(
                              label: Text('Confirmed', style: TextStyle(color: Colors.white, fontSize: 10)),
                              backgroundColor: Color(0xFF0D9488),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text('Root Canal Review #16', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                        const Text('Tomorrow, 09:00 AM • Dr. Neil Shah', style: TextStyle(color: Colors.white70, fontSize: 13)),
                        const SizedBox(height: 12),
                        ElevatedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.qr_code, size: 16),
                          label: const Text('Show Digital Pass'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0D9488),
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Fast Actions Grid
                Row(
                  children: [
                    _buildPatientAction(
                      icon: Icons.calendar_month,
                      label: 'Book Visit',
                      color: Colors.teal,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => AppointmentBookingScreen(apiClient: widget.apiClient)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildPatientAction(
                      icon: Icons.medication,
                      label: 'Prescriptions',
                      color: Colors.indigo,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => MyPrescriptionsScreen(apiClient: widget.apiClient)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildPatientAction(
                      icon: Icons.receipt_long,
                      label: 'Bills & Pay',
                      color: Colors.amber.shade800,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => MyInvoicesScreen(apiClient: widget.apiClient)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildPatientAction(
                      icon: Icons.folder_shared,
                      label: 'Records & X-rays',
                      color: Colors.blue,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => DentalRecordsScreen(apiClient: widget.apiClient)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // AI Health Assistant Banner
                InkWell(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => AIHealthAssistantScreen(apiClient: widget.apiClient)),
                  ),
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [Colors.teal.shade50, Colors.cyan.shade50]),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.teal.shade200),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.auto_awesome, color: Color(0xFF0D9488), size: 30),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('AI Dental Symptom Guide', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                              Text('Ask questions about oral hygiene, sensitivity & care', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            ],
                          ),
                        ),
                        Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPatientAction({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
          decoration: BoxDecoration(
            color: color.withOpacity(0.08),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: color.withOpacity(0.2)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 12),
              Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }
}
