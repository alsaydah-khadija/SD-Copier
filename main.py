import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
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
PICTURE_BASE_DIR = Path("D:/Media/Pictures")
VIDEO_BASE_DIR = Path("D:/Media/Videos")

# Common subdirectories where Canon stores media
CANON_MEDIA_SUBDIRS = ["DCIM/100CANON", "DCIM/100EOS_R"]

def get_removable_drives():
    drives = []
    output = subprocess.check_output("wmic logicaldisk get DeviceID, DriveType", shell=True).decode()
    lines = output.strip().split("\n")[1:]
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == '2':  # DriveType 2 = Removable Disk
            device_id = parts[0]
            drives.append(device_id)
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
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    dest_path = dest_dir / f"{dest_path.stem}_{timestamp}{dest_path.suffix}"

                shutil.copy2(source_path, dest_path)
                print(f"Copied {source_path} -> {dest_path}")


def eject_drive(drive_letter):
    subprocess.run(["powershell", "(New-Object -comObject Shell.Application).NameSpace(17).ParseName(\"{}\\\").InvokeVerb(\"Eject\")".format(drive_letter)], shell=True)


def process_cameras(cancel_event=None, progress_callback=None):
    drives = get_removable_drives()
    results = []
    total_bytes = 0
    start_time = time.time()

    for idx, drive in enumerate(drives, start=1):
        base_drive = Path(drive + "/")
        picture_dest = PICTURE_BASE_DIR / f"cam{idx}"
        video_dest = VIDEO_BASE_DIR / f"cam{idx}"

        found = False
        for root, _, files in os.walk(base_drive):
            for file in files:
                if cancel_event and cancel_event.is_set():
                    results.append("Transfer cancelled.")
                    return results
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
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    dest_path = dest_path.parent / f"{dest_path.stem}_{timestamp}{dest_path.suffix}"

                shutil.copy2(source_path, dest_path)
                try:
                    total_bytes += os.path.getsize(source_path)
                except Exception:
                    pass
                found = True

                # Update transfer speed
                if progress_callback:
                    elapsed = time.time() - start_time
                    speed = total_bytes / elapsed if elapsed > 0 else 0
                    progress_callback(speed)

        if found and not (cancel_event and cancel_event.is_set()):
            eject_drive(drive)
            results.append(f"Transferred and ejected cam{idx}.")
        elif not found:
            results.append(f"SD card {idx} found, but no media files detected.")
    if not drives:
        results.append("No SD cards found.")
    return results


def run_gui():
    root = tk.Tk()
    root.title("Camera SD Transfer Tool")
    root.geometry("400x250")

    status_label = tk.Label(root, text="", font=("Arial", 10))
    status_label.pack(pady=5)
    speed_label = tk.Label(root, text="Transfer speed: 0 MB/s", font=("Arial", 10))
    speed_label.pack(pady=5)

    cancel_event = threading.Event()
    transfer_thread = None

    def update_speed(speed):
        speed_label.config(text=f"Transfer speed: {speed/1024/1024:.2f} MB/s")

    def on_transfer():
        status_label.config(text="Transferring...")
        speed_label.config(text="Transfer speed: 0 MB/s")
        cancel_event.clear()
        def task():
            results = process_cameras(cancel_event, update_speed)
            status_label.config(text="\n".join(results))
        nonlocal transfer_thread
        transfer_thread = threading.Thread(target=task)
        transfer_thread.start()

    def on_cancel():
        cancel_event.set()
        status_label.config(text="Cancelling...")

    tk.Label(root, text="Camera SD Transfer Utility", font=("Arial", 16)).pack(pady=10)
    tk.Button(root, text="Start Transfer", command=on_transfer, font=("Arial", 12)).pack(pady=5)
    tk.Button(root, text="Cancel", command=on_cancel, font=("Arial", 12)).pack(pady=5)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
