import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class MobileBillingScreen extends StatefulWidget {
  final String patientName;
  final ApiClient apiClient;

  const MobileBillingScreen({
    super.key,
    required this.patientName,
    required this.apiClient,
  });

  @override
  State<MobileBillingScreen> createState() => _MobileBillingScreenState();
}

class _MobileBillingScreenState extends State<MobileBillingScreen> {
  String _paymentMethod = 'UPI';
  final double _amount = 2500;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Invoice: ${widget.patientName}')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const Text('Amount Payable', style: TextStyle(color: Colors.grey)),
                    const SizedBox(height: 4),
                    Text('₹$_amount', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
                    const Divider(height: 24),
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Composite Restoration #16'),
                        Text('₹2,500'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text('Payment Mode', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Row(
              children: [
                _buildMethodChip('UPI', Icons.qr_code_2),
                const SizedBox(width: 8),
                _buildMethodChip('CASH', Icons.attach_money),
                const SizedBox(width: 8),
                _buildMethodChip('CARD', Icons.credit_card),
              ],
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Payment of ₹$_amount collected via $_paymentMethod!')),
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0D9488),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Record Payment & Send Receipt', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMethodChip(String method, IconData icon) {
    final isSelected = _paymentMethod == method;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _paymentMethod = method),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF0D9488) : Colors.grey.shade100,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            children: [
              Icon(icon, color: isSelected ? Colors.white : Colors.black87),
              const SizedBox(height: 4),
              Text(method, style: TextStyle(color: isSelected ? Colors.white : Colors.black87, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ),
    );
  }
}
