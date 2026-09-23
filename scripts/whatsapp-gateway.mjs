import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  Browsers,
} from "@whiskeysockets/baileys";
import QRCode from "qrcode";
import pino from "pino";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const AUTH_DIR = path.resolve(__dirname, "..", "storage", "whatsapp_auth");
const PORT = Number(process.env.WA_GATEWAY_PORT || 4050);

fs.mkdirSync(AUTH_DIR, { recursive: true });

let sock = null;
let currentStatus = "CONNECTING"; // "CONNECTING" | "QR_READY" | "CONNECTED" | "DISCONNECTED"
let currentQrDataUrl = null;
let connectedUser = null;
let lastError = null;
let isStarting = false;

const logger = pino({ level: "silent" });

async function startWhatsApp() {
  if (isStarting) return;
  isStarting = true;

  try {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    let version = [2, 3000, 1015901307];
    try {
      const latest = await fetchLatestBaileysVersion();
      if (latest?.version) version = latest.version;
    } catch {
      // fallback version
    }

    sock = makeWASocket({
      version,
      auth: state,
      logger,
      printQRInTerminal: false,
      browser: Browsers.windows("DentalCare Pro Clinic"),
      syncFullHistory: false,
      markOnlineOnConnect: false,
    });

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        try {
          currentQrDataUrl = await QRCode.toDataURL(qr, {
            width: 280,
            margin: 2,
            color: { dark: "#0f172a", light: "#ffffff" },
          });
          currentStatus = "QR_READY";
          lastError = null;
        } catch (err) {
          console.error("Failed to generate QR Data URL:", err);
        }
      }

      if (connection === "open") {
        currentStatus = "CONNECTED";
        currentQrDataUrl = null;
        lastError = null;
        connectedUser = {
          id: sock?.user?.id || "",
          name: sock?.user?.name || "Clinic WhatsApp",
        };
        console.log("[WhatsApp Gateway] Connected as:", connectedUser);
      }

      if (connection === "close") {
        const statusCode =
          lastDisconnect?.error?.output?.statusCode ||
          lastDisconnect?.error?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        if (!shouldReconnect) {
          console.log("[WhatsApp Gateway] Logged out. Clearing auth state and restarting...");
          currentStatus = "DISCONNECTED";
          connectedUser = null;
          currentQrDataUrl = null;
          try {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
            fs.mkdirSync(AUTH_DIR, { recursive: true });
          } catch {}
          isStarting = false;
          setTimeout(() => startWhatsApp(), 1500);
        } else {
          currentStatus = "CONNECTING";
          isStarting = false;
          setTimeout(() => startWhatsApp(), 2500);
        }
      }
    });
  } catch (err) {
    console.error("[WhatsApp Gateway] Startup error:", err);
    lastError = String(err?.message || err);
    currentStatus = "DISCONNECTED";
  } finally {
    isStarting = false;
  }
}

function formatWhatsAppJid(rawPhone) {
  let digits = String(rawPhone || "").replace(/[^0-9]/g, "");
  if (digits.startsWith("0") && digits.length === 11) {
    digits = "91" + digits.slice(1);
  } else if (digits.length === 10) {
    digits = "91" + digits;
  }
  return `${digits}@s.whatsapp.net`;
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8");
        resolve(raw ? JSON.parse(raw) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, payload) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  });
  res.end(JSON.stringify(payload));
}

const server = http.createServer(async (req, res) => {
  if (req.method === "OPTIONS") {
    return sendJson(res, 200, { ok: true });
  }

  const url = new URL(req.url || "/", `http://127.0.0.1:${PORT}`);

  if (req.method === "GET" && url.pathname === "/status") {
    return sendJson(res, 200, {
      connected: currentStatus === "CONNECTED",
      status: currentStatus,
      qr_data_url: currentQrDataUrl,
      user: connectedUser,
      error: lastError,
    });
  }

  if (req.method === "POST" && url.pathname === "/pairing-code") {
    try {
      const body = await readJsonBody(req);
      let digits = String(body.phone || "").replace(/[^0-9]/g, "");
      if (digits.length === 10) digits = "91" + digits;
      if (!digits || digits.length < 10) {
        return sendJson(res, 400, { success: false, message: "Valid phone number required" });
      }
      if (!sock) {
        return sendJson(res, 503, { success: false, message: "WhatsApp socket initializing" });
      }
      const code = await sock.requestPairingCode(digits);
      return sendJson(res, 200, { success: true, pairing_code: code, phone: digits });
    } catch (err) {
      return sendJson(res, 500, {
        success: false,
        message: err?.message || "Failed to request pairing code",
      });
    }
  }

  if (req.method === "POST" && url.pathname === "/send-document") {
    try {
      if (currentStatus !== "CONNECTED" || !sock) {
        return sendJson(res, 409, {
          success: false,
          code: "WHATSAPP_NOT_LINKED",
          status: currentStatus,
          qr_data_url: currentQrDataUrl,
          message: "Clinic WhatsApp is not linked yet. Please scan the QR code once to enable direct PDF sending.",
        });
      }

      const body = await readJsonBody(req);
      const { phone, filename, caption, pdf_base64 } = body;

      if (!phone || !pdf_base64) {
        return sendJson(res, 400, {
          success: false,
          message: "phone and pdf_base64 are required",
        });
      }

      let targetJid = formatWhatsAppJid(phone);
      try {
        const results = await sock.onWhatsApp(targetJid.split("@")[0]);
        if (Array.isArray(results) && results.length > 0 && results[0].jid) {
          targetJid = results[0].jid;
        }
      } catch {
        // fallback to formatted JID
      }

      const pdfBuffer = Buffer.from(pdf_base64, "base64");
      const safeFileName = filename || "Patient_Dental_Report.pdf";

      const sent = await sock.sendMessage(targetJid, {
        document: pdfBuffer,
        mimetype: "application/pdf",
        fileName: safeFileName,
        caption: caption || "",
      });

      return sendJson(res, 200, {
        success: true,
        message_id: sent?.key?.id || "sent",
        recipient: targetJid,
        filename: safeFileName,
      });
    } catch (err) {
      console.error("[WhatsApp Gateway] Send Document Error:", err);
      return sendJson(res, 500, {
        success: false,
        message: err?.message || "Failed to send PDF via WhatsApp",
      });
    }
  }

  if (req.method === "POST" && url.pathname === "/logout") {
    try {
      if (sock) {
        await sock.logout();
      }
    } catch {}
    try {
      fs.rmSync(AUTH_DIR, { recursive: true, force: true });
      fs.mkdirSync(AUTH_DIR, { recursive: true });
    } catch {}
    currentStatus = "DISCONNECTED";
    connectedUser = null;
    currentQrDataUrl = null;
    isStarting = false;
    setTimeout(() => startWhatsApp(), 1000);
    return sendJson(res, 200, { success: true });
  }

  return sendJson(res, 404, { error: "Not found" });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`[WhatsApp Gateway] Listening on http://127.0.0.1:${PORT}`);
  startWhatsApp();
});
