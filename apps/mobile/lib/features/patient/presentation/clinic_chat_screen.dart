import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class ClinicChatScreen extends StatefulWidget {
  final ApiClient apiClient;

  const ClinicChatScreen({super.key, required this.apiClient});

  @override
  State<ClinicChatScreen> createState() => _ClinicChatScreenState();
}

class _ClinicChatScreenState extends State<ClinicChatScreen> {
  final _msgCtrl = TextEditingController();
  final List<Map<String, String>> _messages = [
    {'sender': 'CLINIC', 'text': 'Hello Aarav! How are you feeling after your checkup?'},
    {'sender': 'PATIENT', 'text': 'Doing well! Mild sensitivity on cold water.'},
    {'sender': 'CLINIC', 'text': 'That is expected for 24-48 hours. Continue prescribed mouthwash.'},
  ];

  void _sendMessage() {
    if (_msgCtrl.text.trim().isEmpty) return;
    setState(() {
      _messages.add({'sender': 'PATIENT', 'text': _msgCtrl.text.trim()});
      _msgCtrl.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Clinic Front Desk Chat')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final m = _messages[index];
                final isPatient = m['sender'] == 'PATIENT';
                return Align(
                  alignment: isPatient ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: isPatient ? const Color(0xFF0D9488) : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      m['text']!,
                      style: TextStyle(color: isPatient ? Colors.white : Colors.black87),
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _msgCtrl,
                    decoration: InputDecoration(
                      hintText: 'Type your message...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send, color: Color(0xFF0D9488)),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
