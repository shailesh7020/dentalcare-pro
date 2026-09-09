import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class QRCheckinScannerScreen extends StatefulWidget {
  final ApiClient apiClient;

  const QRCheckinScannerScreen({super.key, required this.apiClient});

  @override
  State<QRCheckinScannerScreen> createState() => _QRCheckinScannerScreenState();
}

class _QRCheckinScannerScreenState extends State<QRCheckinScannerScreen> {
  bool _scanned = false;
  String? _patientFound;

  void _simulateScan() {
    setState(() {
      _scanned = true;
      _patientFound = 'Riya Kapoor (ID: PAT-9042)';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Patient QR Scanner')),
      body: Column(
        children: [
          Expanded(
            child: Container(
              color: Colors.black,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 250,
                    height: 250,
                    decoration: BoxDecoration(
                      border: Border.all(color: const Color(0xFF0D9488), width: 3),
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  const Positioned(
                    bottom: 60,
                    child: Text(
                      'Align patient pass QR code within box',
                      style: TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(20),
            color: Colors.white,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_scanned && _patientFound != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green.shade200),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle, color: Colors.green),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text('Checked-in: $_patientFound', style: const TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
                ElevatedButton(
                  onPressed: _simulateScan,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0D9488),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  child: const Text('Simulate Scan Verification'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
