import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';
import '../../../core/auth/biometric_service.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/sync/offline_sync_engine.dart';
import '../../dentist/presentation/dentist_dashboard_screen.dart';
import '../../patient/presentation/patient_home_screen.dart';
import '../../receptionist/presentation/receptionist_dashboard_screen.dart';

class LoginScreen extends StatefulWidget {
  final SecureStorageService secureStorage;
  final ApiClient apiClient;
  final BiometricService biometricService;
  final OfflineSyncEngine syncEngine;
  final VoidCallback onToggleTheme;

  const LoginScreen({
    super.key,
    required this.secureStorage,
    required this.apiClient,
    required this.biometricService,
    required this.syncEngine,
    required this.onToggleTheme,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController(text: 'doctor@dentalcarepro.com');
  final _passCtrl = TextEditingController(text: 'Password@123');
  String _selectedRole = 'DENTIST';
  bool _isLoading = false;
  bool _biometricAvailable = false;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
  }

  Future<void> _checkBiometrics() async {
    final available = await widget.biometricService.isBiometricAvailable();
    setState(() => _biometricAvailable = available);
  }

  Future<void> _handleLogin() async {
    setState(() => _isLoading = true);
    try {
      final response = await widget.apiClient.dio.post(
        ApiEndpoints.login,
        data: {
          'email': _emailCtrl.text.trim(),
          'password': _passCtrl.text.trim(),
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        final assignedRole = data['role'] ?? _selectedRole;
        await widget.secureStorage.saveTokens(
          accessToken: data['access_token'],
          refreshToken: data['refresh_token'],
          userRole: assignedRole,
          userId: data['user_id'] ?? 'user-1',
          clinicId: data['clinic_id'],
        );

        _navigateToRoleHome(assignedRole);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Invalid email or password. Please try again.'),
              backgroundColor: Colors.redAccent,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        final savedRole = await widget.secureStorage.getUserRole();
        if (savedRole != null) {
          _showOfflineOptionDialog(savedRole, e.toString());
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Cannot reach clinic server: ${e.toString()}'),
              backgroundColor: Colors.redAccent,
              duration: const Duration(seconds: 5),
              action: SnackBarAction(
                label: 'Configure',
                textColor: Colors.white,
                onPressed: _showServerConfigDialog,
              ),
            ),
          );
        }
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showOfflineOptionDialog(String savedRole, String errorMsg) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.wifi_off_rounded, color: Colors.amber),
            SizedBox(width: 8),
            Text('Offline Mode Available', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'The clinic server is unreachable from this network. You can continue using cached patient records and appointments.',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 8),
            Text('Saved profile: $savedRole', style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _showServerConfigDialog();
            },
            child: const Text('Change Server URL'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _navigateToRoleHome(savedRole);
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0D9488), foregroundColor: Colors.white),
            child: const Text('Open in Offline Mode'),
          ),
        ],
      ),
    );
  }

  Future<void> _showServerConfigDialog() async {
    final currentUrl = widget.apiClient.baseUrl;
    final ctrl = TextEditingController(text: currentUrl);
    String? testResult;
    bool isTesting = false;

    await showDialog<void>(
      context: context,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            title: const Row(
              children: [
                Icon(Icons.dns_outlined, color: Color(0xFF0D9488)),
                SizedBox(width: 8),
                Text('Server Connection', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Configure the API endpoint URL for on-premise clinic LAN, Cloudflare Tunnel, or remote access.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: ctrl,
                    decoration: InputDecoration(
                      labelText: 'API Base URL',
                      hintText: 'https://api.yourclinic.com/api/v1',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      isDense: true,
                    ),
                    style: const TextStyle(fontSize: 13),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: [
                      ActionChip(
                        label: const Text('Local LAN', style: TextStyle(fontSize: 11)),
                        onPressed: () => setDialogState(() => ctrl.text = 'https://api.dentalcarepro.local/api/v1'),
                      ),
                      ActionChip(
                        label: const Text('Local IP:8000', style: TextStyle(fontSize: 11)),
                        onPressed: () => setDialogState(() => ctrl.text = 'http://192.168.1.100:8000/api/v1'),
                      ),
                      ActionChip(
                        label: const Text('Remote Tunnel', style: TextStyle(fontSize: 11)),
                        onPressed: () => setDialogState(() => ctrl.text = 'https://clinic.dentalcarepro.com/api/v1'),
                      ),
                    ],
                  ),
                  if (testResult != null) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: testResult!.startsWith('OK') ? Colors.green.shade50 : Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: testResult!.startsWith('OK') ? Colors.green.shade200 : Colors.red.shade200),
                      ),
                      child: Text(
                        testResult!,
                        style: TextStyle(
                          fontSize: 11,
                          color: testResult!.startsWith('OK') ? Colors.green.shade800 : Colors.red.shade800,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: isTesting
                    ? null
                    : () async {
                        setDialogState(() {
                          isTesting = true;
                          testResult = null;
                        });
                        try {
                          final testDio = Dio(BaseOptions(connectTimeout: const Duration(seconds: 5)));
                          final target = ctrl.text.trim();
                          final pingUrl = target.endsWith('/api/v1') ? target.replaceAll('/api/v1', '/api/v1/health') : '$target/health';
                          final res = await testDio.get(pingUrl);
                          setDialogState(() {
                            isTesting = false;
                            testResult = 'OK (${res.statusCode}): Server is reachable!';
                          });
                        } catch (err) {
                          setDialogState(() {
                            isTesting = false;
                            testResult = 'Unreachable: ${err.toString().split("\n").first}';
                          });
                        }
                      },
                child: isTesting
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Test Connection'),
              ),
              ElevatedButton(
                onPressed: () async {
                  final newUrl = ctrl.text.trim();
                  if (newUrl.isNotEmpty) {
                    await widget.secureStorage.setServerUrl(newUrl);
                    widget.apiClient.setBaseUrl(newUrl);
                    if (mounted) setState(() {});
                  }
                  Navigator.pop(dialogCtx);
                },
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0D9488), foregroundColor: Colors.white),
                child: const Text('Save & Apply'),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _handleBiometricLogin() async {
    final authenticated = await widget.biometricService.authenticate(
      reason: 'Scan Face or Fingerprint to access DentalCare Pro',
    );
    if (authenticated) {
      final savedRole = await widget.secureStorage.getUserRole() ?? _selectedRole;
      _navigateToRoleHome(savedRole);
    }
  }

  void _navigateToRoleHome(String role) {
    Widget destination;
    switch (role) {
      case 'DENTIST':
        destination = DentistDashboardScreen(
          syncEngine: widget.syncEngine,
          apiClient: widget.apiClient,
          onToggleTheme: widget.onToggleTheme,
        );
        break;
      case 'RECEPTIONIST':
        destination = ReceptionistDashboardScreen(
          syncEngine: widget.syncEngine,
          apiClient: widget.apiClient,
        );
        break;
      case 'PATIENT':
      default:
        destination = PatientHomeScreen(
          syncEngine: widget.syncEngine,
          apiClient: widget.apiClient,
        );
        break;
    }

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => destination),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top Server Connection Status Bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  GestureDetector(
                    onTap: _showServerConfigDialog,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.circle,
                            size: 8,
                            color: widget.apiClient.baseUrl.contains('.local') ? Colors.amber.shade700 : const Color(0xFF0D9488),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            widget.apiClient.baseUrl.replaceAll('https://', '').replaceAll('http://', '').replaceAll('/api/v1', ''),
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Colors.black87),
                          ),
                        ],
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.settings_outlined, color: Colors.grey, size: 20),
                    tooltip: 'Server Connection Settings',
                    onPressed: _showServerConfigDialog,
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Center(
                child: Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D9488),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Center(
                    child: Text('DC', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Center(
                child: Text('DentalCare Pro', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
              ),
              const Center(
                child: Text('Enterprise Practice Mobility', style: TextStyle(color: Colors.grey, fontSize: 14)),
              ),
              const SizedBox(height: 32),

              // Role Selector Tabs
              Container(
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(12),
                ),
                padding: const EdgeInsets.all(4),
                child: Row(
                  children: [
                    _buildRoleTab('DENTIST', 'Dentist'),
                    _buildRoleTab('RECEPTIONIST', 'Receptionist'),
                    _buildRoleTab('PATIENT', 'Patient'),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              TextField(
                controller: _emailCtrl,
                decoration: InputDecoration(
                  labelText: 'Email Address',
                  prefixIcon: const Icon(Icons.email_outlined),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passCtrl,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock_outline),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 24),

              ElevatedButton(
                onPressed: _isLoading ? null : _handleLogin,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0D9488),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Sign In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),

              if (_biometricAvailable) ...[
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: _handleBiometricLogin,
                  icon: const Icon(Icons.fingerprint, size: 24),
                  label: const Text('Biometric Quick Unlock'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRoleTab(String roleKey, String label) {
    final isSelected = _selectedRole == roleKey;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedRole = roleKey),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: isSelected ? [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4)] : null,
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: isSelected ? const Color(0xFF0D9488) : Colors.grey.shade700,
                fontSize: 13,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
