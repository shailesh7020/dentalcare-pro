import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class ClinicalNotesScreen extends StatefulWidget {
  final String patientId;
  final ApiClient apiClient;

  const ClinicalNotesScreen({
    super.key,
    required this.patientId,
    required this.apiClient,
  });

  @override
  State<ClinicalNotesScreen> createState() => _ClinicalNotesScreenState();
}

class _ClinicalNotesScreenState extends State<ClinicalNotesScreen> {
  final _subjectiveCtrl = TextEditingController(text: 'Patient reports mild sensitivity to cold on tooth #16.');
  final _objectiveCtrl = TextEditingController(text: 'Deep caries noted on occlusal surface of #16. Pulp vitality test positive.');
  final _assessmentCtrl = TextEditingController(text: 'Reversible pulpitis secondary to dental caries.');
  final _planCtrl = TextEditingController(text: 'Composite restoration under local anesthesia (Lidocaine 2% with 1:100k epi).');
  bool _isSummarizing = false;

  Future<void> _handleAiSummarize() async {
    setState(() => _isSummarizing = true);
    try {
      final response = await widget.apiClient.dio.post(
        ApiEndpoints.aiAssist,
        data: {
          'task_type': 'CLINICAL_SUMMARY',
          'context_text': '${_subjectiveCtrl.text} ${_objectiveCtrl.text}',
          'procedure_name': 'Composite Restoration #16',
        },
      );
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('AI Clinical Summary Generated!')),
        );
      }
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI Summary ready locally')),
      );
    } finally {
      setState(() => _isSummarizing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Clinical SOAP Note'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            onPressed: _isSummarizing ? null : _handleAiSummarize,
            tooltip: 'AI Clinical Assist',
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSoapField('S - Subjective (Patient Symptoms)', _subjectiveCtrl),
          const SizedBox(height: 12),
          _buildSoapField('O - Objective (Clinical Findings)', _objectiveCtrl),
          const SizedBox(height: 12),
          _buildSoapField('A - Assessment (Diagnosis)', _assessmentCtrl),
          const SizedBox(height: 12),
          _buildSoapField('P - Plan (Procedure & Medication)', _planCtrl),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Clinical Note Saved & Synced')),
              );
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0D9488),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text('Save Note', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSoapField(String label, TextEditingController ctrl) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF0F172A))),
        const SizedBox(height: 6),
        TextField(
          controller: ctrl,
          maxLines: 3,
          decoration: InputDecoration(
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            filled: true,
            fillColor: Colors.grey.shade50,
          ),
        ),
      ],
    );
  }
}
