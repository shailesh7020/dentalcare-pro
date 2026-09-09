export type ConversationType = "PATIENT_CLINIC" | "STAFF_INTERNAL";

export interface ConversationParticipant {
  id: string;
  conversation_id: string;
  user_id?: string;
  patient_id?: string;
  name: string;
  role: string;
  joined_at: string;
}

export interface MessageRead {
  id: string;
  conversation_id: string;
  sender_user_id?: string;
  sender_patient_id?: string;
  sender_name?: string;
  content: string;
  attachments_json?: string;
  is_read: boolean;
  created_at: string;
}

export interface ConversationRead {
  id: string;
  clinic_id: string;
  conversation_type: ConversationType;
  title?: string;
  patient_id?: string;
  patient_name?: string;
  is_active: boolean;
  last_message_at?: string;
  created_at: string;
  unread_count?: number;
  last_message?: string;
  participants: ConversationParticipant[];
}
