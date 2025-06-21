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

# Supported file extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.cr2', '.cr3', '.nef', '.arw'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}

# Volume labels mapped to camera names
CAMERA_LABELS = {
    "CANONR": "Canon R",
    "CANON90D": "Canon 90D",
    "CANONR8": "Canon R8",
    "CANONR6II": "Canon R6 II"
}

# Target folders
PICTURE_BASE_DIR = Path("C:/Media/Pictures")
VIDEO_BASE_DIR = Path("C:/Media/Videos")


def get_removable_drives():
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


def transfer_sd_card(idx, drive, picture_dest, video_dest, cancel_event, speed_callback, result_callback):
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
            else:
                continue

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if dest_path.exists():
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
        t = threading.Thread(
            target=transfer_sd_card,
            args=(idx, drive, picture_dest, video_dest, cancel_event, speed_callback, result_callback)
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
    root.geometry("600x400")

    status_labels = {}
    speed_labels = {}
    label_frames = []
    checkbox_vars = []
    drive_labels = []

    cancel_event = threading.Event()
    transfer_thread = None

    drives = []
    main_base_dir = tk.StringVar(value="C:/Media")
    picture_base_dir = tk.StringVar(value=str(PICTURE_BASE_DIR))
    video_base_dir = tk.StringVar(value=str(VIDEO_BASE_DIR))

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

    def refresh_drives():
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
            cb = tk.Checkbutton(root, text=label_text, variable=var, font=("Arial", 10))
            cb.pack(anchor='w')
            drive_labels.append(cb)
            checkbox_vars.append(var)

    def speed_callback(idx, speed):
        if idx in speed_labels:
            speed_labels[idx].config(text=f"cam{idx} speed: {speed/1024/1024:.2f} MB/s")

    def result_callback(idx, msg):
        if idx in status_labels:
            status_labels[idx].config(text=f"cam{idx}: {msg}")

    def on_transfer():
        # Remove old labels
        for frame in label_frames:
            frame.destroy()
        status_labels.clear()
        speed_labels.clear()
        label_frames.clear()

        # Get selected drives as (drive, volname) tuples
        selected_drives = [(drive, volname) for var, (drive, volname, _) in zip(checkbox_vars, drives) if var.get()]
        for idx, (drive, volname) in enumerate(selected_drives, start=1):
            frame = tk.Frame(root)
            frame.pack(pady=2)
            label_frames.append(frame)
            label_text = f"cam{idx}: Transferring from {drive} - {volname}" if volname else f"cam{idx}: Transferring from {drive}"
            status_labels[idx] = tk.Label(frame, text=label_text, font=("Arial", 10))
            status_labels[idx].pack(side=tk.LEFT)
            speed_labels[idx] = tk.Label(frame, text=f"cam{idx} speed: 0 MB/s", font=("Arial", 10))
            speed_labels[idx].pack(side=tk.LEFT, padx=10)

        cancel_event.clear()

        def task():
            threads = []
            for idx, (drive, volname) in enumerate(selected_drives, start=1):
                picture_dest = Path(picture_base_dir.get()) / f"cam{idx}"
                video_dest = Path(video_base_dir.get()) / f"cam{idx}"
                t = threading.Thread(
                    target=transfer_sd_card,
                    args=(idx, drive, picture_dest, video_dest, cancel_event, speed_callback, result_callback)
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

    tk.Label(root, text="Camera SD Transfer Utility", font=("Arial", 16)).pack(pady=10)
    # Main folder selection
    main_frame = tk.Frame(root)
    main_frame.pack(pady=2)
    tk.Label(main_frame, text="Main Folder:", font=("Arial", 10)).pack(side=tk.LEFT)
    tk.Entry(main_frame, textvariable=main_base_dir, width=40).pack(side=tk.LEFT, padx=5)
    tk.Button(main_frame, text="Browse", command=browse_main_dir).pack(side=tk.LEFT)
    # Picture folder selection
    pic_frame = tk.Frame(root)
    pic_frame.pack(pady=2)
    tk.Label(pic_frame, text="Pictures Folder:", font=("Arial", 10)).pack(side=tk.LEFT)
    tk.Entry(pic_frame, textvariable=picture_base_dir, width=40).pack(side=tk.LEFT, padx=5)
    tk.Button(pic_frame, text="Browse", command=browse_picture_dir).pack(side=tk.LEFT)
    # Video folder selection
    vid_frame = tk.Frame(root)
    vid_frame.pack(pady=2)
    tk.Label(vid_frame, text="Videos Folder:", font=("Arial", 10)).pack(side=tk.LEFT)
    tk.Entry(vid_frame, textvariable=video_base_dir, width=40).pack(side=tk.LEFT, padx=5)
    tk.Button(vid_frame, text="Browse", command=browse_video_dir).pack(side=tk.LEFT)
    # Drive selection and transfer controls
    tk.Button(root, text="Refresh SD Cards", command=refresh_drives, font=("Arial", 12)).pack(pady=5)
    tk.Button(root, text="Start Transfer", command=on_transfer, font=("Arial", 12)).pack(pady=5)
    tk.Button(root, text="Cancel", command=on_cancel, font=("Arial", 12)).pack(pady=5)

    refresh_drives()
    root.mainloop()


if __name__ == "__main__":
    run_gui()
