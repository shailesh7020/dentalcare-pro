import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../common/signature_pad_dialog.dart';

class DentalRecordsScreen extends StatefulWidget {
  final ApiClient apiClient;

  const DentalRecordsScreen({super.key, required this.apiClient});

  @override
  State<DentalRecordsScreen> createState() => _DentalRecordsScreenState();
}

class _DentalRecordsScreenState extends State<DentalRecordsScreen> {
  bool _consentSigned = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Records & Consent Vault')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Pending Consent Form Card
          Card(
            color: Colors.amber.shade50,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.amber.shade300),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Consent Required', style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text('Endodontic Root Canal Therapy Consent Form', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  const Text('Please review and provide your digital signature prior to treatment.', style: TextStyle(fontSize: 12)),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: _consentSigned
                        ? null
                        : () {
                            showDialog(
                              context: context,
                              builder: (_) => SignaturePadDialog(
                                title: 'Patient Informed Consent',
                                signerRole: 'Patient / Guardian',
                                onSave: (sig) {
                                  setState(() => _consentSigned = true);
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Consent form signed digitally!')),
                                  );
                                },
                              ),
                            );
                          },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.amber.shade800,
                      foregroundColor: Colors.white,
                    ),
                    child: Text(_consentSigned ? 'Consent Signed' : 'Sign Consent Form'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          const Text('Clinical Images & Diagnostic X-Rays', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            children: [
              _buildImageCard('Panoramic OPG', '14 May 2026'),
              _buildImageCard('Periapical #16', '02 Sep 2026'),
              _buildImageCard('Bitewing Left', '14 May 2026'),
              _buildImageCard('Intraoral #26', '02 Sep 2026'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildImageCard(String title, String date) {
    return Card(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.image, size: 40, color: Colors.teal),
          const SizedBox(height: 8),
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          Text(date, style: const TextStyle(color: Colors.grey, fontSize: 11)),
        ],
      ),
    );
  }
}
