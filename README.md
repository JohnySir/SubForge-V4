# 🎬 SubForge V4: The Professional Subtitle Architect 🚀

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-purple?style=for-the-badge)
![MKVToolNix](https://img.shields.io/badge/Engine-MKVToolNix-red?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-4.0_Stable-green?style=for-the-badge)

**SubForge V4** is the ultimate evolution of subtitle muxing. Designed for collectors, encoders, and media enthusiasts, it transforms the tedious task of merging subtitles into a high-speed, intelligent, and automated experience.

![gui](https://raw.githubusercontent.com/JohnySir/SubForge-V4/refs/heads/main/images/SS.png "gui") 

---

## ✨ What’s New in V4 (The "Titan" Update)
*Version 4 marks a complete architectural overhaul, moving from a simple script to a professional-grade desktop application.*

### 🧠 Cognitive SDH Detection (Acoustic-Eye™)
No more generic track names. V4 features a proprietary **Weighted Heuristic Scoring System** that reads *inside* your SRT files. It identifies Sound Effects, Music Cues, and Speaker Labels to automatically distinguish between **SDH (Hard of Hearing)** and **Normal** subtitles, naming your tracks perfectly every time.

### ⚡ Hyper-Threaded Merging
Time is precious. V4 introduces **Parallel Processing**, allowing you to mux multiple folders simultaneously. Utilizing a dynamic `ThreadPoolExecutor`, SubForge saturates your CPU's potential to finish hours of work in minutes.

### 🎨 Aero-Sidebar Interface
A complete UI redesign using **CustomTkinter**. The new sidebar-driven layout provides instant access to settings, mkvmerge paths, and output configurations while maintaining a clean, modern aesthetic.

### ⏱️ Real-time Heartbeat & ETA
Stay informed with our new **Live Monitoring System**. Every 5 seconds, SubForge calculates your processing speed and provides a real-time **ETA (Estimated Time of Arrival)**, so you know exactly when your library will be ready.

---

## 🚀 Key Features

*   **Drag & Drop Workflow:** Just drop your movie folders into the queue and let SubForge do the rest.
*   **Global Output Management:** Specify a dedicated output folder or save files directly in the source—your choice.
*   **Smart Folder Analysis:** Automatically pairs video files with their corresponding `.srt` tracks.
*   **Professional Logging:** A dedicated console window provides real-time feedback on every byte processed.
*   **Flexible Config:** Easily update your `mkvmerge.exe` path through the GUI without touching a line of code.

---

## 🛠️ The "Acoustic-Eye" Logic (How SDH Detection Works)
SubForge doesn't just guess; it analyzes. Each subtitle file is put through a scoring gauntlet:
1.  **Noise Identification (+4 pts):** Looks for environmental descriptions like `[Door creaks]` or `(Sighs)`.
2.  **Musicality (+3 pts):** Detects symbols like `♪`, `♫`, or `#`.
3.  **Speaker Context (+3 pts):** Identifies uppercase name labels like `JOHN: Hello`.
4.  **The Threshold:** Any file scoring **4 or higher** is automatically forged as an **SDH** track.

---

## 📥 Installation

1.  **Requirement:** Ensure you have [MKVToolNix](https://mkvtoolnix.download/) installed on your system.
2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/subforge-v4.git
    cd subforge-v4
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Launch the Forge:**
    ```bash
    python subforge-v4.py
    ```

---

## 📖 Usage Guide

### 📂 File Structure (Critical)
SubForge is designed for **Batch Processing**. To work correctly, your files should be organized as follows:
*   **Each movie/episode must have its own folder.**
*   Inside that folder, place the **Video File** and all its corresponding **Subtitle (.srt) files**.
*   You can then drag-and-drop or add **multiple folders** to the application at once.

### ⚙️ How to Operate
1.  **Set Paths:** Open the sidebar and ensure the `mkvmerge Path` points to your `mkvmerge.exe`.
2.  **Add Folders:** Drag and drop your **parent folders** (each containing a video and subs) into the queue.
3.  **Configure Output:** (Optional) Set a specific output folder. If left blank, SubForge saves the new MKV inside the original folder.
4.  **Toggle Parallel:** Keep "Parallel Processing" enabled for maximum speed.
5.  **Ignite:** Hit `🚀 START MERGE` and watch the forge work.

---

## 📜 Requirements
*   **OS:** Windows (Optimized for Win 10/11)
*   **Python:** 3.10 or higher
*   **Libraries:** `customtkinter`, `tkinterdnd2`

---

## 🤝 Credits
ME! 😋
