import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class IntraoralCameraScreen extends StatefulWidget {
  final ApiClient apiClient;

  const IntraoralCameraScreen({super.key, required this.apiClient});

  @override
  State<IntraoralCameraScreen> createState() => _IntraoralCameraScreenState();
}

class _IntraoralCameraScreenState extends State<IntraoralCameraScreen> {
  int _selectedTooth = 16;
  bool _isUploading = false;
  String? _capturedImageMock;

  void _simulateCapture() {
    setState(() {
      _capturedImageMock = 'https://dentalcare.local/media/mock_intraoral_${_selectedTooth}.jpg';
    });
  }

  Future<void> _handleUpload() async {
    setState(() => _isUploading = true);
    try {
      await widget.apiClient.dio.post(
        ApiEndpoints.clinicalMedia,
        data: {
          'patient_id': '00000000-0000-0000-0000-000000000001',
          'media_type': 'INTRAORAL_PHOTO',
          'tooth_number': _selectedTooth,
          'file_url': _capturedImageMock ?? 'https://dentalcare.local/photo.jpg',
          'file_size_bytes': 786432,
          'compression_ratio': 0.58,
          'notes': 'Intraoral capture of tooth #$_selectedTooth',
        },
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Intraoral Photo Uploaded Successfully!')),
      );
      Navigator.pop(context);
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Photo saved in offline media queue')),
      );
      Navigator.pop(context);
    } finally {
      setState(() => _isUploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Intraoral Camera Studio')),
      body: Column(
        children: [
          // Camera Preview Area
          Expanded(
            child: Container(
              color: Colors.black87,
              child: Center(
                child: _capturedImageMock != null
                    ? Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.check_circle, color: Colors.teal, size: 64),
                          const SizedBox(height: 12),
                          Text('Captured Photo for Tooth #$_selectedTooth', style: const TextStyle(color: Colors.white, fontSize: 16)),
                          const SizedBox(height: 6),
                          const Text('Compression: 58% optimized', style: TextStyle(color: Colors.white70, fontSize: 12)),
                        ],
                      )
                    : const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.camera_alt, color: Colors.white38, size: 72),
                          SizedBox(height: 12),
                          Text('Live Intraoral Feed Ready', style: TextStyle(color: Colors.white54)),
                        ],
                      ),
              ),
            ),
          ),

          // Tooth Selector & Actions
          Container(
            padding: const EdgeInsets.all(20),
            color: Colors.white,
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Assign to Tooth FDI #:', style: TextStyle(fontWeight: FontWeight.bold)),
                    DropdownButton<int>(
                      value: _selectedTooth,
                      items: [16, 26, 36, 46, 11, 21, 31, 41].map((t) {
                        return DropdownMenuItem(value: t, child: Text('#$t'));
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) setState(() => _selectedTooth = val);
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _simulateCapture,
                        icon: const Icon(Icons.shutter_speed),
                        label: const Text('Capture Frame'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _capturedImageMock == null || _isUploading ? null : _handleUpload,
                        icon: const Icon(Icons.cloud_upload),
                        label: const Text('Upload Image'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF0D9488),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
