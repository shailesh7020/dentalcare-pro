class AppLocalizations {
  final String locale;

  AppLocalizations(this.locale);

  static final Map<String, Map<String, String>> _localizedValues = {
    'en': {
      'app_title': 'DentalCare Pro',
      'login': 'Sign In',
      'biometric_login': 'Unlock with Face ID / Fingerprint',
      'todays_appointments': "Today's Appointments",
      'odontogram': 'Interactive Odontogram',
      'clinical_notes': 'Clinical Notes',
      'treatment_plan': 'Treatment Plan',
      'intraoral_camera': 'Intraoral Photos',
      'qr_checkin': 'Scan QR Check-In',
      'register_patient': 'New Patient Registration',
      'book_visit': 'Book Appointment',
      'prescriptions': 'My Prescriptions',
      'invoices': 'Billing & Payments',
      'sync_now': 'Sync Offline Data',
    },
    'es': {
      'app_title': 'DentalCare Pro',
      'login': 'Iniciar Sesión',
      'biometric_login': 'Desbloquear con Biometría',
      'todays_appointments': 'Citas de Hoy',
      'odontogram': 'Odontograma Interactivo',
      'clinical_notes': 'Notas Clínicas',
      'treatment_plan': 'Plan de Tratamiento',
      'intraoral_camera': 'Fotos Intraorales',
      'qr_checkin': 'Escanear QR de Llegada',
      'register_patient': 'Registrar Paciente',
      'book_visit': 'Reservar Cita',
      'prescriptions': 'Mis Recetas',
      'invoices': 'Facturación y Pagos',
      'sync_now': 'Sincronizar Datos',
    },
    'hi': {
      'app_title': 'डेंटलकेयर प्रो',
      'login': 'लॉग इन करें',
      'biometric_login': 'बायोमेट्रिक से खोलें',
      'todays_appointments': 'आज के अपॉइंटमेंट्स',
      'odontogram': 'दांतों का चार्ट (ओडोंटोग्राम)',
      'clinical_notes': 'क्लिनिकल नोट्स',
      'treatment_plan': 'उपचार योजना',
      'intraoral_camera': 'इंट्राओरल तस्वीरें',
      'qr_checkin': 'क्यूआर स्कैन चेक-इन',
      'register_patient': 'नया मरीज जोड़ें',
      'book_visit': 'अपॉइंटमेंट बुक करें',
      'prescriptions': 'नुस्खे (दवाएं)',
      'invoices': 'बिल और भुगतान',
      'sync_now': 'डेटा सिंक करें',
    },
  };

  String translate(String key) {
    return _localizedValues[locale]?[key] ?? _localizedValues['en']?[key] ?? key;
  }
}
