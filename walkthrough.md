# LAN Messenger & File Sharer Walkthrough

I have created a LAN messaging and file sharing application that works on Linux devices (Raspberry Pi and Laptop). It supports both a Terminal User Interface (TUI) and a Graphical User Interface (GUI).

## Features
- **Peer Discovery**: Automatically finds other devices on the same network using UDP broadcast.
- **Messaging**: Send text messages to discovered peers.
- **File Sharing**: Send files to peers (basic implementation).
- **Dual Interface**: Choose between TUI (Textual) and GUI (Tkinter).

## Prerequisites
- Python 3.x
- `tkinter` (usually installed with Python, but may need `sudo pacman -S tk` or `sudo apt install python3-tk` on some systems).

## Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone https://github.com/AnoopAparajit/PiToLaptopMessagerandFilesharer.git
    cd PiToLaptopMessagerandFilesharer
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## Usage

### Running the GUI (Default)
```bash
python main.py --username MyLaptop
```
Or simply:
```bash
python main.py
```

### Running the TUI
```bash
python main.py --mode tui --username MyPi
```

## Troubleshooting
- **Firewall**: Ensure ports **5000 (UDP)** and **5001 (TCP)** are open on your firewall.
- **Tkinter Error**: If you get an error about `libtk` or `_tkinter`, install the system package for Tkinter (e.g., `sudo pacman -S tk` on Manjaro/Arch).
