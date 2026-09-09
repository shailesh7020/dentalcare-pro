export type DeliveryChannel = "IN_APP" | "EMAIL" | "SMS" | "WHATSAPP" | "PUSH";
export type NotificationType =
  | "APPOINTMENT_REMINDER"
  | "APPOINTMENT_CONFIRMATION"
  | "APPOINTMENT_CANCELLED"
  | "APPOINTMENT_RESCHEDULED"
  | "APPOINTMENT_BOOKED"
  | "BILLING_INVOICE_GENERATED"
  | "BILLING_PAYMENT_RECEIVED"
  | "BILLING_PAYMENT_OVERDUE"
  | "TREATMENT_PLAN_SHARED"
  | "PRESCRIPTION_ISSUED"
  | "FOLLOW_UP_RECALL"
  | "CONSENT_FORM_REQUIRED"
  | "SYSTEM_ALERT";

export type NotificationPriority = "LOW" | "NORMAL" | "HIGH" | "URGENT";

export interface NotificationRecord {
  id: string;
  clinic_id: string;
  patient_id?: string;
  user_id?: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  delivery_channel: DeliveryChannel;
  title: string;
  message: string;
  is_read: boolean;
  read_at?: string;
  delivered_at?: string;
  error_message?: string;
  created_at: string;
  patient_name?: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  template_key: string;
  channel: DeliveryChannel;
  subject_template?: string;
  body_template: string;
  variables_schema: Record<string, string>;
  is_active: boolean;
}

export interface ClinicNotificationSettings {
  id: string;
  clinic_id: string;
  email_enabled: boolean;
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  reminder_7d_enabled: boolean;
  reminder_3d_enabled: boolean;
  reminder_24h_enabled: boolean;
  reminder_2h_enabled: boolean;
  auto_recall_enabled: boolean;
  email_from_name?: string;
  whatsapp_phone_number?: string;
}

export interface NotificationStats {
  total_sent: number;
  unread_count: number;
  by_channel: Record<DeliveryChannel, number>;
  by_type: Record<string, number>;
}
