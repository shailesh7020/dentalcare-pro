======================================================================
  DENTALCARE PRO - BACKUP UTILITY & DISASTER RECOVERY REFERENCE
======================================================================

DentalCare Pro incorporates enterprise-grade automated data protection.
This folder provides standalone one-click utilities for clinic backup
and disaster recovery operations.

AUTOMATED DAILY BACKUPS:
  * DentalCare Pro automatically takes a snapshot of your complete clinical
    database every single night at 23:00 (11:00 PM).
  * Backups are saved directly to: C:\DentalCarePro_Backups\
  * Backups are encrypted with AES-256 and protected against corruption.

INCLUDED UTILITIES IN THIS DIRECTORY:

1. take_backup.bat
   - Double-click anytime to immediately take an on-demand clinical backup.
   - Recommended before major year-end accounting closures or hardware upgrades.

2. restore_backup.bat
   - Guided recovery tool to restore your clinic database from any chosen .sql backup.
   - Requires explicit "YES" confirmation to protect against accidental overwrites.

3. verify_integrity.bat
   - Computes and verifies cryptographic SHA-256 checksums of all backup files
     in your backup directory to guarantee zero bit-rot or file corruption.

4. backup_manager.exe
   - Standalone command-line backup engine supporting --backup and --restore flags.

RECOMMENDED CLINIC 3-2-1 BACKUP BEST PRACTICE:
  1. Maintain primary active records in PostgreSQL on your main clinic PC.
  2. Maintain automated daily local backups in C:\DentalCarePro_Backups\.
  3. Weekly Off-Site Transfer: Copy the contents of C:\DentalCarePro_Backups\
     to an encrypted external USB drive or clinic network storage weekly,
     and store the drive in a fireproof clinic safe.

NEED EMERGENCY ASSISTANCE?
  If you have experienced hardware failure or need help migrating to a
  new server computer, contact technical support immediately:
  Email: support@dentalcarepro.com | Toll-Free: 1-800-555-DENT (3368)
