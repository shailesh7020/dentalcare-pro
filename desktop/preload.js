// desktop/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktopAPI', {
  platform: process.platform,
  version: '1.0.0',
  isDesktop: true,
  // Window controls
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  // Utilities
  createBackup: () => ipcRenderer.invoke('create-backup'),
  openBackupsFolder: () => ipcRenderer.send('open-backups-folder'),
  openLogsFolder: () => ipcRenderer.send('open-logs-folder'),
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  saveSetupConfig: (config) => ipcRenderer.invoke('save-setup-config', config),
  testDbConnection: (config) => ipcRenderer.invoke('test-db-connection', config),
});
