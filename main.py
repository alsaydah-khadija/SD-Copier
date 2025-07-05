import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import threading
import time
import queue
import tkinter.ttk as ttk
from PIL import Image, ImageTk 
from remove_sd_files import remove_all_files_from_sd
# Supported file extensions
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.cr2', '.cr3', '.nef', '.arw', '.raw', '.tif', '.tiff', '.heif', '.heic'
}
VIDEO_EXTENSIONS = {
    '.mp4', '.mov', '.avi', '.mkv', '.mxf', '.mts', '.hevc'
}
SOUND_EXTENSIONS = {
    '.wav', '.mp3', '.aac', '.flac', '.ogg', '.m4a'
}

# Volume labels mapped to camera names
CAMERA_LABELS = {
    "CANONR": "Canon R",
    "CANON90D": "Canon 90D",
    "CANONR8": "Canon R8",
    "CANONR6II": "Canon R6 II"
}
global_progress_bar = None
global_stats_label = None
# Target folders
PICTURE_BASE_DIR = Path("C:/Media/Pictures")
VIDEO_BASE_DIR = Path("C:/Media/Videos")
SOUND_BASE_DIR = Path("C:/Media/Sound")
test_mode_env = False

def get_removable_drives(test_mode=False):
    """
    Returns a list of removable drives.
    If test_mode is True, returns 4 sample SD cards for interface testing.
    """
    if test_mode:
        # Return 4 fake SD cards for testing the interface
        return [
            ("E:", "CANONR", "32.0 GB (used: 10.0 GB)"),
            ("F:", "CANON90D", "64.0 GB (used: 20.0 GB)"),
            ("G:", "CANONR8", "128.0 GB (used: 50.0 GB)"),
            ("H:", "CANONR6II", "256.0 GB (used: 100.0 GB)"),
        ]
    drives = []
    output = subprocess.check_output(
        'wmic logicaldisk get DeviceID,DriveType,Size,VolumeName', shell=True
    ).decode(errors='ignore')
    lines = output.strip().split("\n")
    if len(lines) < 2:
        return drives
    for line in lines[1:]:
        if not line.strip():
            continue
        # Split by whitespace, but VolumeName may be missing or have spaces, so handle carefully
        parts = line.split()
        if len(parts) < 2:
            continue
        device_id = parts[0]
        drive_type = parts[1]
        size_str = parts[2] if len(parts) > 2 and parts[2].isdigit() else ""
        # VolumeName is everything after Size (may be empty)
        volume_name = ""
        if len(parts) > 3:
            volume_name = " ".join(parts[3:])
        elif len(parts) == 3 and not parts[2].isdigit():
            volume_name = parts[2]
            size_str = ""
        if drive_type != '2':
            continue
        try:
            total, used, free = shutil.disk_usage(device_id + "\\")
            size_gb = total / (1024 ** 3)
            used_gb = used / (1024 ** 3)
            size_display = f"{size_gb:.1f} GB (used: {used_gb:.1f} GB)"
        except Exception:
            size_display = "Unknown"
        drives.append((device_id, volume_name, size_display))
    return drives


