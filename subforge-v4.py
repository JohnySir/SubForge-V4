import sys
import logging
import subprocess
import threading
import queue
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# --- GUI Libraries ---
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

# --- Configuration ---
CONFIG = {
    'VIDEO_EXTENSIONS': ['.mp4', '.mkv', '.avi', '.mov'],
    'SUBTITLE_EXTENSION': '.srt',
    'MKVMERGE_PATH': r'C:\Program Files\MKVToolNix\mkvmerge.exe',
    'OUTPUT_SUFFIX': '_subbed',
    'DEFAULT_OUTPUT_FOLDER': '',  # If empty, saves in video folder
    'MAX_PARALLEL_TASKS': 4,
}

# --- Set up live logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)

# ====================================================
# Core Logic
# ====================================================

def detect_subtitle_type(file_path):
    """
    Advanced SDH detection logic.
    Identifies if a subtitle is SDH (Hard of Hearing) or Normal.
    """
    re_sdh_brackets = re.compile(r'[\[\(].*?[\]\)]')
    re_music = re.compile(r'[♪♫#]')
    re_speaker = re.compile(r'^[A-Z]{2,}(\s+[A-Z]{2,})*\s*:', re.MULTILINE)
    re_html = re.compile(r'<[^>]+>')
    
    sdh_points = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Remove HTML tags before analysis
            clean_content = re_html.sub('', content)
            
            # 1. Brackets/Parentheses check (Descriptions like [Door creaks])
            brackets = re_sdh_brackets.findall(clean_content)
            if brackets:
                noise_words = ['thud', 'creak', 'sigh', 'gasp', 'music', 'laugh', 'chuckle', 'exhale', 'inhale', 'engine', 'birds', 'wind', 'footsteps']
                noise_count = sum(1 for b in brackets if any(word in b.lower() for word in noise_words) or b.isupper())
                
                if noise_count > 3:
                    sdh_points += 4
                elif len(brackets) > 10:
                    sdh_points += 2

            # 2. Music symbols (Common in SDH for background music)
            if re_music.search(clean_content):
                sdh_points += 3
            
            # 3. Speaker labels (NAME: Hello)
            speakers = re_speaker.findall(clean_content)
            if len(speakers) > 5:
                sdh_points += 3
                
            return "SDH" if sdh_points >= 4 else "Normal"
    except Exception as e:
        logging.error(f"Error detecting SDH in {file_path}: {e}")
        return "Normal"

def analyze_folder(folder_path):
    video_file, subtitle_files = None, []
    try:
        for file in Path(folder_path).iterdir():
            if file.is_file():
                if file.suffix.lower() in CONFIG['VIDEO_EXTENSIONS']:
                    if video_file:
                        logging.warning(f"Multiple videos found in {Path(folder_path).name}, using first found.")
                    else:
                        video_file = file
                elif file.suffix.lower() == CONFIG['SUBTITLE_EXTENSION']:
                    subtitle_files.append(file)
    except Exception as e:
        logging.error(f"Could not analyze folder {folder_path}: {e}")
    return video_file, subtitle_files

def merge_subtitles(video_file, subtitle_files, output_path, mkvmerge_path, progress_callback=None):
    cmd = [mkvmerge_path, '--ui-language', 'en', '-o', str(output_path), str(video_file)]
    
    sdh_count = 0
    normal_count = 0
    
    for sub_file in subtitle_files:
        sub_type = detect_subtitle_type(sub_file)
        if sub_type == "SDH":
            sdh_count += 1
            track_name = f"SDH {sdh_count}"
        else:
            normal_count += 1
            track_name = f"SRT {normal_count}"
            
        cmd.extend(['--language', '0:eng', '--track-name', f'0:{track_name}', str(sub_file)])

    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8', 
            startupinfo=startupinfo,
            bufsize=1,
            universal_newlines=True
        )
        
        # Parse output for real-time progress
        for line in process.stdout:
            if "Progress:" in line:
                try:
                    percent = int(re.search(r'(\d+)%', line).group(1))
                    if progress_callback:
                        progress_callback(percent)
                except:
                    pass
        
        process.wait()
        if process.returncode == 0:
            return True, None
        else:
            return False, process.stderr.read()
    except Exception as e:
        return False, str(e)

