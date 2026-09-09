import { describe, expect, it } from "vitest";
import { z } from "zod";

const MOBILE_REGEX = /^[6-9]\d{9}$/;
const AADHAAR_REGEX = /^\d{12}$/;
const PIN_REGEX = /^\d{6}$/;

const patientValidationSchema = z
  .object({
    first_name: z.string().min(1).max(80),
    last_name: z.string().min(1).max(80),
    gender: z.enum(["FEMALE", "MALE", "NON_BINARY", "PREFER_NOT_TO_SAY"]),
    date_of_birth: z.string().min(1).refine((dob) => new Date(dob) <= new Date(), "DOB cannot be future"),
    mobile_number: z.string().regex(MOBILE_REGEX, "Invalid mobile"),
    alternate_mobile: z.string().regex(MOBILE_REGEX).optional().or(z.literal("")),
    email: z.string().email().optional().or(z.literal("")),
    aadhaar_number: z.string().regex(AADHAAR_REGEX).optional().or(z.literal("")),
    pin_code: z.string().regex(PIN_REGEX).optional().or(z.literal("")),
  })
  .refine((data) => !data.alternate_mobile || data.alternate_mobile !== data.mobile_number, {
    message: "Alternate mobile must differ from primary mobile",
    path: ["alternate_mobile"],
  });

describe("Patient Validation Schema", () => {
  it("validates a compliant patient registration payload", () => {
    const valid = {
      first_name: "Aarav",
      last_name: "Mehta",
      gender: "MALE" as const,
      date_of_birth: "1992-05-15",
      mobile_number: "9876543210",
      alternate_mobile: "8765432109",
      email: "aarav.mehta@example.com",
      aadhaar_number: "123456789012",
      pin_code: "400001",
    };
    const result = patientValidationSchema.safeParse(valid);
    expect(result.success).toBe(true);
  });

  it("rejects invalid Indian mobile numbers", () => {
    const invalidNumbers = [
      "1234567890", // starts with 1
      "5876543210", // starts with 5
      "987654321", // 9 digits
      "98765432100", // 11 digits
      "abcd567890", // non-numeric
    ];
    for (const num of invalidNumbers) {
      const result = patientValidationSchema.safeParse({
        first_name: "Test",
        last_name: "Patient",
        gender: "FEMALE",
        date_of_birth: "1990-01-01",
        mobile_number: num,
      });
      expect(result.success).toBe(false);
    }
  });

  it("rejects future dates of birth", () => {
    const futureDob = "2999-12-31";
    const result = patientValidationSchema.safeParse({
      first_name: "Test",
      last_name: "Patient",
      gender: "FEMALE",
      date_of_birth: futureDob,
      mobile_number: "9876543210",
    });
    expect(result.success).toBe(false);
  });

  it("rejects when alternate mobile equals primary mobile number", () => {
    const result = patientValidationSchema.safeParse({
      first_name: "Test",
      last_name: "Patient",
      gender: "FEMALE",
      date_of_birth: "1990-01-01",
      mobile_number: "9876543210",
      alternate_mobile: "9876543210",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toContain("Alternate mobile must differ");
    }
  });

  it("validates 12-digit Aadhaar number format", () => {
    const invalidAadhaar = "12345678";
    const result = patientValidationSchema.safeParse({
      first_name: "Test",
      last_name: "Patient",
      gender: "FEMALE",
      date_of_birth: "1990-01-01",
      mobile_number: "9876543210",
      aadhaar_number: invalidAadhaar,
    });
    expect(result.success).toBe(false);
  });

  it("validates 6-digit Indian PIN code", () => {
    const invalidPin = "4001";
    const result = patientValidationSchema.safeParse({
      first_name: "Test",
      last_name: "Patient",
      gender: "FEMALE",
      date_of_birth: "1990-01-01",
      mobile_number: "9876543210",
      pin_code: invalidPin,
    });
    expect(result.success).toBe(false);
  });
});
