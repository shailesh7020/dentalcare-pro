import { describe, expect, it } from "vitest";
import { z } from "zod";

describe("Frontend UI & Design System QA", () => {
  describe("Role Focus Modes", () => {
    const validModes = ["all", "receptionist", "dentist", "admin"] as const;

    it("verifies all enterprise station focus profiles are valid", () => {
      expect(validModes).toContain("all");
      expect(validModes).toContain("receptionist");
      expect(validModes).toContain("dentist");
      expect(validModes).toContain("admin");
    });
  });

  describe("Command Palette Spotlight Search Logic", () => {
    type CommandItem = {
      id: string;
      title: string;
      category: string;
      keywords: string[];
      href: string;
    };

    const commands: CommandItem[] = [
      {
        id: "new-patient",
        title: "Register New Patient",
        category: "Quick Actions",
        href: "/patients/new",
        keywords: ["add", "create", "patient", "register"],
      },
      {
        id: "book-visit",
        title: "Book Appointment",
        category: "Quick Actions",
        href: "/appointments?book=true",
        keywords: ["schedule", "appointment", "calendar", "visit"],
      },
      {
        id: "new-invoice",
        title: "Create Invoice / Bill",
        category: "Quick Actions",
        href: "/billing/new",
        keywords: ["billing", "payment", "invoice", "receipt"],
      },
      {
        id: "ai-studio",
        title: "AI Clinical Assistant",
        category: "Quick Actions",
        href: "/ai",
        keywords: ["ai", "assistant", "soap", "summary", "intelligence"],
      },
      {
        id: "nav-inventory",
        title: "Inventory & Dental Supplies",
        category: "Operations & Finance",
        href: "/inventory",
        keywords: ["inventory", "stock", "supplies", "medicines"],
      },
    ];

    function filterCommands(query: string): CommandItem[] {
      if (!query.trim()) return commands;
      const q = query.toLowerCase().trim();
      return commands.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q) ||
          c.keywords.some((k) => k.toLowerCase().includes(q))
      );
    }

    it("returns all commands on empty query", () => {
      expect(filterCommands("")).toHaveLength(5);
    });

    it("finds patient registration by keyword 'register'", () => {
      const results = filterCommands("register");
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("new-patient");
    });

    it("finds appointment booking by title 'Appointment'", () => {
      const results = filterCommands("Appointment");
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("book-visit");
    });

    it("finds billing by keyword 'receipt'", () => {
      const results = filterCommands("receipt");
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("new-invoice");
    });

    it("returns empty list for non-matching search term", () => {
      const results = filterCommands("nonexistent-xyz-feature");
      expect(results).toHaveLength(0);
    });
  });

  describe("Clinical Form Input Guardrails", () => {
    const MOBILE_REGEX = /^[6-9]\d{9}$/;
    const PIN_REGEX = /^\d{6}$/;

    const quickPatientSchema = z.object({
      first_name: z.string().min(1).max(80),
      mobile_number: z.string().regex(MOBILE_REGEX, "Invalid Indian mobile"),
      pin_code: z.string().regex(PIN_REGEX, "Invalid 6-digit PIN").optional().or(z.literal("")),
      age: z.number().int().min(0).max(130),
    });

    it("accepts valid patient inputs", () => {
      const res = quickPatientSchema.safeParse({
        first_name: "Rohan",
        mobile_number: "9820098200",
        pin_code: "400001",
        age: 32,
      });
      expect(res.success).toBe(true);
    });

    it("rejects invalid mobile numbers", () => {
      const res = quickPatientSchema.safeParse({
        first_name: "Rohan",
        mobile_number: "12345",
        age: 32,
      });
      expect(res.success).toBe(false);
    });

    it("rejects age over biological limits (>130)", () => {
      const res = quickPatientSchema.safeParse({
        first_name: "Ancient",
        mobile_number: "9820098200",
        age: 150,
      });
      expect(res.success).toBe(false);
    });
  });
});
