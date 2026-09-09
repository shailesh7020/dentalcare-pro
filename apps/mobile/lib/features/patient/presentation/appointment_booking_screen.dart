import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class AppointmentBookingScreen extends StatefulWidget {
  final ApiClient apiClient;

  const AppointmentBookingScreen({super.key, required this.apiClient});

  @override
  State<AppointmentBookingScreen> createState() => _AppointmentBookingScreenState();
}

class _AppointmentBookingScreenState extends State<AppointmentBookingScreen> {
  String _selectedReason = 'Routine Dental Checkup';
  String _selectedDoctor = 'Dr. Neil Shah';
  String _selectedSlot = '10:00 AM';

  final List<String> _slots = ['09:00 AM', '10:00 AM', '11:30 AM', '02:00 PM', '03:30 PM', '04:30 PM'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Book Appointment')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Select Doctor', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedDoctor,
              decoration: const InputDecoration(border: OutlineInputBorder()),
              items: const [
                DropdownMenuItem(value: 'Dr. Neil Shah', child: Text('Dr. Neil Shah (Endodontist)')),
                DropdownMenuItem(value: 'Dr. Maya Iyer', child: Text('Dr. Maya Iyer (Orthodontist)')),
              ],
              onChanged: (val) => setState(() => _selectedDoctor = val ?? 'Dr. Neil Shah'),
            ),
            const SizedBox(height: 20),

            const Text('Reason for Visit', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedReason,
              decoration: const InputDecoration(border: OutlineInputBorder()),
              items: const [
                DropdownMenuItem(value: 'Routine Dental Checkup', child: Text('Routine Dental Checkup')),
                DropdownMenuItem(value: 'Toothache / Emergency', child: Text('Toothache / Emergency')),
                DropdownMenuItem(value: 'Teeth Whitening & Cleaning', child: Text('Teeth Whitening & Cleaning')),
              ],
              onChanged: (val) => setState(() => _selectedReason = val ?? 'Routine Dental Checkup'),
            ),
            const SizedBox(height: 24),

            const Text('Available Slots Tomorrow', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: _slots.map((slot) {
                final isSelected = _selectedSlot == slot;
                return ChoiceChip(
                  label: Text(slot),
                  selected: isSelected,
                  selectedColor: const Color(0xFF0D9488),
                  labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black87),
                  onSelected: (_) => setState(() => _selectedSlot = slot),
                );
              }).toList(),
            ),
            const Spacer(),

            ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Appointment booked with $_selectedDoctor at $_selectedSlot!')),
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0D9488),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Confirm Appointment', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }
}
