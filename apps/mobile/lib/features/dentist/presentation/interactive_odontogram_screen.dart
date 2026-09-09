import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';

class InteractiveOdontogramScreen extends StatefulWidget {
  final String patientId;
  final String patientName;
  final ApiClient apiClient;

  const InteractiveOdontogramScreen({
    super.key,
    required this.patientId,
    required this.patientName,
    required this.apiClient,
  });

  @override
  State<InteractiveOdontogramScreen> createState() => _InteractiveOdontogramScreenState();
}

class _InteractiveOdontogramScreenState extends State<InteractiveOdontogramScreen> {
  int? _selectedTooth;
  final Map<int, String> _toothConditions = {
    16: 'CARIES',
    26: 'RESTORATION',
    36: 'ROOT_CANAL',
    46: 'CROWN',
  };

  // Adult FDI Tooth quadrants
  final List<int> _upperRight = [18, 17, 16, 15, 14, 13, 12, 11];
  final List<int> _upperLeft = [21, 22, 23, 24, 25, 26, 27, 28];
  final List<int> _lowerRight = [48, 47, 46, 45, 44, 43, 42, 41];
  final List<int> _lowerLeft = [31, 32, 33, 34, 35, 36, 37, 38];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Odontogram: ${widget.patientName}'),
      ),
      body: Column(
        children: [
          // Arch selector / instruction
          Container(
            color: Colors.teal.shade50,
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.touch_app, size: 16, color: Color(0xFF0D9488)),
                SizedBox(width: 8),
                Text('Tap any tooth to inspect surfaces or record findings', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Upper Arch
          const Text('Maxillary Arch (Upper)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey)),
          const SizedBox(height: 6),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                ..._upperRight.map((t) => _buildToothWidget(t)),
                Container(width: 2, height: 40, color: Colors.grey.shade300, margin: const EdgeInsets.symmetric(horizontal: 4)),
                ..._upperLeft.map((t) => _buildToothWidget(t)),
              ],
            ),
          ),
          const Divider(height: 32),

          // Lower Arch
          const Text('Mandibular Arch (Lower)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.grey)),
          const SizedBox(height: 6),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                ..._lowerRight.map((t) => _buildToothWidget(t)),
                Container(width: 2, height: 40, color: Colors.grey.shade300, margin: const EdgeInsets.symmetric(horizontal: 4)),
                ..._lowerLeft.map((t) => _buildToothWidget(t)),
              ],
            ),
          ),
          const Spacer(),

          // Details panel for selected tooth
          if (_selectedTooth != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 10, offset: const Offset(0, -3))],
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Tooth #$_selectedTooth', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      Text(
                        _toothConditions[_selectedTooth] ?? 'HEALTHY',
                        style: TextStyle(
                          color: _toothConditions.containsKey(_selectedTooth) ? Colors.orange.shade800 : Colors.green,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    children: [
                      _buildConditionAction('CARIES', Colors.red),
                      _buildConditionAction('RESTORATION', Colors.blue),
                      _buildConditionAction('ROOT_CANAL', Colors.purple),
                      _buildConditionAction('EXTRACTION', Colors.grey),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildToothWidget(int toothNumber) {
    final isSelected = _selectedTooth == toothNumber;
    final condition = _toothConditions[toothNumber];

    Color bgColor = Colors.white;
    if (condition == 'CARIES') bgColor = Colors.red.shade100;
    if (condition == 'RESTORATION') bgColor = Colors.blue.shade100;
    if (condition == 'ROOT_CANAL') bgColor = Colors.purple.shade100;

    return GestureDetector(
      onTap: () => setState(() => _selectedTooth = toothNumber),
      child: Container(
        width: 38,
        height: 54,
        margin: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          color: bgColor,
          border: Border.all(
            color: isSelected ? const Color(0xFF0D9488) : Colors.grey.shade400,
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Center(
          child: Text(
            '$toothNumber',
            style: TextStyle(
              fontSize: 12,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
              color: isSelected ? const Color(0xFF0D9488) : Colors.black87,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildConditionAction(String name, Color color) {
    return ActionChip(
      label: Text(name, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.bold)),
      backgroundColor: color.withOpacity(0.1),
      onPressed: () {
        if (_selectedTooth != null) {
          setState(() => _toothConditions[_selectedTooth!] = name);
        }
      },
    );
  }
}
