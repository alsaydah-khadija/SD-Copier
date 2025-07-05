import os
import threading
import shutil
from datetime import datetime

def remove_all_files_from_sd(
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
):
    # Remove old labels and cards
    for frame in label_frames:
        frame.destroy()
    label_frames.clear()
    for widget in cards_frame.winfo_children():
        widget.destroy()
    status_labels.clear()
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
    import tkinter as tk
    scanning_label = tk.Label(root, text="Scanning files...", font=("Arial", 11, "italic"), fg="blue")
    scanning_label.pack()
    root.update()

    # Scan all drives for files and sizes
    per_drive_stats = []
    global_total_files = 0
    for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
        image_files, _ = scan_media_files(drive, IMAGE_EXTENSIONS)
        video_files, _ = scan_media_files(drive, VIDEO_EXTENSIONS)
        sound_files, _ = scan_media_files(drive, SOUND_EXTENSIONS)
        all_files = image_files + video_files + sound_files
        per_drive_stats.append({
            "files": all_files,
            "total_files": len(all_files),
            "deleted_files": 0,
        })
        global_total_files += len(all_files)

    scanning_label.destroy()

    # --- GLOBAL PROGRESS BAR ---
    if global_progress_bar:
        global_progress_bar.destroy()
    if global_stats_label:
        global_stats_label.destroy()
    global_progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
    global_progress_bar.pack(pady=4)
    global_stats_label = tk.Label(root, text=f"Total: {global_total_files} files to delete", font=("Arial", 10, "bold"))
    global_stats_label.pack()

    # --- PER DRIVE PROGRESS (as horizontal cards) ---
    for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
        card = tk.Frame(cards_frame, bg="#fff", bd=2, relief=tk.RIDGE, padx=10, pady=8)
        card.pack(side=tk.LEFT, padx=8, pady=4)
        label_frames.append(card)
        label_text = f"cam{cam_number}: {drive} - {volname}" if volname else f"cam{cam_number}: {drive}"
        tk.Label(card, text=label_text, font=("Arial", 10, "bold"), bg="#fff", fg="#2d415a").pack(anchor='w')
        size_labels[idx] = tk.Label(card, text=f"Total: {per_drive_stats[idx-1]['total_files']} files", font=("Arial", 9), bg="#fff")
        size_labels[idx].pack(anchor='w')
        transferred_labels[idx] = tk.Label(card, text=f"Deleted: 0 files", font=("Arial", 9), bg="#fff")
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

    # --- REMOVE TASK ---
    def task():
        global_deleted_files = 0

        def update_progress(idx, files_done):
            # Per drive
            total_files = per_drive_stats[idx-1]['total_files']
            percent = (files_done / total_files * 100) if total_files else 0
            progress_bars[idx]['value'] = percent
            percent_labels[idx].config(text=f"{percent:.1f}%")
            transferred_labels[idx].config(text=f"Deleted: {files_done} files")
            file_count_labels[idx].config(text=f"{files_done}/{total_files} files")
            # Global
            nonlocal global_deleted_files
            global_deleted_files = sum(stat['deleted_files'] for stat in per_drive_stats)
            global_percent = (global_deleted_files / global_total_files * 100) if global_total_files else 0
            if global_progress_bar is not None:
                global_progress_bar['value'] = global_percent
            if global_stats_label is not None:
                global_stats_label.config(
                    text=f"Total: {global_deleted_files}/{global_total_files} files deleted ({global_percent:.1f}%)"
                )

        def remove_one(idx, drive, stat, cam_number):
            files_done = 0
            for file_path in stat['files']:
                if cancel_event.is_set():
                    status_labels[idx].config(text="Delete cancelled.")
                    return
                try:
                    os.remove(file_path)
                    stat['deleted_files'] += 1
                except Exception:
                    pass
                files_done += 1
                update_progress(idx, files_done)
            if not cancel_event.is_set():
                eject_drive(drive)
                status_labels[idx].config(text=f"All files deleted and cam{cam_number} ejected.")

        threads = []
        for idx, (drive, volname, cam_number) in enumerate(selected_drives, start=1):
            t = threading.Thread(
                target=remove_one,
                args=(idx, drive, per_drive_stats[idx-1], cam_number)
            )
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        if not selected_drives:
            status_labels[0].config(text="No SD cards selected.")

    threading.Thread(target=task).start()