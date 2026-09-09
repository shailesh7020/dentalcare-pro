import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../common/signature_pad_dialog.dart';

class TreatmentPlanBuilderScreen extends StatefulWidget {
  final String patientId;
  final ApiClient apiClient;

  const TreatmentPlanBuilderScreen({
    super.key,
    required this.patientId,
    required this.apiClient,
  });

  @override
  State<TreatmentPlanBuilderScreen> createState() => _TreatmentPlanBuilderScreenState();
}

class _TreatmentPlanBuilderScreenState extends State<TreatmentPlanBuilderScreen> {
  final List<Map<String, dynamic>> _procedures = [
    {'name': 'Dental Prophylaxis (Scaling)', 'tooth': 'All', 'cost': 1500, 'selected': true},
    {'name': 'Composite Restoration #16', 'tooth': '16', 'cost': 2500, 'selected': true},
    {'name': 'Porcelain Fused to Metal Crown #26', 'tooth': '26', 'cost': 8000, 'selected': false},
  ];

  String? _doctorSignature;

  double get _totalEstimate => _procedures
      .where((p) => p['selected'] as bool)
      .fold(0, (sum, p) => sum + (p['cost'] as num));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Treatment Plan Builder')),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text('Selected Procedures', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ..._procedures.map((proc) {
                  return CheckboxListTile(
                    title: Text(proc['name'], style: const TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text('Tooth: ${proc['tooth']} • Estimated: ₹${proc['cost']}'),
                    value: proc['selected'] as bool,
                    activeColor: const Color(0xFF0D9488),
                    onChanged: (val) => setState(() => proc['selected'] = val ?? false),
                  );
                }),
                const SizedBox(height: 20),

                // Digital signature indicator
                Card(
                  child: ListTile(
                    leading: Icon(
                      _doctorSignature != null ? Icons.verified : Icons.gesture,
                      color: _doctorSignature != null ? Colors.green : Colors.grey,
                    ),
                    title: const Text('Dentist Digital Sign-Off'),
                    subtitle: Text(_doctorSignature != null ? 'Signed digitally by Dr. Neil Shah' : 'Pending signature'),
                    trailing: TextButton(
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (_) => SignaturePadDialog(
                            title: 'Dentist Treatment Approval',
                            signerRole: 'Attending Clinician',
                            onSave: (sig) => setState(() => _doctorSignature = sig),
                          ),
                        );
                      },
                      child: Text(_doctorSignature != null ? 'Re-sign' : 'Sign Now'),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Total and Submit Bar
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 6)],
            ),
            child: Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('Total Estimate', style: TextStyle(color: Colors.grey, fontSize: 12)),
                    Text('₹$_totalEstimate', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  ],
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Treatment Plan Generated and Sent to Patient!')),
                    );
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0D9488),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                  child: const Text('Publish Plan'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
