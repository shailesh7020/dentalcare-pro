// desktop/main.js
const { app, BrowserWindow, Menu, Tray, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const BackupManager = require('./backup_manager');
const AutoUpdateManager = require('./updater');

const APPDATA_DIR = path.join(process.env.LOCALAPPDATA || app.getPath('appData'), 'DentalCarePro');
const CONFIG_FILE = path.join(APPDATA_DIR, 'config.json');
const LOGS_DIR = path.join(APPDATA_DIR, 'logs');
const STATE_FILE = path.join(APPDATA_DIR, 'window-state.json');

if (!fs.existsSync(LOGS_DIR)) fs.mkdirSync(LOGS_DIR, { recursive: true });

let mainWindow = null;
let splashWindow = null;
let tray = null;
let backendProcess = null;
let backupManager = new BackupManager(APPDATA_DIR);
let updater = new AutoUpdateManager('1.0.0', APPDATA_DIR);

function logSupervisor(message) {
  const line = `[${new Date().toISOString()}] [Supervisor] ${message}\n`;
  try {
    fs.appendFileSync(path.join(LOGS_DIR, 'supervisor.log'), line, 'utf-8');
  } catch (_) {}
}

function checkBackendHealth(port = 8000) {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/api/health`, { timeout: 2000 }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

function launchBackendProcess(port = 8000) {
  logSupervisor('Initiating backend process launch...');
  const rootDir = path.resolve(__dirname, '..');
  const exePath = path.join(rootDir, 'dist', 'backend', 'DentalCarePro-API.exe');

  if (fs.existsSync(exePath)) {
    logSupervisor(`Spawning compiled binary: ${exePath}`);
    backendProcess = spawn(exePath, ['--port', String(port)], {
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });
  } else {
    logSupervisor('Binary not found, launching desktop_entry.py via Python');
    const pyEntry = path.join(rootDir, 'backend', 'desktop_entry.py');
    backendProcess = spawn('python', [pyEntry, '--port', String(port)], {
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });
  }

  backendProcess.stdout.on('data', (data) => logSupervisor(`[stdout] ${data.toString().trim()}`));
  backendProcess.stderr.on('data', (data) => logSupervisor(`[stderr] ${data.toString().trim()}`));

  backendProcess.on('exit', (code, sig) => {
    logSupervisor(`Backend process exited with code ${code}, signal ${sig}`);
  });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 360,
    frame: false,
    resizable: false,
    center: true,
    alwaysOnTop: true,
    transparent: false,
    backgroundColor: '#0f172a',
    icon: path.join(__dirname, '..', 'assets', 'branding', 'app_icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

function getWindowState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    }
  } catch (_) {}
  return { width: 1366, height: 860, isMaximized: false };
}

function saveWindowState() {
  if (!mainWindow) return;
  try {
    const isMax = mainWindow.isMaximized();
    const bounds = mainWindow.getBounds();
    fs.writeFileSync(STATE_FILE, JSON.stringify({ ...bounds, isMaximized: isMax }));
  } catch (_) {}
}

function createMainWindow(targetUrl) {
  const state = getWindowState();

  mainWindow = new BrowserWindow({
    width: state.width,
    height: state.height,
    x: state.x,
    y: state.y,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    title: 'DentalCare Pro — Enterprise Dental Clinic Management',
    icon: path.join(__dirname, '..', 'assets', 'branding', 'app_icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  if (state.isMaximized) {
    mainWindow.maximize();
  }

  mainWindow.loadURL(targetUrl);

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
  });

  mainWindow.on('close', () => {
    saveWindowState();
  });

  setupNativeMenu();
  setupSystemTray();
}

function setupNativeMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        { label: 'New Patient', accelerator: 'Alt+N', click: () => mainWindow.webContents.send('route', '/patients/new') },
        { label: 'Book Appointment', accelerator: 'Alt+B', click: () => mainWindow.webContents.send('route', '/appointments') },
        { type: 'separator' },
        { label: 'Exit DentalCare Pro', accelerator: 'Ctrl+Q', click: () => app.quit() }
      ]
    },
    {
      label: 'Operatory',
      submenu: [
        { label: 'Live Waiting Queue', accelerator: 'Alt+Q', click: () => mainWindow.webContents.send('route', '/appointments/queue') },
        { label: '32-Tooth Odontogram', click: () => mainWindow.webContents.send('route', '/patients') },
        { label: 'Daily Financial Day Sheet', click: () => mainWindow.webContents.send('route', '/billing/reports') },
      ]
    },
    {
      label: 'Database & Backups',
      submenu: [
        {
          label: 'Create Database Backup Now...',
          click: async () => {
            const res = await backupManager.createBackup();
            if (res.success) {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Backup Successful',
                message: `DentalCare Pro backup saved successfully to:\n${res.filePath}`
              });
            } else {
              dialog.showErrorBox('Backup Failed', res.error);
            }
          }
        },
        {
          label: 'Open Backups Folder',
          click: () => shell.openPath(backupManager.backupsDir)
        },
        {
          label: 'View Application Logs',
          click: () => shell.openPath(LOGS_DIR)
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'User Manual & Tutorial (PDF)',
          click: () => {
            const pdfPath = path.resolve(__dirname, '..', 'Project-tutorial.pdf');
            if (fs.existsSync(pdfPath)) shell.openPath(pdfPath);
            else dialog.showMessageBox(mainWindow, { type: 'info', title: 'Tutorial', message: 'Project-tutorial.pdf is available in the installation folder.' });
          }
        },
        {
          label: 'Check for Updates...',
          click: async () => {
            const info = await updater.checkForUpdates();
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'DentalCare Pro Updates',
              message: info.message
            });
          }
        },
        { type: 'separator' },
        {
          label: 'About DentalCare Pro',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About DentalCare Pro',
              message: 'DentalCare Pro Enterprise Edition\nVersion: 1.0.0\nBuilt for Multi-Clinic Networks and DSOs\nHIPAA & GDPR Compliant\nCopyright © 2026 DentalCare Pro Inc.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function setupSystemTray() {
  if (tray) return;
  const iconPath = path.join(__dirname, '..', 'assets', 'branding', 'app_icon.ico');
  if (!fs.existsSync(iconPath)) return;

  tray = new Tray(iconPath);
  tray.setToolTip('DentalCare Pro Enterprise');

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open DentalCare Pro', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { label: 'Live Waiting Queue', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.webContents.send('route', '/appointments/queue'); } } },
    { type: 'separator' },
    { label: 'Create Backup', click: async () => await backupManager.createBackup() },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() }
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) mainWindow.focus();
      else mainWindow.show();
    }
  });
}

// IPC Handlers
ipcMain.handle('create-backup', async () => await backupManager.createBackup());
ipcMain.handle('check-for-updates', async () => await updater.checkForUpdates());
ipcMain.on('open-backups-folder', () => shell.openPath(backupManager.backupsDir));
ipcMain.on('open-logs-folder', () => shell.openPath(LOGS_DIR));

ipcMain.handle('test-db-connection', async (event, config) => {
  // Verifies connection string format
  if (config.databaseUrl && config.databaseUrl.startsWith('postgresql')) {
    return { success: true };
  }
  return { success: false, error: 'Invalid PostgreSQL connection URL' };
});

ipcMain.handle('save-setup-config', async (event, payload) => {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(payload, null, 2), 'utf-8');
    logSupervisor('Setup wizard configuration saved successfully.');
    // Restart backend with new config and transition to main app
    if (backendProcess) backendProcess.kill();
    launchBackendProcess(payload.PORT || 8000);
    setTimeout(() => {
      createMainWindow(`http://127.0.0.1:${payload.PORT || 8000}/`);
    }, 2500);
    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

app.whenReady().then(async () => {
  createSplashWindow();

  // Check if first-launch wizard is required
  const isConfigured = fs.existsSync(CONFIG_FILE);

  let isHealthy = await checkBackendHealth(8000);
  if (!isHealthy) {
    launchBackendProcess(8000);
    let attempts = 0;
    while (!isHealthy && attempts < 15) {
      await new Promise(r => setTimeout(r, 1000));
      isHealthy = await checkBackendHealth(8000);
      attempts++;
    }
  }

  if (!isConfigured) {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    createMainWindow(path.join('file://', __dirname, 'wizard.html'));
  } else {
    createMainWindow('http://localhost:3000');
  }
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    logSupervisor('Terminating backend process on application close...');
    backendProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
