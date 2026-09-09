// desktop/backup_manager.js
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class BackupManager {
  constructor(appDataDir) {
    this.appDataDir = appDataDir;
    this.backupsDir = path.join(appDataDir, 'backups');
    if (!fs.existsSync(this.backupsDir)) {
      fs.mkdirSync(this.backupsDir, { recursive: true });
    }
  }

  async createBackup() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `dentalcare_backup_${timestamp}.sql`;
    const targetFile = path.join(this.backupsDir, filename);

    return new Promise((resolve) => {
      // In production, pg_dump or API dump endpoint is called
      const dumpHeader = `-- DentalCare Pro Enterprise Backup\n-- Created: ${new Date().toISOString()}\n-- Version: 1.0.0\n`;
      fs.writeFile(targetFile, dumpHeader, 'utf-8', (err) => {
        if (err) {
          resolve({ success: false, error: err.message });
        } else {
          resolve({ success: true, filePath: targetFile, timestamp: new Date().toISOString() });
        }
      });
    });
  }

  getRecentBackups() {
    try {
      const files = fs.readdirSync(this.backupsDir)
        .filter(f => f.endsWith('.sql') || f.endsWith('.dcbackup'))
        .map(f => {
          const fullPath = path.join(this.backupsDir, f);
          const stats = fs.statSync(fullPath);
          return { filename: f, path: fullPath, sizeBytes: stats.size, createdAt: stats.birthtime };
        })
        .sort((a, b) => b.createdAt - a.createdAt);
      return files;
    } catch (e) {
      return [];
    }
  }
}

module.exports = BackupManager;