# ====================================================
# Main GUI Application (Corrected Structure)
# ====================================================
class SubtitleMergerApp(TkinterDnD.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Theme and Styling ---
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.COLOR_PURPLE = "#8e44ad"
        self.COLOR_SUCCESS = "#2ecc71"
        self.COLOR_ERROR = "#e74c3c"
        self.COLOR_WARNING = "#f39c12"
        self.COLOR_INFO = "#3498db"
        self.FONT_FAMILY = ("Segoe UI", 13)

        # --- Window Setup ---
        self.title("Johny's Professional Subtitle Merger v2")
        self.geometry("1000x700")

        appearance_mode = ctk.get_appearance_mode()
        fg_color_tuple = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        background_color = fg_color_tuple[1] if appearance_mode == "Dark" else fg_color_tuple[0]
        self.config(bg=background_color)

        self.log_queue = queue.Queue()
        self.is_processing = False
        self.folders_to_process = set()
        self.start_time = None
        self.output_folder = ctk.StringVar(value=CONFIG['DEFAULT_OUTPUT_FOLDER'])
        self.mkvmerge_path = ctk.StringVar(value=CONFIG['MKVMERGE_PATH'])

        # --- Drag & Drop Setup ---
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        
        self.update_folder_list_view()
        self.process_log_queue()
        self.update_heartbeat() # Every 5 seconds update

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

        logo_label = ctk.CTkLabel(self.sidebar, text="SUB MERGER V2", font=(self.FONT_FAMILY[0], 20, "bold"), text_color=self.COLOR_PURPLE)
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # MKVMERGE Path Section
        ctk.CTkLabel(self.sidebar, text="mkvmerge Path:", font=(self.FONT_FAMILY[0], 12, "bold")).grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.mkvmerge_entry = ctk.CTkEntry(self.sidebar, textvariable=self.mkvmerge_path, font=(self.FONT_FAMILY[0], 11))
        self.mkvmerge_entry.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="ew")
        btn_browse_mkv = ctk.CTkButton(self.sidebar, text="Browse mkvmerge", height=28, font=(self.FONT_FAMILY[0], 11), command=self.browse_mkvmerge)
        btn_browse_mkv.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Output Folder Section
        ctk.CTkLabel(self.sidebar, text="Output Folder:", font=(self.FONT_FAMILY[0], 12, "bold")).grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.output_entry = ctk.CTkEntry(self.sidebar, textvariable=self.output_folder, placeholder_text="Default: Source Folder", font=(self.FONT_FAMILY[0], 11))
        self.output_entry.grid(row=5, column=0, padx=20, pady=(5, 5), sticky="ew")
        btn_browse_out = ctk.CTkButton(self.sidebar, text="Browse Output", height=28, font=(self.FONT_FAMILY[0], 11), command=self.browse_output_folder)
        btn_browse_out.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Settings
        ctk.CTkLabel(self.sidebar, text="Settings:", font=(self.FONT_FAMILY[0], 12, "bold")).grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        self.parallel_var = ctk.BooleanVar(value=True)
        self.check_parallel = ctk.CTkCheckBox(self.sidebar, text="Parallel Processing", variable=self.parallel_var, font=(self.FONT_FAMILY[0], 12))
        self.check_parallel.grid(row=8, column=0, padx=20, pady=5, sticky="w")

        # Action Buttons
        self.btn_add = ctk.CTkButton(self.sidebar, text="Add Folder", font=self.FONT_FAMILY, command=self.browse_folder)
        self.btn_add.grid(row=9, column=0, padx=20, pady=10, sticky="ew")

        self.btn_clear = ctk.CTkButton(self.sidebar, text="Clear List", font=self.FONT_FAMILY, fg_color="transparent", border_width=1, command=self.clear_list)
        self.btn_clear.grid(row=10, column=0, padx=20, pady=5, sticky="ew")

        self.btn_clear_logs = ctk.CTkButton(self.sidebar, text="Clear Logs", font=self.FONT_FAMILY, fg_color="transparent", border_width=1, command=self.clear_logs)
        self.btn_clear_logs.grid(row=11, column=0, padx=20, pady=5, sticky="ew")

        self.btn_start = ctk.CTkButton(self.sidebar, text="🚀 START MERGE", font=(self.FONT_FAMILY[0], 15, "bold"),
                                       command=self.start_processing, fg_color=self.COLOR_PURPLE, hover_color="#732d91", height=50)
        self.btn_start.grid(row=13, column=0, padx=20, pady=20, sticky="ew")

    def create_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        # Folder List
        self.folder_list_frame = ctk.CTkScrollableFrame(self.main_area, label_text="Queue (Drag & Drop Supported)", label_font=(self.FONT_FAMILY[0], 14, "bold"))
        self.folder_list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.folder_list_frame.grid_columnconfigure(0, weight=1)

        # Log and Progress
        bottom_frame = ctk.CTkFrame(self.main_area)
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_rowconfigure(1, weight=1)

        progress_container = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        progress_container.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(progress_container, text="Status: Ready", font=self.FONT_FAMILY, anchor="w")
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        self.time_label = ctk.CTkLabel(progress_container, text="Elapsed: 0s", font=(self.FONT_FAMILY[0], 11), text_color="gray")
        self.time_label.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(bottom_frame, progress_color=self.COLOR_PURPLE, height=12)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")

        self.log_area = ctk.CTkTextbox(bottom_frame, state="disabled", font=("Consolas", 12), activate_scrollbars=True, border_spacing=5)
        self.log_area.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

    def handle_drop(self, event):
        paths = self.tk.splitlist(event.data)
        for path_str in paths:
            path = Path(path_str.strip('{}'))
            if path.is_dir():
                self.folders_to_process.add(str(path))
            else:
                self.log_queue.put((f"Skipped non-folder: {path.name}", self.COLOR_WARNING))
        self.update_folder_list_view()

    def browse_mkvmerge(self):
        file = ctk.filedialog.askopenfilename(title="Select mkvmerge.exe", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if file:
            self.mkvmerge_path.set(file)

    def browse_folder(self):
        folder = ctk.filedialog.askdirectory(title="Select Folder")
        if folder:
            self.folders_to_process.add(folder)
            self.update_folder_list_view()

    def browse_output_folder(self):
        folder = ctk.filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def update_folder_list_view(self):
        for widget in self.folder_list_frame.winfo_children():
            widget.destroy()

        if not self.folders_to_process:
            placeholder = ctk.CTkLabel(self.folder_list_frame, text="✨ Drop folders here to start merging...", text_color="gray", font=(self.FONT_FAMILY[0], 14, "italic"))
            placeholder.grid(row=0, column=0, padx=10, pady=20, sticky="ew")
            return

        for i, folder in enumerate(sorted(list(self.folders_to_process))):
            frame = ctk.CTkFrame(self.folder_list_frame, fg_color="transparent")
            frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            frame.grid_columnconfigure(0, weight=1)
            
            label = ctk.CTkLabel(frame, text=f"  📂 {Path(folder).name}", anchor="w", font=self.FONT_FAMILY)
            label.grid(row=0, column=0, sticky="w")
            
            remove_btn = ctk.CTkButton(frame, text="✕", width=30, height=24, fg_color="transparent", text_color="gray", hover_color="#e74c3c", command=lambda f=folder: self.remove_folder(f))
            remove_btn.grid(row=0, column=1, sticky="e")

    def remove_folder(self, folder):
        if self.is_processing: return
        self.folders_to_process.remove(folder)
        self.update_folder_list_view()

    def clear_list(self):
        if self.is_processing: return
        self.folders_to_process.clear()
        self.update_folder_list_view()

    def clear_logs(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    def log_message(self, message, color=None):
        self.log_area.configure(state="normal")
        tag = f"tag_{len(self.log_area.get('1.0', 'end-1c'))}"
        self.log_area.insert("end", message + "\n")
        if color:
            self.log_area.tag_add(tag, f"end-{len(message)+2}c", "end-1c")
            self.log_area.tag_config(tag, foreground=color)
        self.log_area.configure(state="disabled")
        self.log_area.yview_moveto(1.0)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message, color = self.log_queue.get_nowait()
            self.log_message(message, color)
        self.after(100, self.process_log_queue)

    def update_heartbeat(self):
        if self.is_processing and self.start_time:
            import time
            elapsed = time.time() - self.start_time
            self.time_label.configure(text=f"Elapsed: {int(elapsed)}s")
            
            # Simple ETA calculation
            if self.completed_tasks > 0:
                total = len(self.folders_to_process)
                avg_time = elapsed / self.completed_tasks
                remaining = (total - self.completed_tasks) * avg_time
                self.time_label.configure(text=f"Elapsed: {int(elapsed)}s | ETA: {int(remaining)}s")
                
        self.after(5000, self.update_heartbeat)

    def set_ui_state(self, is_processing):
        self.is_processing = is_processing
        state = "disabled" if is_processing else "normal"
        self.btn_add.configure(state=state)
        self.btn_clear.configure(state=state)
        self.btn_start.configure(state=state)
        self.output_entry.configure(state=state)
        self.mkvmerge_entry.configure(state=state)
        self.check_parallel.configure(state=state)
        self.btn_start.configure(text="🔄 PROCESSING..." if is_processing else "🚀 START MERGE")

    def start_processing(self):
        if not self.folders_to_process:
            self.log_queue.put(("⚠️ Please add folders to process.", self.COLOR_WARNING))
            return

        import time
        self.start_time = time.time()
        self.set_ui_state(True)
        self.clear_logs()
        self.log_queue.put(("🚀 Initialization started...", self.COLOR_INFO))

        self.thread = threading.Thread(target=self.processing_manager, daemon=True)
        self.thread.start()

    def processing_manager(self):
        folders = list(self.folders_to_process)
        self.total_folders = len(folders)
        self.completed_tasks = 0
        self.folder_progress = {f: 0 for f in folders}
        
        out_folder = self.output_folder.get()
        if out_folder:
            Path(out_folder).mkdir(parents=True, exist_ok=True)

        use_parallel = self.parallel_var.get()
        max_workers = CONFIG['MAX_PARALLEL_TASKS'] if use_parallel else 1
        
        self.log_queue.put((f"ℹ️ Mode: {'Parallel' if use_parallel else 'Sequential'} ({max_workers} workers)", self.COLOR_INFO))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_single_folder, folder, out_folder) for folder in folders]
            for future in futures:
                future.result()

        import time
        elapsed = int(time.time() - self.start_time)
        summary = f"✨ DONE! Processed {self.total_folders} folders in {elapsed}s."
        self.progress_bar.set(1.0)
        self.progress_label.configure(text=summary)
        self.log_queue.put(("\n" + summary, self.COLOR_SUCCESS))
        self.set_ui_state(False)

    def update_overall_progress(self):
        total_percent = sum(self.folder_progress.values()) / self.total_folders
        self.progress_bar.set(total_percent / 100)
        self.progress_label.configure(text=f"Overall Progress: {int(total_percent)}% ({self.completed_tasks}/{self.total_folders} completed)")

    def process_single_folder(self, folder_path, out_folder_base):
        try:
            folder_name = Path(folder_path).name
            self.log_queue.put((f"🔍 Analyzing: {folder_name}", None))
            video, subs = analyze_folder(folder_path)

            if not video or not subs:
                self.log_queue.put((f"⚠️ Skipped {folder_name}: Missing video or subtitles.", self.COLOR_WARNING))
                self.folder_progress[folder_path] = 100
            else:
                if out_folder_base:
                    output = Path(out_folder_base) / (video.stem + CONFIG['OUTPUT_SUFFIX'] + '.mkv')
                else:
                    output = video.with_stem(video.stem + CONFIG['OUTPUT_SUFFIX']).with_suffix('.mkv')

                def progress_cb(percent):
                    self.folder_progress[folder_path] = percent
                    self.update_overall_progress()

                success, error = merge_subtitles(video, subs, output, self.mkvmerge_path.get(), progress_callback=progress_cb)
                if success:
                    self.log_queue.put((f"✅ MERGED: {folder_name}", self.COLOR_SUCCESS))
                    self.folder_progress[folder_path] = 100
                else:
                    self.log_queue.put((f"❌ FAILED: {folder_name} - {error}", self.COLOR_ERROR))
                    self.folder_progress[folder_path] = 100
        except Exception as e:
            self.log_queue.put((f"🔥 CRITICAL ERROR in {folder_path}: {e}", self.COLOR_ERROR))
            self.folder_progress[folder_path] = 100
        
        self.completed_tasks += 1
        self.update_overall_progress()


if __name__ == "__main__":
    app = SubtitleMergerApp()
    app.mainloop()