import tkinter
import threading
import customtkinter  # Added for widget type checking


def handle_text_shortcut(widget, action):
    """Handles text shortcuts like cut, copy, paste, select all for a given widget."""
    try:
        # Determine the actual tkinter widget if it's a customtkinter wrapper
        tk_widget = None
        if isinstance(widget, customtkinter.CTkEntry):
            tk_widget = widget._entry
        elif isinstance(widget, customtkinter.CTkTextbox):
            tk_widget = widget._textbox
        elif isinstance(widget, tkinter.Entry) or isinstance(widget, tkinter.Text):
            tk_widget = widget

        if not tk_widget:
            return "break"  # Not a supported widget type for text shortcuts

        if action == "cut":
            if hasattr(tk_widget, "event_generate"):
                tk_widget.event_generate("<<Cut>>")
            elif (
                hasattr(tk_widget, "delete")
                and hasattr(tk_widget, "get")
                and hasattr(tk_widget, "clipboard_clear")
                and hasattr(tk_widget, "clipboard_append")
            ):
                try:
                    selected_text = tk_widget.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
                    tk_widget.clipboard_clear()
                    tk_widget.clipboard_append(selected_text)
                    tk_widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
                except tkinter.TclError:
                    pass  # No selection
        elif action == "copy":
            if hasattr(tk_widget, "event_generate"):
                tk_widget.event_generate("<<Copy>>")
            elif (
                hasattr(tk_widget, "get")
                and hasattr(tk_widget, "clipboard_clear")
                and hasattr(tk_widget, "clipboard_append")
            ):
                try:
                    selected_text = tk_widget.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
                    tk_widget.clipboard_clear()
                    tk_widget.clipboard_append(selected_text)
                except tkinter.TclError:
                    pass  # No selection
        elif action == "select_all":
            if hasattr(tk_widget, "select_range"):  # For Entry widgets
                tk_widget.select_range(0, "end")
                tk_widget.icursor("end")
            elif hasattr(tk_widget, "tag_add"):  # For Text widgets
                tk_widget.tag_add("sel", "1.0", "end")
                tk_widget.mark_set("insert", "end")
        elif action == "paste":
            try:
                clipboard_content = widget.clipboard_get()
                if tk_widget.tag_ranges(
                    "sel"
                ):  # If there's a selection, delete it first
                    tk_widget.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
                tk_widget.insert(tkinter.INSERT, clipboard_content)
            except tkinter.TclError:
                pass  # Clipboard is empty or widget doesn't support insert
    except AttributeError:
        pass  # Widget doesn't support the action
    return "break"  # Prevents default event handling


class RightClickMenu(tkinter.Menu):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, tearoff=0, **kwargs)
        self.parent = parent
        self.add_command(
            label="Cut",
            command=lambda: handle_text_shortcut(self.parent.focus_get(), "cut"),
        )
        self.add_command(
            label="Copy",
            command=lambda: handle_text_shortcut(self.parent.focus_get(), "copy"),
        )
        self.add_command(
            label="Paste",
            command=lambda: handle_text_shortcut(self.parent.focus_get(), "paste"),
        )
        self.add_separator()
        self.add_command(
            label="Select All",
            command=lambda: handle_text_shortcut(self.parent.focus_get(), "select_all"),
        )

    def popup(self, event):
        try:
            self.tk_popup(event.x_root, event.y_root)
        finally:
            self.grab_release()


class ServerContextMenu(tkinter.Menu):
    def __init__(
        self,
        parent,
        config,
        ping_label,
        ping_handler,
        url_test_handler,
        delete_handler,
        edit_handler,
        show_qr_handler,
        **kwargs,
    ):
        super().__init__(parent, tearoff=0, **kwargs)
        self.config = config
        self.ping_label = ping_label
        self.ping_handler = ping_handler
        self.url_test_handler = url_test_handler
        self.delete_handler = delete_handler
        self.edit_handler = edit_handler
        self.show_qr_handler = show_qr_handler

        self.add_command(label="Test Ping (TCP)", command=self.test_ping_single)
        self.add_command(label="Test Latency (URL)", command=self.test_url_single)
        self.add_command(label="Show QR Code", command=self.show_qr_code)
        self.add_separator()
        self.add_command(label="Edit Server Name", command=self.edit_server)
        self.add_command(label="Delete Server", command=self.delete_server)

    def show_qr_code(self):
        self.show_qr_handler(self.config)

    def test_ping_single(self):
        threading.Thread(
            target=self.ping_handler, args=(self.config, self.ping_label), daemon=True
        ).start()

    def test_url_single(self):
        threading.Thread(
            target=self.url_test_handler,
            args=(self.config, self.ping_label),
            daemon=True,
        ).start()

    def edit_server(self):
        self.edit_handler(self.config)

    def delete_server(self):
        self.delete_handler(self.config)

    def popup(self, event):
        try:
            self.tk_popup(event.x_root, event.y_root)
        finally:
            self.grab_release()
