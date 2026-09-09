import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class MyPrescriptionsScreen extends StatelessWidget {
  final ApiClient apiClient;

  const MyPrescriptionsScreen({super.key, required this.apiClient});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Prescriptions')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildRxCard(
            context,
            date: '02 Sep 2026',
            doctor: 'Dr. Neil Shah',
            meds: [
              'Amoxicillin 500mg • 1 capsule 3x daily (5 days)',
              'Ibuprofen 400mg • 1 tablet as needed for pain',
              'Chlorhexidine 0.2% • Mouthwash 2x daily (7 days)',
            ],
          ),
          const SizedBox(height: 12),
          _buildRxCard(
            context,
            date: '14 May 2026',
            doctor: 'Dr. Maya Iyer',
            meds: [
              'Paracetamol 650mg • 1 tablet after meals',
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRxCard(BuildContext context, {required String date, required String doctor, required List<String> meds}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(date, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(doctor, style: const TextStyle(color: Colors.grey, fontSize: 13)),
              ],
            ),
            const Divider(height: 20),
            ...meds.map((m) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      const Icon(Icons.circle, size: 6, color: Color(0xFF0D9488)),
                      const SizedBox(width: 8),
                      Expanded(child: Text(m, style: const TextStyle(fontSize: 13))),
                    ],
                  ),
                )),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Downloading prescription PDF...')),
                  );
                },
                icon: const Icon(Icons.picture_as_pdf, size: 16),
                label: const Text('Download PDF'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
