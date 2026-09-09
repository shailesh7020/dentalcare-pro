import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class AIHealthAssistantScreen extends StatefulWidget {
  final ApiClient apiClient;

  const AIHealthAssistantScreen({super.key, required this.apiClient});

  @override
  State<AIHealthAssistantScreen> createState() => _AIHealthAssistantScreenState();
}

class _AIHealthAssistantScreenState extends State<AIHealthAssistantScreen> {
  final _queryCtrl = TextEditingController(text: 'What should I do after a dental filling?');
  String? _answer;
  bool _loading = false;

  Future<void> _askAi() async {
    setState(() => _loading = true);
    try {
      final res = await widget.apiClient.dio.post(
        ApiEndpoints.aiAssist,
        data: {
          'task_type': 'PATIENT_EDUCATION',
          'context_text': _queryCtrl.text,
        },
      );
      if (res.statusCode == 200) {
        setState(() {
          _answer = res.data['suggestion'];
        });
      }
    } catch (_) {
      setState(() {
        _answer = 'Post-Care Guidance:\n• Avoid eating until numbness completely wears off.\n• Maintain gentle brushing.\n• Call clinic if pain worsens.';
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Health Guide')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Medical disclaimer banner
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, color: Colors.blue, size: 20),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Informational assistance only. This does not substitute professional clinical diagnosis.',
                    style: TextStyle(fontSize: 11, color: Colors.blueGrey),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          TextField(
            controller: _queryCtrl,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'Ask your dental question',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _loading ? null : _askAi,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Ask AI Assistant'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
          const SizedBox(height: 20),

          if (_loading) const Center(child: CircularProgressIndicator()),

          if (_answer != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('DentalCare AI Answer', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    const SizedBox(height: 8),
                    Text(_answer!, style: const TextStyle(fontSize: 13, height: 1.4)),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
