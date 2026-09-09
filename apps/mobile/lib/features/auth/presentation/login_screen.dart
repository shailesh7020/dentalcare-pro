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
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Authentication failed: ${e.toString()}'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
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
              const SizedBox(height: 40),
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
