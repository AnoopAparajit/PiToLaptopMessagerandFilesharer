import argparse
import sys
import socket

def get_default_username():
    try:
        return socket.gethostname()
    except:
        return "User"

def main():
    parser = argparse.ArgumentParser(description="LAN Messenger & File Sharer")
    parser.add_argument("--mode", choices=["gui", "tui"], default="gui", help="Interface mode (gui or tui)")
    parser.add_argument("--username", default=get_default_username(), help="Username to display to peers")
    
    args = parser.parse_args()

    if args.mode == "tui":
        from src.tui.app import TuiApp
        app = TuiApp(args.username)
        app.run()
    else:
        from src.gui.app import run_gui
        run_gui(args.username)

if __name__ == "__main__":
    main()
