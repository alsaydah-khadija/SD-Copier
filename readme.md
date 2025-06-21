SD Copier
A modern, user-friendly tool for copying photos and videos from multiple SD cards to your computer, with support for parallel transfers, customizable destination folders, and automatic file renaming.

Features
Detects all removable SD cards automatically
Parallel transfer from multiple SD cards
Customizable main, pictures, and videos folders
Option to create a dated folder or subfolders (e.g., Azza, Reading)
File renaming with date and hour suffix to avoid overwrites
Shows transfer speed for each card
Ejects SD cards after transfer
Modern, emoji-enhanced GUI
How to Use
Run the App

Double-click the executable (if using the portable version) or run python main.py.
Select Folders

Optionally set the main folder, or use the default.
You can also set custom Pictures and Videos folders.
(Optional) Create Dated or Subfolder

Use the "Create Today's Folder" button for a dated folder.
Use the Azza/Reading buttons to create/use a subfolder.
Insert SD Cards

The app will list all detected SD cards. Select which ones to copy.
Start Transfer

Click "Start Transfer" to begin copying. Progress and speed are shown for each card.
Eject and Done

SD cards are ejected automatically after transfer.
Use the "Open" button to open the main folder in Explorer.
Making it Portable
Use PyInstaller to create a standalone .exe:
The output will be in the dist folder. Copy and run on any Windows PC.
Requirements
Windows 10/11
Python 3.8+ (if not using the portable .exe)
Standard Windows tools (PowerShell, WMIC)
License
MIT License