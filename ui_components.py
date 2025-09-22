import tkinter
import threading

def handle_text_shortcut(widget, action):
    """Handles text shortcuts like cut, copy, paste, select all for a given widget."""
    try:
        if action == 'cut':
            widget.event_generate("<<Cut>>")
        elif action == 'copy':
            widget.event_generate("<<Copy>>")
        elif action == 'select_all':
            if isinstance(widget, tkinter.Text) or isinstance(widget, tkinter.Text):
                widget.tag_add("sel", "1.0", "end")
            else: # Entry widgets
                widget.select_range(0, 'end')
                widget.icursor('end')
        elif action == 'paste':
            try:
                clipboard = widget.clipboard_get()
                # Try to delete selected text before pasting
                try:
                    start = widget.index("sel.first")
                    end = widget.index("sel.last")
                    widget.delete(start, end)
                except tkinter.TclError:
                    pass # No selection, just insert
                widget.insert(tkinter.INSERT, clipboard)
            except tkinter.TclError:
                pass # Clipboard is empty
    except AttributeError:
        pass # Widget doesn't support the action
    return "break" # Prevents default event handling

class RightClickMenu(tkinter.Menu):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, tearoff=0, **kwargs)
        self.parent = parent
        self.add_command(label="Cut", command=lambda: handle_text_shortcut(self.parent.focus_get(), 'cut'))
        self.add_command(label="Copy", command=lambda: handle_text_shortcut(self.parent.focus_get(), 'copy'))
        self.add_command(label="Paste", command=lambda: handle_text_shortcut(self.parent.focus_get(), 'paste'))
        self.add_separator()
        self.add_command(label="Select All", command=lambda: handle_text_shortcut(self.parent.focus_get(), 'select_all'))

    def popup(self, event):
        try:
            self.tk_popup(event.x_root, event.y_root)
        finally:
            self.grab_release()

class ServerContextMenu(tkinter.Menu):
    def __init__(self, parent, config, ping_label, ping_handler, url_test_handler, delete_handler, edit_handler, **kwargs):
        super().__init__(parent, tearoff=0, **kwargs)
        self.config = config
        self.ping_label = ping_label
        self.ping_handler = ping_handler
        self.url_test_handler = url_test_handler
        self.delete_handler = delete_handler
        self.edit_handler = edit_handler

        self.add_command(label="Test Ping (TCP)", command=self.test_ping_single)
        self.add_command(label="Test Latency (URL)", command=self.test_url_single)
        self.add_separator()
        self.add_command(label="Edit Server Name", command=self.edit_server)
        self.add_command(label="Delete Server", command=self.delete_server)

    def test_ping_single(self):
        threading.Thread(target=self.ping_handler, args=(self.config, self.ping_label), daemon=True).start()

    def test_url_single(self):
        threading.Thread(target=self.url_test_handler, args=(self.config, self.ping_label), daemon=True).start()

    def edit_server(self):
        self.edit_handler(self.config)

    def delete_server(self):
        self.delete_handler(self.config)

    def popup(self, event):
        try:
            self.tk_popup(event.x_root, event.y_root)
        finally:
            self.grab_release()
