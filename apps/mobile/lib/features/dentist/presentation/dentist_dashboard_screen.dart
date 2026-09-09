import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/sync/offline_sync_engine.dart';
import '../../common/offline_banner.dart';
import 'clinical_notes_screen.dart';
import 'interactive_odontogram_screen.dart';
import 'intraoral_camera_screen.dart';
import 'patient_chart_screen.dart';
import 'treatment_plan_builder_screen.dart';

class DentistDashboardScreen extends StatefulWidget {
  final OfflineSyncEngine syncEngine;
  final ApiClient apiClient;
  final VoidCallback onToggleTheme;

  const DentistDashboardScreen({
    super.key,
    required this.syncEngine,
    required this.apiClient,
    required this.onToggleTheme,
  });

  @override
  State<DentistDashboardScreen> createState() => _DentistDashboardScreenState();
}

class _DentistDashboardScreenState extends State<DentistDashboardScreen> {
  final List<Map<String, dynamic>> _todayAppointments = [
    {
      'id': 'appt-1',
      'time': '09:00 AM',
      'patient_name': 'Aarav Mehta',
      'procedure': 'Root Canal Treatment #16',
      'status': 'IN_CHAIR',
      'patient_id': 'p-1',
      'phone': '+91 98765 43210',
    },
    {
      'id': 'appt-2',
      'time': '10:30 AM',
      'patient_name': 'Riya Kapoor',
      'procedure': 'Crown Preparation #26',
      'status': 'CONFIRMED',
      'patient_id': 'p-2',
      'phone': '+91 98765 43211',
    },
    {
      'id': 'appt-3',
      'time': '11:45 AM',
      'patient_name': 'Arjun Rao',
      'procedure': 'Routine Cleaning & Checkup',
      'status': 'CHECKED_IN',
      'patient_id': 'p-3',
      'phone': '+91 98765 43212',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dentist Station', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.brightness_6),
            onPressed: widget.onToggleTheme,
          ),
          IconButton(
            icon: const Icon(Icons.sync),
            onPressed: () async {
              await widget.syncEngine.pullLatestDelta();
              setState(() {});
            },
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
                // Doctor greeting card
                Card(
                  color: const Color(0xFF0D9488),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Good Morning,', style: TextStyle(color: Colors.white70, fontSize: 14)),
                        const Text('Dr. Neil Shah', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            _buildStatItem('Chair 1', 'Active Operatory'),
                            _buildStatItem('8 Visits', 'Today Scheduled'),
                            _buildStatItem('3 Left', 'Procedures Pending'),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Quick Tools Header
                const Text('Clinical Tools', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildToolCard(
                      icon: Icons.camera_alt_outlined,
                      label: 'Intraoral',
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => IntraoralCameraScreen(apiClient: widget.apiClient)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildToolCard(
                      icon: Icons.grid_view_rounded,
                      label: 'Odontogram',
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => InteractiveOdontogramScreen(
                            patientId: 'p-1',
                            patientName: 'Aarav Mehta',
                            apiClient: widget.apiClient,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildToolCard(
                      icon: Icons.edit_note,
                      label: 'SOAP Note',
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ClinicalNotesScreen(patientId: 'p-1', apiClient: widget.apiClient),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildToolCard(
                      icon: Icons.playlist_add,
                      label: 'Plan Rx',
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => TreatmentPlanBuilderScreen(patientId: 'p-1', apiClient: widget.apiClient),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // Today's Agenda
                const Text("Today's Patient Schedule", style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                ..._todayAppointments.map((appt) => _buildAppointmentCard(appt)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String val, String label) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(val, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ],
    );
  }

  Widget _buildToolCard({required IconData icon, required String label, required VoidCallback onTap}) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: Colors.teal.shade50,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.teal.shade100),
          ),
          child: Column(
            children: [
              Icon(icon, color: const Color(0xFF0D9488), size: 24),
              const SizedBox(height: 6),
              Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF0F172A))),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppointmentCard(Map<String, dynamic> appt) {
    final statusColor = appt['status'] == 'IN_CHAIR'
        ? Colors.teal
        : appt['status'] == 'CHECKED_IN'
            ? Colors.orange
            : Colors.blue;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: statusColor.withOpacity(0.15),
          child: Text(
            appt['time'].split(' ')[0],
            style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
          ),
        ),
        title: Text(appt['patient_name'], style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(appt['procedure'], style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
        trailing: const Icon(Icons.arrow_forward_ios, size: 14),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => PatientChartScreen(
                patientId: appt['patient_id'],
                patientName: appt['patient_name'],
                apiClient: widget.apiClient,
              ),
            ),
          );
        },
      ),
    );
  }
}
