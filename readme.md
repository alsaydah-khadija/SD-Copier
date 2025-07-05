# SD Copier

**SD Copier** is a modern, user-friendly tool for quickly copying photos, videos, and sound files from multiple SD cards to your computer. It supports parallel transfers, customizable destination folders, automatic file renaming to avoid overwrites, and a clear, emoji-enhanced graphical interface.

---

## Features

- **Automatic SD Card Detection:** Detects all removable SD cards as soon as they are inserted.
- **Parallel Transfers:** Copy from multiple SD cards at the same time for maximum speed.
- **Customizable Folders:** Set your own main, pictures, videos, and sound folders.
- **Dated & Subfolders:** Easily create folders for today’s date or use special subfolders like "Azza" or "Reading".
- **Automatic File Renaming:** Files are renamed with date and hour suffixes to prevent overwriting.
- **Transfer Progress:** See real-time progress and speed for each SD card.
- **Automatic Eject:** SD cards are safely ejected after transfer.
- **Modern GUI:** Clean, emoji-enhanced interface for ease of use.

---

## How to Use

### 1. Run the App

- **Option 1 (Recommended for Windows):**  
  Run the ready-to-use portable version:  
  `dist/main.exe`

- **Option 2:**  
  Run with Python:  
  ```sh
  python main.py
  ```

### 2. Select Folders

- Optionally set the main folder, or use the default.
- You can also set custom Pictures, Videos, and Sound folders.

### 3. Create Dated or Subfolder

- Use the **"Create Today's Folder"** button for a dated folder.
- Use the **Azza/Reading** buttons to create/use a subfolder.

### 4. Insert SD Cards

- The app will list all detected SD cards. Select which ones to copy.

### 5. Start Transfer

- Click **"Start Transfer"** to begin copying. Progress and speed are shown for each card.

### 6. Eject and Done

- SD cards are ejected automatically after transfer.
- Use the **"Open"** button to open the main folder in Explorer.

---

## Making it Portable

You can use [PyInstaller](https://www.pyinstaller.org/) to create a standalone `.exe`:

```sh
pyinstaller --onefile --noconsole main.py
```

The output will be in the `dist` folder. Copy and run on any Windows PC.

---

## Requirements

- Windows 10/11
- Python 3.8+ (if not using the portable `.exe`)
- Standard Windows tools (PowerShell, WMIC)

---

## License

MIT License

---

**Enjoy fast, safe, and organized transfers with SD Copier!**