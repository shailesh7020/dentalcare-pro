import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class MyInvoicesScreen extends StatelessWidget {
  final ApiClient apiClient;

  const MyInvoicesScreen({super.key, required this.apiClient});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Billing & Invoices')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Outstanding Balance Card
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Colors.teal.shade50,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.teal.shade200),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Total Outstanding', style: TextStyle(color: Colors.grey, fontSize: 12)),
                    Text('₹2,500', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0D9488))),
                  ],
                ),
                ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Redirecting to secure UPI / Card payment gateway...')),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0D9488),
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Pay Online'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          const Text('Past Invoices', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Card(
            child: ListTile(
              title: const Text('Invoice #INV-2026-089'),
              subtitle: const Text('Root canal procedure • 02 Sep 2026'),
              trailing: const Text('₹2,500', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
          Card(
            child: ListTile(
              title: const Text('Invoice #INV-2026-042'),
              subtitle: const Text('Cleaning & Consultation • 14 May 2026 (Paid)'),
              trailing: const Text('₹1,500', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }
}
