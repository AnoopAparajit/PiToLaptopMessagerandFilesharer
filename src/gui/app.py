import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
from typing import Optional

from ..core.discovery import PeerDiscovery
from ..core.network import NetworkManager
from ..core.protocol import Message, MessageType

class GuiApp:
    def __init__(self, root: tk.Tk, username: str):
        self.root = root
        self.username = username
        self.root.title(f"LAN Messenger - {username}")
        self.root.geometry("800x600")

        self.discovery = PeerDiscovery(username, self.on_peer_discovered, self.on_peer_lost)
        self.network = NetworkManager(username, self.on_message_received)
        self.selected_peer_ip: Optional[str] = None
        
        # Queue for thread-safe UI updates
        self.gui_queue = queue.Queue()

        self._setup_ui()
        self._start_services()
        self._process_queue()

    def _setup_ui(self):
        # Main Layout
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sidebar (Peer List)
        sidebar_frame = ttk.Labelframe(main_paned, text="Peers")
        main_paned.add(sidebar_frame, weight=1)

        self.peer_listbox = tk.Listbox(sidebar_frame)
        self.peer_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.peer_listbox.bind('<<ListboxSelect>>', self._on_peer_selected)

        # Chat Area
        chat_frame = ttk.Frame(main_paned)
        main_paned.add(chat_frame, weight=3)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input Area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.msg_entry = ttk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        send_btn = ttk.Button(input_frame, text="Send", command=self._send_message)
        send_btn.pack(side=tk.LEFT)

        file_btn = ttk.Button(input_frame, text="File", command=self._send_file)
        file_btn.pack(side=tk.LEFT, padx=(5, 0))

    def _start_services(self):
        self.discovery.start()
        self.network.start()

    def _process_queue(self):
        try:
            while True:
                task = self.gui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def on_peer_discovered(self, ip: str, name: str):
        self.gui_queue.put(lambda: self._add_peer(ip, name))

    def _add_peer(self, ip: str, name: str):
        display = f"{name} ({ip})"
        # Check if already exists to avoid duplicates (though discovery handles this logic mostly)
        if display not in self.peer_listbox.get(0, tk.END):
            self.peer_listbox.insert(tk.END, display)

    def on_peer_lost(self, ip: str):
        self.gui_queue.put(lambda: self._remove_peer(ip))

    def _remove_peer(self, ip: str):
        # Find and remove
        for idx, item in enumerate(self.peer_listbox.get(0, tk.END)):
            if f"({ip})" in item:
                self.peer_listbox.delete(idx)
                if self.selected_peer_ip == ip:
                    self.selected_peer_ip = None
                    self._log_message("System", f"Peer {ip} lost.")
                break

    def _on_peer_selected(self, event):
        selection = self.peer_listbox.curselection()
        if selection:
            item = self.peer_listbox.get(selection[0])
            # Extract IP from "Name (IP)"
            self.selected_peer_ip = item.split('(')[-1].strip(')')
            self._log_message("System", f"Selected peer: {self.selected_peer_ip}")

    def on_message_received(self, msg: Message):
        if msg.type == MessageType.TEXT:
            self.gui_queue.put(lambda: self._log_message(msg.sender_name, msg.payload['text']))
        elif msg.type == MessageType.FILE_OFFER:
            self.gui_queue.put(lambda: self._handle_file_offer(msg))

    def _handle_file_offer(self, msg: Message):
        filename = msg.payload['filename']
        size = msg.payload['filesize']
        if messagebox.askyesno("File Offer", f"{msg.sender_name} wants to send {filename} ({size} bytes). Accept?"):
            # In a real app, we'd send FILE_ACCEPT and start transfer.
            # For this simplified version, we'll just log it.
            self._log_message("System", f"Accepted file offer for {filename} (Not fully implemented)")
        else:
            self._log_message("System", f"Rejected file offer for {filename}")

    def _send_message(self):
        text = self.msg_entry.get()
        if not text:
            return
        
        if not self.selected_peer_ip:
            messagebox.showerror("Error", "Select a peer first.")
            return

        try:
            self.network.send_message(self.selected_peer_ip, text)
            self._log_message(self.username, text)
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {e}")

    def _send_file(self):
        if not self.selected_peer_ip:
            messagebox.showerror("Error", "Select a peer first.")
            return

        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                self.network.send_file_offer(self.selected_peer_ip, filepath)
                self._log_message("System", f"Sent file offer: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send file offer: {e}")

    def _log_message(self, sender: str, text: str):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"[{sender}]: {text}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def on_close(self):
        self.discovery.stop()
        self.network.stop()
        self.root.destroy()

def run_gui(username: str):
    root = tk.Tk()
    app = GuiApp(root, username)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
