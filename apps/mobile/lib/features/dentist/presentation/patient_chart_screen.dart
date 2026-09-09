import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import 'clinical_notes_screen.dart';
import 'interactive_odontogram_screen.dart';
import 'intraoral_camera_screen.dart';
import 'treatment_plan_builder_screen.dart';

class PatientChartScreen extends StatelessWidget {
  final String patientId;
  final String patientName;
  final ApiClient apiClient;

  const PatientChartScreen({
    super.key,
    required this.patientId,
    required this.patientName,
    required this.apiClient,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(patientName),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Medical Alerts Banner
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.red.shade200),
            ),
            child: const Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.red),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Medical Alerts', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 13)),
                      Text('Penicillin Allergy • Hypertensive (Stage 1)', style: TextStyle(fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Demographics card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(patientName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const Chip(
                        label: Text('Adult Dentition', style: TextStyle(fontSize: 11)),
                        backgroundColor: Color(0xFFF1F5F9),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text('Age: 32 • Gender: Male • Blood Group: O+', style: TextStyle(color: Colors.grey, fontSize: 13)),
                  const Text('Emergency Contact: Sunita Mehta (+91 98765 00000)', style: TextStyle(color: Colors.grey, fontSize: 13)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Action navigation buttons
          ElevatedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => InteractiveOdontogramScreen(
                  patientId: patientId,
                  patientName: patientName,
                  apiClient: apiClient,
                ),
              ),
            ),
            icon: const Icon(Icons.grid_on),
            label: const Text('Open Interactive Odontogram'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ClinicalNotesScreen(patientId: patientId, apiClient: apiClient),
              ),
            ),
            icon: const Icon(Icons.description_outlined),
            label: const Text('Record Clinical SOAP Notes'),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => TreatmentPlanBuilderScreen(patientId: patientId, apiClient: apiClient),
              ),
            ),
            icon: const Icon(Icons.medical_services_outlined),
            label: const Text('Create Treatment Plan'),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => IntraoralCameraScreen(apiClient: apiClient),
              ),
            ),
            icon: const Icon(Icons.camera_alt_outlined),
            label: const Text('Capture Intraoral Photos'),
          ),
        ],
      ),
    );
  }
}
