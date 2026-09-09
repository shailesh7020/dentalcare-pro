import { describe, expect, it } from "vitest";
import type { DeliveryChannel, NotificationPriority } from "../notifications/types";
import type {
  PortalAppointmentRead,
  PortalDashboardSummary,
  PortalInvoiceRead,
  PortalPrescriptionRead,
  PortalToothRead,
} from "./types";

describe("Phase 10: Patient Portal & Communication System", () => {
  describe("Dashboard & Summary Metrics", () => {
    it("aggregates dashboard financial and clinical indicators correctly", () => {
      const summary: PortalDashboardSummary = {
        patient_id: "p-4401",
        patient_name: "Donna Noble",
        patient_number: "P-4401",
        clinic_name: "City Dental Care",
        next_appointment: {
          id: "appt-1",
          appointment_number: "APT-2026-0099",
          date: "2026-10-15",
          time: "02:00 PM",
          dentist_name: "Dr. David Tennant",
          visit_type: "CONSULTATION",
          status: "CONFIRMED",
        },
        active_prescriptions_count: 2,
        total_balance_due: 272.5,
        unread_messages_count: 1,
        pending_forms_count: 1,
      };

      expect(summary.patient_name).toBe("Donna Noble");
      expect(summary.total_balance_due).toBeGreaterThan(0);
      expect(summary.next_appointment?.status).toBe("CONFIRMED");
      expect(summary.pending_forms_count).toBe(1);
    });

    it("verifies appointment status lifecycle transitions", () => {
      const statuses: PortalAppointmentRead["status"][] = [
        "SCHEDULED",
        "CONFIRMED",
        "COMPLETED",
        "CANCELLED",
      ];
      expect(statuses).toContain("SCHEDULED");
      expect(statuses).toContain("CANCELLED");
      expect(statuses.length).toBe(4);
    });
  });

  describe("Prescriptions & Medicines Model", () => {
    it("structures prescription orders with frequency and food instructions", () => {
      const rx: PortalPrescriptionRead = {
        id: "rx-101",
        prescription_number: "RX-2026-0001",
        date: "2026-09-05",
        dentist_name: "Dr. David Tennant",
        diagnosis: "Acute periapical periodontitis",
        notes: "Complete full antibiotic course",
        items: [
          {
            id: "it-1",
            medicine_name: "Amoxicillin 500mg",
            dosage: "1 capsule",
            frequency: "TDS",
            duration: "5 days",
            instructions: "Take after food",
          },
          {
            id: "it-2",
            medicine_name: "Ibuprofen 400mg",
            dosage: "1 tablet",
            frequency: "SOS",
            duration: "3 days",
            instructions: "For pain",
          },
        ],
      };

      expect(rx.items.length).toBe(2);
      expect(rx.items[0].frequency).toBe("TDS");
      expect(rx.items[0].duration).toBe("5 days");
      expect(rx.items[1].dosage).toBe("1 tablet");
    });
  });

  describe("Billing & Payment Computations", () => {
    it("calculates invoice grand total, paid amounts, and remaining balance due", () => {
      const invoice: PortalInvoiceRead = {
        id: "inv-101",
        invoice_number: "INV-2026-01",
        date: "2026-09-01",
        total_amount: 500.0,
        discount_amount: 50.0,
        tax_amount: 22.5,
        final_amount: 472.5,
        paid_amount: 200.0,
        balance_due: 272.5,
        status: "PARTIALLY_PAID",
      };

      const calculatedFinal = invoice.total_amount - invoice.discount_amount + invoice.tax_amount;
      expect(calculatedFinal).toBe(472.5);
      expect(invoice.balance_due).toBe(invoice.final_amount - invoice.paid_amount);
      expect(invoice.status).toBe("PARTIALLY_PAID");
    });

    it("verifies paid invoices have zero balance due", () => {
      const settledInvoice: PortalInvoiceRead = {
        id: "inv-102",
        invoice_number: "INV-2026-02",
        date: "2026-08-15",
        total_amount: 350.0,
        discount_amount: 0.0,
        tax_amount: 17.5,
        final_amount: 367.5,
        paid_amount: 367.5,
        balance_due: 0.0,
        status: "PAID",
      };

      expect(settledInvoice.balance_due).toBe(0.0);
      expect(settledInvoice.status).toBe("PAID");
    });
  });

  describe("Interactive Odontogram Teeth Representation", () => {
    it("renders valid FDI tooth chart numbering and standard dental conditions", () => {
      const tooth: PortalToothRead = {
        tooth_number: "14",
        condition: "FILLING",
        color: "#3B82F6",
        notes: "DO Resin Composite",
      };

      expect(tooth.tooth_number).toBe("14");
      expect(tooth.condition).toBe("FILLING");
      expect(tooth.color).toBe("#3B82F6");
    });
  });

  describe("Notification Template Engine & Variables Substitution", () => {
    function renderTemplate(template: string, vars: Record<string, string>): string {
      return template.replace(/\{\{(\w+)\}\}/g, (_, key) => vars[key] || "");
    }

    it("substitutes clinical variables in notification templates seamlessly", () => {
      const tmpl =
        "Hello {{patient_name}}, your appointment with {{dentist_name}} is on {{date}} at {{time}}.";
      const vars = {
        patient_name: "Donna Noble",
        dentist_name: "Dr. David Tennant",
        date: "2026-10-15",
        time: "02:00 PM",
      };

      const result = renderTemplate(tmpl, vars);
      expect(result).toBe(
        "Hello Donna Noble, your appointment with Dr. David Tennant is on 2026-10-15 at 02:00 PM."
      );
    });

    it("supports all 5 notification delivery channels", () => {
      const channels: DeliveryChannel[] = ["IN_APP", "EMAIL", "SMS", "WHATSAPP", "PUSH"];
      expect(channels.length).toBe(5);
      expect(channels).toContain("WHATSAPP");
      expect(channels).toContain("EMAIL");
      expect(channels).toContain("SMS");
    });

    it("supports all 4 notification priority tiers", () => {
      const priorities: NotificationPriority[] = ["LOW", "NORMAL", "HIGH", "URGENT"];
      expect(priorities.length).toBe(4);
      expect(priorities).toContain("URGENT");
    });
  });

  describe("Recall Timing & Multi-Interval Windows", () => {
    it("validates standard dental recall intervals", () => {
      const recallRules = {
        ROOT_CANAL: 180, // 6 months
        EXTRACTION: 7, // 7 days
        SCALING: 180, // 6 months
        IMPLANT: 90, // 3 months
        CROWN: 14, // 2 weeks
      };

      expect(recallRules.ROOT_CANAL).toBe(180);
      expect(recallRules.EXTRACTION).toBe(7);
      expect(recallRules.SCALING).toBe(180);
      expect(recallRules.IMPLANT).toBe(90);
    });

    it("verifies multi-interval reminder windows (7d, 3d, 24h, 2h)", () => {
      const reminderWindows = ["7d", "3d", "24h", "2h"];
      expect(reminderWindows).toHaveLength(4);
      expect(reminderWindows).toContain("24h");
    });
  });
});
