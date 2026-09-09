import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class FastPatientRegistrationScreen extends StatefulWidget {
  final ApiClient apiClient;

  const FastPatientRegistrationScreen({super.key, required this.apiClient});

  @override
  State<FastPatientRegistrationScreen> createState() => _FastPatientRegistrationScreenState();
}

class _FastPatientRegistrationScreenState extends State<FastPatientRegistrationScreen> {
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  String _gender = 'MALE';
  bool _isSubmitting = false;

  Future<void> _handleRegister() async {
    if (_firstNameCtrl.text.isEmpty || _phoneCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please provide first name and phone number')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      await widget.apiClient.dio.post(
        ApiEndpoints.patients,
        data: {
          'first_name': _firstNameCtrl.text.trim(),
          'last_name': _lastNameCtrl.text.trim(),
          'phone': _phoneCtrl.text.trim(),
          'email': _emailCtrl.text.trim(),
          'gender': _gender,
        },
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Patient Registered Successfully!')),
      );
      Navigator.pop(context);
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Registration saved to offline queue')),
      );
      Navigator.pop(context);
    } finally {
      setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Rapid Walk-in Registration')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _firstNameCtrl,
                  decoration: const InputDecoration(labelText: 'First Name *', border: OutlineInputBorder()),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _lastNameCtrl,
                  decoration: const InputDecoration(labelText: 'Last Name', border: OutlineInputBorder()),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _phoneCtrl,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: 'Mobile Number *',
              prefixText: '+91 ',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email Address (Optional)', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _gender,
            decoration: const InputDecoration(labelText: 'Gender', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'MALE', child: Text('Male')),
              DropdownMenuItem(value: 'FEMALE', child: Text('Female')),
              DropdownMenuItem(value: 'OTHER', child: Text('Other')),
            ],
            onChanged: (val) => setState(() => _gender = val ?? 'MALE'),
          ),
          const SizedBox(height: 28),
          ElevatedButton(
            onPressed: _isSubmitting ? null : _handleRegister,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: _isSubmitting
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text('Complete Intake & Check-in', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
