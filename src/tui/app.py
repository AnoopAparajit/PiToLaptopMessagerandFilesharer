from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button, ListView, ListItem, Label
from textual.message import Message as TextualMessage
from textual import work
from datetime import datetime
import threading
import asyncio

from ..core.discovery import PeerDiscovery
from ..core.network import NetworkManager
from ..core.protocol import Message, MessageType

class ChatMessage(ListItem):
    def __init__(self, sender: str, text: str, is_self: bool):
        super().__init__()
        self.sender = sender
        self.text = text
        self.is_self = is_self

    def compose(self) -> ComposeResult:
        align = "right" if self.is_self else "left"
        color = "green" if self.is_self else "blue"
        yield Label(f"[{color}]{self.sender}[/{color}]: {self.text}")

class PeerItem(ListItem):
    def __init__(self, ip: str, name: str):
        super().__init__()
        self.ip = ip
        self.name = name

    def compose(self) -> ComposeResult:
        yield Label(f"{self.name} ({self.ip})")

class TuiApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 30;
        dock: left;
        border-right: solid green;
    }
    #chat-area {
        weight: 1;
        border: solid blue;
    }
    #input-area {
        height: 3;
        dock: bottom;
    }
    """

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.discovery = PeerDiscovery(username, self.on_peer_discovered, self.on_peer_lost)
        self.network = NetworkManager(username, self.on_message_received)
        self.selected_peer_ip = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sidebar"):
            yield Label("Discovered Peers")
            yield ListView(id="peer-list")
        with Vertical(id="chat-area"):
            yield ListView(id="messages")
        with Horizontal(id="input-area"):
            yield Input(placeholder="Type a message...", id="message-input")
            yield Button("Send", id="send-button")
        yield Footer()

    def on_mount(self):
        self.discovery.start()
        self.network.start()

    def on_unmount(self):
        self.discovery.stop()
        self.network.stop()

    def on_peer_discovered(self, ip: str, name: str):
        self.call_from_thread(self._add_peer, ip, name)

    def _add_peer(self, ip: str, name: str):
        peer_list = self.query_one("#peer-list", ListView)
        peer_list.append(PeerItem(ip, name))

    def on_peer_lost(self, ip: str):
        self.call_from_thread(self._remove_peer, ip)

    def _remove_peer(self, ip: str):
        peer_list = self.query_one("#peer-list", ListView)
        for item in peer_list.children:
            if isinstance(item, PeerItem) and item.ip == ip:
                item.remove()
                break

    def on_message_received(self, msg: Message):
        if msg.type == MessageType.TEXT:
            self.call_from_thread(self._add_message, msg.sender_name, msg.payload['text'], False)

    def _add_message(self, sender: str, text: str, is_self: bool):
        messages = self.query_one("#messages", ListView)
        messages.append(ChatMessage(sender, text, is_self))
        messages.scroll_end()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send-button":
            self._send_message()

    def on_input_submitted(self, event: Input.Submitted):
        self._send_message()

    def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.id == "peer-list":
            item = event.item
            if isinstance(item, PeerItem):
                self.selected_peer_ip = item.ip
                self.notify(f"Selected peer: {item.name}")

    def _send_message(self):
        input_widget = self.query_one("#message-input", Input)
        text = input_widget.value
        if not text:
            return

        if not self.selected_peer_ip:
            self.notify("Please select a peer first.", severity="error")
            return

        try:
            self.network.send_message(self.selected_peer_ip, text)
            self._add_message(self.username, text, True)
            input_widget.value = ""
        except Exception as e:
            self.notify(f"Failed to send: {e}", severity="error")

if __name__ == "__main__":
    app = TuiApp("User")
    app.run()
