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
PICTURE_BASE_DIR = Path("C:/Media/Pictures")
VIDEO_BASE_DIR = Path("C:/Media/Videos")


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
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
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

    def refresh_drives():
        nonlocal drives
        drives = get_removable_drives()
        # Remove old checkboxes
        for label in drive_labels:
            label.destroy()
        drive_labels.clear()
        checkbox_vars.clear()
        for idx, drive in enumerate(drives, start=1):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(root, text=f"cam{idx} ({drive})", variable=var, font=("Arial", 10))
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

        selected_drives = [drive for var, drive in zip(checkbox_vars, drives) if var.get()]
        for idx, drive in enumerate(selected_drives, start=1):
            frame = tk.Frame(root)
            frame.pack(pady=2)
            label_frames.append(frame)
            status_labels[idx] = tk.Label(frame, text=f"cam{idx}: Transferring...", font=("Arial", 10))
            status_labels[idx].pack(side=tk.LEFT)
            speed_labels[idx] = tk.Label(frame, text=f"cam{idx} speed: 0 MB/s", font=("Arial", 10))
            speed_labels[idx].pack(side=tk.LEFT, padx=10)

        cancel_event.clear()

        def task():
            threads = []
            for idx, drive in enumerate(selected_drives, start=1):
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
    tk.Button(root, text="Refresh SD Cards", command=refresh_drives, font=("Arial", 12)).pack(pady=5)
    tk.Button(root, text="Start Transfer", command=on_transfer, font=("Arial", 12)).pack(pady=5)
    tk.Button(root, text="Cancel", command=on_cancel, font=("Arial", 12)).pack(pady=5)

    refresh_drives()
    root.mainloop()


if __name__ == "__main__":
    run_gui()