def transfer_files(source_dir: Path, dest_dir: Path, extensions: set):
    for root, _, files in os.walk(source_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in extensions:
                source_path = Path(root) / file
                dest_path = dest_dir / file

                dest_path.parent.mkdir(parents=True, exist_ok=True)

                if dest_path.exists():
                    timestamp = datetime.now().strftime("%d-%m-%Y-%H")
                    dest_path = dest_path.parent / f"{dest_path.stem}_{timestamp}{dest_path.suffix}"

                shutil.copy2(source_path, dest_path)
                print(f"Copied {source_path} -> {dest_path}")


def eject_drive(drive_letter):
    # Try PowerShell method first
    try:
        result = subprocess.run(
            ["powershell", "-Command", f"(New-Object -comObject Shell.Application).NameSpace(17).ParseName('{drive_letter}\\').InvokeVerb('Eject')"],
            shell=True, capture_output=True
        )
        # If PowerShell method fails, try mountvol as fallback
        if result.returncode != 0:
            subprocess.run(f"mountvol {drive_letter}: /p", shell=True)
    except Exception as e:
        # As a last resort, try mountvol
        try:
            subprocess.run(f"mountvol {drive_letter}: /p", shell=True)
        except Exception:
            pass


def scan_media_files(drive, extensions):
    """Scan drive for files with given extensions. Returns (file_list, total_size_bytes)."""
    file_list = []
    total_size = 0
    for root, _, files in os.walk(Path(drive + "/")):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in extensions:
                path = Path(root) / file
                file_list.append(path)
                try:
                    total_size += os.path.getsize(path)
                except Exception:
                    pass
    return file_list, total_size


def format_size(num_bytes):
    if num_bytes >= 1024**3:
        return f"{num_bytes/1024**3:.2f} GB"
    elif num_bytes >= 1024**2:
        return f"{num_bytes/1024**2:.2f} MB"
    elif num_bytes >= 1024:
        return f"{num_bytes/1024:.2f} KB"
    else:
        return f"{num_bytes} B"


def transfer_sd_card(idx, drive, picture_dest, video_dest,sound_dest, cancel_event, speed_callback, result_callback):
    total_bytes = 0
    start_time = time.time()
    found = False
    for root, _, files in os.walk(Path(drive + "/")):
        for file in files:
            if cancel_event.is_set():
                result_callback(idx, "Transfer cancelled.")
                return
            ext = Path(file).suffix.lower()
            source_path = Path(root) / file
            if ext in IMAGE_EXTENSIONS:
                dest_path = picture_dest / file
            elif ext in VIDEO_EXTENSIONS:
                dest_path = video_dest / file
            elif ext in SOUND_EXTENSIONS:
                dest_path = sound_dest / file
            else:
                continue

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            # Always add date-hour suffix to filename
            timestamp = datetime.now().strftime("%d-%m-%Y-%H")
            dest_path = dest_path.parent / f"{dest_path.stem}_{timestamp}{dest_path.suffix}"

            shutil.copy2(source_path, dest_path)
            try:
                total_bytes += os.path.getsize(source_path)
            except Exception:
                pass
            found = True

            # Update transfer speed
            elapsed = time.time() - start_time
            speed = total_bytes / elapsed if elapsed > 0 else 0
            speed_callback(idx, speed)

    if found and not cancel_event.is_set():
        eject_drive(drive)
        result_callback(idx, f"Transferred and ejected cam{idx}.")
    elif not found:
        result_callback(idx, f"SD card {idx} found, but no media files detected.")


def process_cameras_parallel(cancel_event, speed_callback, result_callback):
    drives = get_removable_drives()
    threads = []
    for idx, drive in enumerate(drives, start=1):
        picture_dest = PICTURE_BASE_DIR / f"cam{idx}"
        video_dest = VIDEO_BASE_DIR / f"cam{idx}"
        sound_dest = SOUND_BASE_DIR / f"cam{idx}"
        t = threading.Thread(
            target=transfer_sd_card,
            args=(idx, drive, picture_dest, video_dest, sound_dest,cancel_event, speed_callback, result_callback)
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    if not drives:
        result_callback(0, "No SD cards found.")


def run_gui():
    root = tk.Tk()
    root.title("Camera SD Transfer Tool")
    root.geometry("800x800")  # Increased window size
    root.configure(bg="#f4f6fa")
    style_font = ("Segoe UI", 12)
    label_font = ("Segoe UI", 11, "bold")
    entry_font = ("Segoe UI", 11)
    button_font = ("Segoe UI", 11, "bold")
    pad = {'padx': 8, 'pady': 6}

    # --- Add Logo on Top Right ---
    top_frame = tk.Frame(root, bg="#f4f6fa")
    top_frame.pack(fill=tk.X, pady=(8, 0))

    tk.Label(top_frame, text="📸 Camera SD Transfer Utility", font=("Segoe UI", 18, "bold"), bg="#f4f6fa", fg="#2d415a").pack(side=tk.LEFT, padx=12)

    # Load and display the logo image on the top right
    try:
        import sys
        import os

        if getattr(sys, 'frozen', False):
            # Running in a bundle
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        else:
            # Running in normal Python
            base_path = os.path.abspath(".")

        logo_path = os.path.join(base_path, "assets", "logo.jpg")
        logo_img = Image.open(logo_path)
        logo_img = logo_img.resize((64, 64), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(top_frame, image=logo_photo, bg="#f4f6fa")
        logo_label.image = logo_photo  # Keep a reference
        logo_label.pack(side=tk.RIGHT, padx=12)
    except Exception as e:
        print("Logo not found or failed to load:", e)

    status_labels = {}
    speed_labels = {}
    label_frames = []
    checkbox_vars = []
    drive_labels = []

    progress_bars = {}
    file_count_labels = {}
    size_labels = {}
    transferred_labels = {}
    percent_labels = {}

    global_progress_bar = None
    global_stats_label = None

    cancel_event = threading.Event()
    transfer_thread = None

    drives = []
    cam_drive_map = []  # <-- Use this instead of root.cam_drive_map
    main_base_dir = tk.StringVar(value="C:/Media")
    picture_base_dir = tk.StringVar(value=str(PICTURE_BASE_DIR))
    video_base_dir = tk.StringVar(value=str(VIDEO_BASE_DIR))
    sound_base_dir = tk.StringVar(value=str(SOUND_BASE_DIR))
    azza_reading_var = tk.StringVar(value="")

    def browse_main_dir():
        folder = filedialog.askdirectory(title="Select Main Base Directory")
        if folder:
            main_base_dir.set(folder)
            picture_base_dir.set(str(Path(folder) / "Pictures"))
            video_base_dir.set(str(Path(folder) / "Videos"))

    def browse_picture_dir():
        folder = filedialog.askdirectory(title="Select Picture Base Directory")
        if folder:
            picture_base_dir.set(folder)

    def browse_video_dir():
        folder = filedialog.askdirectory(title="Select Video Base Directory")
        if folder:
            video_base_dir.set(folder)

    def browse_sound_dir():
        folder = filedialog.askdirectory(title="Select Sound Base Directory")
        if folder:
            sound_base_dir.set(folder)

    def refresh_drives_root():
        nonlocal drives
        drives = get_removable_drives()
        # Remove old checkboxes
        for label in drive_labels:
            label.destroy()
        drive_labels.clear()
        checkbox_vars.clear()
        for idx, (drive, volname, size_display) in enumerate(drives, start=1):
            var = tk.BooleanVar(value=True)
            label_text = f"cam{idx} ({drive} - {volname} - {size_display})" if volname else f"cam{idx} ({drive} - {size_display})"
            cb = tk.Checkbutton(root, text=label_text, variable=var, font=entry_font, bg="#f4f6fa")
            cb.pack(anchor='w', padx=10)
            drive_labels.append(cb)
            checkbox_vars.append(var)

    def speed_callback(idx, speed):
        if idx in speed_labels:
            speed_labels[idx].config(text=f"cam{idx} speed: {speed/1024/1024:.2f} MB/s")

    def result_callback(idx, msg):
        if idx in status_labels:
            status_labels[idx].config(text=f"cam{idx}: {msg}")

    def get_unique_cam_folder(base_dir, prefix="cam"):
        """
        Returns a unique cam folder path (e.g., cam1, cam2, ...) under base_dir.
        """
        n = 1
        while True:
            folder = Path(base_dir) / f"{prefix}{n}"
            if not folder.exists():
                return folder, n
            n += 1

    def refresh_drives_frame():
        nonlocal drives, cam_drive_map
        drives = get_removable_drives(test_mode=test_mode_env)
        for label in drive_labels:
            label.destroy()
        drive_labels.clear()
        checkbox_vars.clear()
        cam_drive_map.clear()
        # Use unique cam numbers for each drive
        used_cam_numbers = set()
        for drive, volname, size_display in drives:
            n = 1
            while n in used_cam_numbers or (Path(picture_base_dir.get()) / f"cam{n}").exists() or (Path(video_base_dir.get()) / f"cam{n}").exists():
                n += 1
            used_cam_numbers.add(n)
            label_text = f"cam{n} ({drive} - {volname} - {size_display})" if volname else f"cam{n} ({drive} - {size_display})"
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(drives_frame, text=label_text, variable=var, font=entry_font, bg="#f4f6fa")
            cb.pack(anchor='w', padx=10)
            drive_labels.append(cb)
            checkbox_vars.append(var)
            cam_drive_map.append((drive, volname, n))  # Store mapping for transfer

    def on_transfer():
        nonlocal cam_drive_map
        global global_progress_bar, global_stats_label
        # Remove old labels and cards
        for frame in label_frames:
            frame.destroy()
        label_frames.clear()
        for widget in cards_frame.winfo_children():
            widget.destroy()
        status_labels.clear()
        speed_labels.clear()
        progress_bars.clear()
        file_count_labels.clear()
        size_labels.clear()
        transferred_labels.clear()
        percent_labels.clear()

        # Get selected drives as (drive, volname, cam_number) tuples
        selected_drives = [
            (drive, volname, cam_number)
            for var, (drive, volname, cam_number) in zip(checkbox_vars, cam_drive_map)
            if var.get()
        ]

        # --- SCANNING INDICATOR ---
        scanning_label = tk.Label(root, text="Scanning files...", font=("Arial", 11, "italic"), fg="blue")
        scanning_label.pack()
        root.update()

        # Scan all drives for files and sizes
        per_drive_stats = []
        global_total_files = 0
        global_total_bytes = 0
        for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
            image_files, image_bytes = scan_media_files(drive, IMAGE_EXTENSIONS)
            video_files, video_bytes = scan_media_files(drive, VIDEO_EXTENSIONS)
            sound_files, sound_bytes = scan_media_files(drive, SOUND_EXTENSIONS)
            all_files = image_files + video_files + sound_files
            total_bytes = image_bytes + video_bytes + sound_bytes
            per_drive_stats.append({
                "files": all_files,
                "total_files": len(all_files),
                "total_bytes": total_bytes,
                "transferred_files": 0,
                "transferred_bytes": 0,
            })
            global_total_files += len(all_files)
            global_total_bytes += total_bytes

        scanning_label.destroy()

        # --- GLOBAL PROGRESS BAR ---
        global global_progress_bar, global_stats_label
        if global_progress_bar:
            global_progress_bar.destroy()
        if global_stats_label:
            global_stats_label.destroy()
        global_progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
        global_progress_bar.pack(pady=4)
        global_stats_label = tk.Label(root, text=f"Total: {global_total_files} files, {format_size(global_total_bytes)}", font=("Arial", 10, "bold"))
        global_stats_label.pack()

        # --- PER DRIVE PROGRESS (as horizontal cards) ---
        for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
            card = tk.Frame(cards_frame, bg="#fff", bd=2, relief=tk.RIDGE, padx=10, pady=8)
            card.pack(side=tk.LEFT, padx=8, pady=4)
            label_frames.append(card)
            label_text = f"cam{cam_number}: {drive} - {volname}" if volname else f"cam{cam_number}: {drive}"
            tk.Label(card, text=label_text, font=("Arial", 10, "bold"), bg="#fff", fg="#2d415a").pack(anchor='w')
            speed_labels[idx] = tk.Label(card, text=f"Speed: 0 MB/s", font=("Arial", 9), bg="#fff")
            speed_labels[idx].pack(anchor='w')
            size_labels[idx] = tk.Label(card, text=f"Total: {per_drive_stats[idx-1]['total_files']} files, {format_size(per_drive_stats[idx-1]['total_bytes'])}", font=("Arial", 9), bg="#fff")
            size_labels[idx].pack(anchor='w')
            transferred_labels[idx] = tk.Label(card, text=f"Transferred: 0 files, 0 MB", font=("Arial", 9), bg="#fff")
            transferred_labels[idx].pack(anchor='w')
            percent_labels[idx] = tk.Label(card, text="0%", font=("Arial", 9), bg="#fff")
            percent_labels[idx].pack(anchor='w')
            pb = ttk.Progressbar(card, length=160, mode='determinate')
            pb.pack(anchor='w', pady=(2, 0))
            progress_bars[idx] = pb
            file_count_labels[idx] = tk.Label(card, text="0/0 files", font=("Arial", 9), bg="#fff")
            file_count_labels[idx].pack(anchor='w')
            status_labels[idx] = tk.Label(card, text="", font=("Arial", 9, "italic"), bg="#fff", fg="#64748b")
            status_labels[idx].pack(anchor='w')

        cancel_event.clear()

        # --- TRANSFER TASK ---
        def task():
            global_transferred_files = 0
            global_transferred_bytes = 0

            def update_progress(idx, files_done, bytes_done):
                # Per drive
                total_files = per_drive_stats[idx-1]['total_files']
                total_bytes = per_drive_stats[idx-1]['total_bytes']
                percent = (bytes_done / total_bytes * 100) if total_bytes else 0
                progress_bars[idx]['value'] = percent
                percent_labels[idx].config(text=f"{percent:.1f}%")
                transferred_labels[idx].config(text=f"Transferred: {files_done} files, {format_size(bytes_done)}")
                file_count_labels[idx].config(text=f"{files_done}/{total_files} files")
                # Global
                nonlocal global_transferred_files, global_transferred_bytes
                global_transferred_files = sum(stat['transferred_files'] for stat in per_drive_stats)
                global_transferred_bytes = sum(stat['transferred_bytes'] for stat in per_drive_stats)
                global_percent = (global_transferred_bytes / global_total_bytes * 100) if global_total_bytes else 0
                if global_progress_bar is not None:
                    global_progress_bar['value'] = global_percent
                if global_stats_label is not None:
                    global_stats_label.config(
                        text=f"Total: {global_transferred_files}/{global_total_files} files, {format_size(global_transferred_bytes)}/{format_size(global_total_bytes)} ({global_percent:.1f}%)"
                    )

            def transfer_one(idx, drive, picture_dest, video_dest, sound_dest, stat, cam_number):
                total_bytes = 0
                files_done = 0
                start_time = time.time()
                for file_path in stat['files']:
                    if cancel_event.is_set():
                        result_callback(idx, "Transfer cancelled.")
                        return
                    ext = file_path.suffix.lower()
                    if ext in IMAGE_EXTENSIONS:
                        dest_path = picture_dest / file_path.name
                    elif ext in VIDEO_EXTENSIONS:
                        dest_path = video_dest / file_path.name
                    elif ext in SOUND_EXTENSIONS:
                        dest_path = sound_dest / file_path.name
                    else:
                        continue
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%d-%m-%Y-%H")
                    dest_path = dest_path.parent / f"{dest_path.stem}_{timestamp}{dest_path.suffix}"
                    shutil.copy2(file_path, dest_path)
                    try:
                        size = os.path.getsize(file_path)
                        total_bytes += size
                        stat['transferred_bytes'] += size
                        stat['transferred_files'] += 1
                    except Exception:
                        pass
                    files_done += 1
                    # Update transfer speed
                    elapsed = time.time() - start_time
                    speed = total_bytes / elapsed if elapsed > 0 else 0
                    speed_callback(idx, speed)
                    update_progress(idx, files_done, stat['transferred_bytes'])
                if not cancel_event.is_set():
                    eject_drive(drive)
                    result_callback(idx, f"Transferred and ejected cam{cam_number}.")

            threads = []
            for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
                picture_dest = Path(picture_base_dir.get()) / f"cam{cam_number}"
                video_dest = Path(video_base_dir.get()) / f"cam{cam_number}"
                sound_dest = Path(sound_base_dir.get()) / f"cam{cam_number}"
                t = threading.Thread(
                    target=transfer_one,
                    args=(idx, drive, picture_dest, video_dest, sound_dest, per_drive_stats[idx-1], cam_number)
                )
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            if not selected_drives:
                result_callback(0, "No SD cards selected.")

        nonlocal transfer_thread
        transfer_thread = threading.Thread(target=task)
        transfer_thread.start()

    def on_cancel():
        cancel_event.set()
        for idx in status_labels:
            status_labels[idx].config(text=f"cam{idx}: Cancelling...")

    def create_today_folder():
        today_str = datetime.now().strftime("%d-%m-%Y")
        folder = filedialog.askdirectory(title="Select Parent Directory for Today's Folder")
        if folder:
            today_folder = Path(folder) / today_str
            today_folder.mkdir(parents=True, exist_ok=True)
            main_base_dir.set(str(today_folder))
            picture_base_dir.set(str(today_folder / "Pictures"))
            video_base_dir.set(str(today_folder / "Videos"))
            sound_base_dir.set(str(today_folder / "Sound"))

    def set_azza():
        base = Path(main_base_dir.get())
        # If already ends with 'Azza', do nothing
        if base.name == "Azza":
            return
        # If ends with 'Reading', replace with 'Azza'
        if base.name == "Reading":
            base = base.parent / "Azza"
        else:
            base = base / "Azza"
        base.mkdir(parents=True, exist_ok=True)
        main_base_dir.set(str(base))
        picture_base_dir.set(str(base / "Pictures"))
        video_base_dir.set(str(base / "Videos"))
        sound_base_dir.set(str(base / "Sound"))
        azza_reading_var.set("Azza")

    def set_reading():
        base = Path(main_base_dir.get())
        # If already ends with 'Reading', do nothing
        if base.name == "Reading":
            return
        # If ends with 'Azza', replace with 'Reading'
        if base.name == "Azza":
            base = base.parent / "Reading"
        else:
            base = base / "Reading"
        base.mkdir(parents=True, exist_ok=True)
        main_base_dir.set(str(base))
        picture_base_dir.set(str(base / "Pictures"))
        video_base_dir.set(str(base / "Videos"))
        sound_base_dir.set(str(base / "Sound"))
        azza_reading_var.set("Reading")

    def open_main_folder():
        folder = main_base_dir.get()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showerror("Error", f"Folder does not exist: {folder}")


    # Azza/Reading selection
    azza_reading_frame = tk.Frame(root, bg="#f4f6fa")
    azza_reading_frame.pack(pady=2)
    tk.Label(azza_reading_frame, text="Choose Subfolder:", font=label_font, bg="#f4f6fa").pack(side=tk.LEFT)
    tk.Button(azza_reading_frame, text="🟣 Azza", command=set_azza, font=button_font, bg="#e0e7ff", fg="#3b0764", relief=tk.GROOVE).pack(side=tk.LEFT, padx=5)
    tk.Button(azza_reading_frame, text="🟢 Reading", command=set_reading, font=button_font, bg="#d1fae5", fg="#065f46", relief=tk.GROOVE).pack(side=tk.LEFT, padx=5)

    # Main folder selection
    main_frame = tk.Frame(root, bg="#f4f6fa")
    main_frame.pack(pady=2, fill=tk.X)
    tk.Label(main_frame, text="📁 Main Folder:", font=label_font, bg="#f4f6fa").pack(side=tk.LEFT)
    tk.Entry(main_frame, textvariable=main_base_dir, width=36, font=entry_font).pack(side=tk.LEFT, padx=5)
    tk.Button(main_frame, text="Browse", command=browse_main_dir, font=button_font, bg="#e0e7ff").pack(side=tk.LEFT)
    tk.Button(main_frame, text="Create Today's Folder", command=create_today_folder, font=button_font, bg="#fef9c3").pack(side=tk.LEFT, padx=5)
    tk.Button(main_frame, text="Open", command=open_main_folder, font=button_font, bg="#bae6fd").pack(side=tk.LEFT, padx=5)

    # Picture folder selection
    pic_frame = tk.Frame(root, bg="#f4f6fa")
    pic_frame.pack(pady=2, fill=tk.X)
    tk.Label(pic_frame, text="🖼️ Pictures Folder:", font=label_font, bg="#f4f6fa").pack(side=tk.LEFT)
    tk.Entry(pic_frame, textvariable=picture_base_dir, width=36, font=entry_font).pack(side=tk.LEFT, padx=5)
    tk.Button(pic_frame, text="Browse", command=browse_picture_dir, font=button_font, bg="#e0e7ff").pack(side=tk.LEFT)

    # Video folder selection
    vid_frame = tk.Frame(root, bg="#f4f6fa")
    vid_frame.pack(pady=2, fill=tk.X)
    tk.Label(vid_frame, text="🎬 Videos Folder:", font=label_font, bg="#f4f6fa").pack(side=tk.LEFT)
    tk.Entry(vid_frame, textvariable=video_base_dir, width=36, font=entry_font).pack(side=tk.LEFT, padx=5)
    tk.Button(vid_frame, text="Browse", command=browse_video_dir, font=button_font, bg="#e0e7ff").pack(side=tk.LEFT)

    # Sound folder selection
    sound_frame = tk.Frame(root, bg="#f4f6fa")
    sound_frame.pack(pady=2, fill=tk.X)
    tk.Label(sound_frame, text="🔊 Sound Folder:", font=label_font, bg="#f4f6fa").pack(side=tk.LEFT)
    tk.Entry(sound_frame, textvariable=sound_base_dir, width=36, font=entry_font).pack(side=tk.LEFT, padx=5)
    tk.Button(sound_frame, text="Browse", command=browse_sound_dir, font=button_font, bg="#e0e7ff").pack(side=tk.LEFT)

    # Drive selection and transfer controls
    drives_frame = tk.LabelFrame(root, text="Select SD Cards to Transfer", font=label_font, bg="#f4f6fa", fg="#2d415a", bd=2, relief=tk.GROOVE)
    drives_frame.pack(pady=10, fill=tk.X, padx=10)

    # --- Add Uncheck All Button (moved and styled) ---
    def uncheck_all_sd_cards():
        for var in checkbox_vars:
            var.set(False)

    # Place Uncheck All button at the top of drives_frame
    uncheck_btn = tk.Button(
        drives_frame,
        text="Uncheck All",
        command=uncheck_all_sd_cards,
        font=button_font,
        bg="#fca5a5",  # Light red for visibility
        fg="#7f1d1d",  # Dark red text
        relief=tk.RAISED,
        bd=2,
        padx=10,
        pady=2
    )
    uncheck_btn.pack(anchor='e', pady=(4, 2), padx=8)



    # --- Bottom Buttons in a Horizontal Frame ---
    bottom_btn_frame = tk.Frame(root, bg="#f4f6fa")
    bottom_btn_frame.pack(pady=5)

    tk.Button(
        bottom_btn_frame,
        text="🔄 Refresh SD Cards",
        command=refresh_drives_frame,
        font=button_font,
        bg="#fef9c3"
    ).pack(side=tk.LEFT, padx=6)

    tk.Button(
        bottom_btn_frame,
        text="🚀 Start Transfer",
        command=on_transfer,
        font=button_font,
        bg="#bbf7d0"
    ).pack(side=tk.LEFT, padx=6)

    tk.Button(
        bottom_btn_frame,
        text="⏹️ Cancel",
        command=on_cancel,
        font=button_font,
        bg="#fecaca"
    ).pack(side=tk.LEFT, padx=6)

    tk.Button(
        bottom_btn_frame,
        text="🗑️ Remove All Files from SD Cards",
        command=lambda: remove_all_files_from_sd(
            root,
            cards_frame,
            label_frames,
            status_labels,
            progress_bars,
            file_count_labels,
            size_labels,
            transferred_labels,
            percent_labels,
            checkbox_vars,
            cam_drive_map,
            scan_media_files,
            IMAGE_EXTENSIONS,
            VIDEO_EXTENSIONS,
            SOUND_EXTENSIONS,
            cancel_event,
            eject_drive,
            global_progress_bar,
            global_stats_label,
            ttk
        ),
        font=button_font,
        bg="#fee2e2",
        fg="#b91c1c"
    ).pack(side=tk.LEFT, padx=6)

    # --- Horizontal SD Card Progress Cards with Scrollbar ---
    # Create a canvas with a horizontal scrollbar for SD card progress cards
    cards_canvas = tk.Canvas(root, bg="#f4f6fa", highlightthickness=0, height=170)
    cards_scrollbar = tk.Scrollbar(root, orient="horizontal", command=cards_canvas.xview)
    cards_canvas.configure(xscrollcommand=cards_scrollbar.set)
    cards_canvas.pack(fill=tk.X, padx=10, pady=(0, 8))
    cards_scrollbar.pack(fill=tk.X, padx=10, pady=(0, 8))

    # Frame inside the canvas to hold the SD card progress cards
    cards_frame = tk.Frame(cards_canvas, bg="#f4f6fa")
    cards_canvas.create_window((0, 0), window=cards_frame, anchor="nw")

    def update_cards_scrollregion(event=None):
        cards_canvas.configure(scrollregion=cards_canvas.bbox("all"))

    cards_frame.bind("<Configure>", update_cards_scrollregion)

    refresh_drives_frame()

    # --- Footer ---
    footer = tk.Label(
        root,
        text="Prepared By S.Khadeeja Dev Team",
        font=("Segoe UI", 10, "italic"),
        bg="#f4f6fa",
        fg="#64748b"
    )
    footer.pack(side=tk.BOTTOM, pady=6)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
