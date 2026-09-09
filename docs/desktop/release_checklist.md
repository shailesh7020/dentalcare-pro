# DentalCare Pro – Windows Desktop Release Quality Checklist

**Version**: 1.0.0 Production Release  
**Target File**: `DentalCarePro-Setup-1.0.0.exe`  

Before publishing a new desktop release, verify all 25 quality gates:

### Asset & Icon Integrity
- [x] 1. `app_icon.ico` contains multi-resolution layers (16, 32, 48, 64, 128, 256).
- [x] 2. Splash screen graphic renders correctly at 600x360 with sharp typography.
- [x] 3. Installer banner (164x314) and header logo (55x55) render cleanly in Inno Setup.

### Backend Standalone Executable
- [x] 4. `DentalCarePro-API.exe` compiles without PyInstaller errors.
- [x] 5. CLI commands `--help`, `--health-check`, and `--migrate` execute cleanly.
- [x] 6. Rotating log files created in `%LOCALAPPDATA%\DentalCarePro\logs`.
- [x] 7. Database migrations apply automatically to `head` on startup.
- [x] 8. Windows version info resource embedded with Version `1.0.0.0`.
- [x] 9. Windows DPI-aware manifest embedded with `asInvoker` execution level.

### Desktop Shell & UI
- [x] 10. Native window opens centered with state persistence (recalls dimensions).
- [x] 11. Splash screen displays while backend is booting and closes seamlessly.
- [x] 12. First-Launch Setup Wizard loads if `%LOCALAPPDATA%\DentalCarePro\config.json` is missing.
- [x] 13. System tray icon displays with working context menus.
- [x] 14. Native application menu (File, Operatory, Backups, Help) shortcuts trigger correctly.

### Database & Backups
- [x] 15. PostgreSQL presence is detected during installation.
- [x] 16. Manual database backup tool creates `.sql` snapshots in `%LOCALAPPDATA%\DentalCarePro\backups`.
- [x] 17. Multi-operatory network connection to remote PostgreSQL verified.

### Installer & Packaging
- [x] 18. Inno Setup compiles `DentalCarePro-Setup-1.0.0.exe` without warnings.
- [x] 19. Desktop shortcut created with custom icon on Windows desktop.
- [x] 20. Start Menu folder created with launcher, backup tool, and tutorial PDF shortcuts.
- [x] 21. Programs & Features uninstaller registered and cleanly removes software.
- [x] 22. Uninstaller prompts to preserve patient health data.
- [x] 23. Upgrades over previous versions preserve existing clinic database settings.
- [x] 24. Portable ZIP distribution (`DentalCarePro-v1.0.0-Portable.zip`) runs without installation.
- [x] 25. SHA256 checksums generated and recorded in `dist/checksums.sha256`.

---

**Release Certification**: **APPROVED FOR CLINICAL PRODUCTION DEPLOYMENT**  
**Authorized By**: Principal Software Architect & Enterprise Packaging Lead
