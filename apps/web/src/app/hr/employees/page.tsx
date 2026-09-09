"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Users,
  Search,
  Filter,
  Plus,
  ArrowRight,
  ShieldCheck,
  Mail,
  Phone,
  Building,
  CheckCircle2,
  AlertCircle,
  X,
} from "lucide-react";
import { HRNav } from "../nav";
import { Employee, EmployeeStatus, EmploymentType } from "../types";

const mockEmployees: Employee[] = [
  {
    id: "emp-001",
    employee_code: "EMP-1001",
    first_name: "Dr. Ananya",
    last_name: "Shah",
    email: "ananya.shah@dentalcare.com",
    phone: "+91 98201 12345",
    gender: "FEMALE",
    qualification: "MDS (Prosthodontics)",
    specialization: "Prosthodontics",
    license_number: "DCI-MH-44821",
    license_expiry_date: "2027-04-15",
    designation: "Chief Prosthodontist & Clinic Admin",
    employment_type: "FULL_TIME",
    joining_date: "2023-01-10",
    status: "ACTIVE",
    base_salary: 140000,
    created_at: "2023-01-10T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "emp-002",
    employee_code: "EMP-1002",
    first_name: "Dr. Rohan",
    last_name: "Verma",
    email: "rohan.verma@dentalcare.com",
    phone: "+91 98202 23456",
    gender: "MALE",
    qualification: "MDS (Endodontics)",
    specialization: "Endodontics",
    license_number: "DCI-MH-51209",
    license_expiry_date: "2026-10-15", // Expiring soon!
    designation: "Consultant Endodontist",
    employment_type: "FULL_TIME",
    joining_date: "2023-06-15",
    status: "ACTIVE",
    base_salary: 125000,
    created_at: "2023-06-15T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "emp-003",
    employee_code: "EMP-1003",
    first_name: "Dr. Kavita",
    last_name: "Rao",
    email: "kavita.rao@dentalcare.com",
    phone: "+91 98203 34567",
    gender: "FEMALE",
    qualification: "MDS (Orthodontics)",
    specialization: "Orthodontics",
    license_number: "DCI-KA-38102",
    license_expiry_date: "2028-02-28",
    designation: "Roaming Specialist Orthodontist",
    employment_type: "CONSULTANT",
    joining_date: "2024-02-01",
    status: "ACTIVE",
    base_salary: 110000,
    created_at: "2024-02-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "emp-004",
    employee_code: "EMP-1004",
    first_name: "Pooja",
    last_name: "Nair",
    email: "pooja.nair@dentalcare.com",
    phone: "+91 98204 45678",
    gender: "FEMALE",
    qualification: "Diploma in Dental Hygiene",
    specialization: "Preventive Care",
    designation: "Senior Dental Hygienist",
    employment_type: "FULL_TIME",
    joining_date: "2024-05-10",
    status: "ON_LEAVE",
    base_salary: 45000,
    created_at: "2024-05-10T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  {
    id: "emp-005",
    employee_code: "EMP-1005",
    first_name: "Vikram",
    last_name: "Patil",
    email: "vikram.patil@dentalcare.com",
    phone: "+91 98205 56789",
    gender: "MALE",
    qualification: "Certified Dental Assistant (CDA)",
    designation: "Lead Chairside Assistant",
    employment_type: "FULL_TIME",
    joining_date: "2024-08-01",
    status: "ACTIVE",
    base_salary: 38000,
    created_at: "2024-08-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>(mockEmployees);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [showModal, setShowModal] = useState(false);

  // New employee form state
  const [code, setCode] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [designation, setDesignation] = useState("");
  const [specialization, setSpecialization] = useState("General Dentistry");
  const [license, setLicense] = useState("");
  const [salary, setSalary] = useState(60000);

  const filtered = employees.filter((emp) => {
    const matchesSearch =
      `${emp.first_name} ${emp.last_name} ${emp.employee_code} ${emp.designation} ${emp.specialization || ""}`
        .toLowerCase()
        .includes(search.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || emp.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleAddEmployee = (e: React.FormEvent) => {
    e.preventDefault();
    const newEmp: Employee = {
      id: `emp-${Date.now()}`,
      employee_code: code || `EMP-${Math.floor(1000 + Math.random() * 9000)}`,
      first_name: firstName,
      last_name: lastName,
      email,
      gender: "OTHER",
      specialization,
      license_number: license || undefined,
      designation,
      employment_type: "FULL_TIME",
      joining_date: new Date().toISOString().split("T")[0],
      status: "ACTIVE",
      base_salary: salary,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setEmployees([newEmp, ...employees]);
    setShowModal(false);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Staff & Employee Directory</h1>
            <p className="text-sm text-slate-500 mt-1">
              Manage clinical practitioners, dental assistants, hygienists & administrative personnel
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" /> Onboard Employee
          </button>
        </div>

        {/* Search and Filters Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs mb-6 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by name, ID, role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs rounded-lg border border-slate-200 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="ON_LEAVE">On Leave</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
        </div>

        {/* Directory Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Employee ID & Name</th>
                  <th className="py-3 px-4">Designation & Specialty</th>
                  <th className="py-3 px-4">Council License #</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Base Pay</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xs">
                          {emp.first_name[0]}{emp.last_name[0]}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900">
                            {emp.first_name} {emp.last_name}
                          </div>
                          <span className="text-[11px] font-mono text-slate-400">{emp.employee_code}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{emp.designation}</div>
                      <span className="text-[11px] text-teal-600">{emp.specialization || "General"}</span>
                    </td>
                    <td className="py-3 px-4">
                      {emp.license_number ? (
                        <div>
                          <span className="font-mono text-slate-700">{emp.license_number}</span>
                          {emp.license_expiry_date && (
                            <span className="block text-[10px] text-slate-400">
                              Exp: {emp.license_expiry_date}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                        {emp.employment_type.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          emp.status === "ACTIVE"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {emp.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-medium text-slate-900">
                      ₹{emp.base_salary.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/hr/employees/${emp.id}`}
                        className="inline-flex items-center gap-1 text-teal-600 hover:text-teal-700 font-semibold"
                      >
                        Dossier <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal: Onboard Employee */}
        {showModal && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl relative border border-slate-200">
              <button
                onClick={() => setShowModal(false)}
                className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
              <h2 className="text-lg font-bold text-slate-900 mb-4">Onboard New Team Member</h2>
              <form onSubmit={handleAddEmployee} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">First Name</label>
                    <input
                      required
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="e.g. Dr. Rajesh"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Last Name</label>
                    <input
                      required
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="e.g. Sharma"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Email</label>
                    <input
                      required
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="doctor@dentalcare.com"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Badge Code</label>
                    <input
                      type="text"
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="EMP-1006"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Designation</label>
                    <input
                      required
                      type="text"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="e.g. Associate Periodontist"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Specialty</label>
                    <select
                      value={specialization}
                      onChange={(e) => setSpecialization(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                    >
                      <option value="General Dentistry">General Dentistry</option>
                      <option value="Orthodontics">Orthodontics</option>
                      <option value="Endodontics">Endodontics</option>
                      <option value="Prosthodontics">Prosthodontics</option>
                      <option value="Oral Surgery">Oral Surgery</option>
                      <option value="Pedodontics">Pedodontics</option>
                      <option value="Periodontics">Periodontics</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Dental Council Reg #</label>
                    <input
                      type="text"
                      value={license}
                      onChange={(e) => setLicense(e.target.value)}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                      placeholder="e.g. DCI-MH-12345"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Monthly Base Pay (₹)</label>
                    <input
                      required
                      type="number"
                      value={salary}
                      onChange={(e) => setSalary(Number(e.target.value))}
                      className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg font-semibold hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold"
                  >
                    Register Employee
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
