import tkinter
import threading
import customtkinter  # Added for widget type checking
from tkinter import messagebox
from constants import (
    BTN_ADD,
    BTN_ADD_RULE,
    BTN_CANCEL,
    BTN_CLOSE,
    BTN_DELETE,
    BTN_EDIT,
    BTN_SAVE,
    BTN_SAVE_CHANGES,
    LBL_NAME,
    LBL_RULE_ACTION,
    LBL_RULE_TYPE,
    LBL_RULE_VALUE,
    LBL_SUBSCRIPTIONS,
    LBL_URL,
    MSG_INPUT_ERROR_EMPTY,
    TITLE_ADD_ROUTING_RULE,
    TITLE_ADD_SUB,
    TITLE_EDIT_ROUTING_RULE,
    TITLE_EDIT_SUB,
    TITLE_SUB_MANAGER,
    APP_FONT,
    LogLevel,
    TITLE_CONFIRM_DELETE,
)


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


class AddRoutingRuleDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, callback, initial_rule=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.initial_rule = initial_rule

        self.title(
            TITLE_ADD_ROUTING_RULE if initial_rule is None else TITLE_EDIT_ROUTING_RULE
        )
        self.geometry("400x300")
        self.transient(parent)  # Make it appear on top of the main window
        self.grab_set()  # Make it modal

        self.grid_columnconfigure(1, weight=1)

        # Rule Type
        customtkinter.CTkLabel(self, text=LBL_RULE_TYPE, font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.type_optionmenu = customtkinter.CTkOptionMenu(
            self,
            values=["domain", "ip", "process", "geosite", "geoip"],
            font=APP_FONT,
        )
        self.type_optionmenu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Rule Value
        customtkinter.CTkLabel(self, text=LBL_RULE_VALUE, font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.value_entry = customtkinter.CTkEntry(self, font=APP_FONT)
        self.value_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Action
        customtkinter.CTkLabel(self, text=LBL_RULE_ACTION, font=APP_FONT).grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )
        self.action_optionmenu = customtkinter.CTkOptionMenu(
            self,
            values=["direct", "proxy", "block"],
            font=APP_FONT,
        )
        self.action_optionmenu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        if self.initial_rule:
            self.type_optionmenu.set(self.initial_rule["type"])
            self.value_entry.insert(0, self.initial_rule["value"])
            self.action_optionmenu.set(self.initial_rule["action"])

        # Buttons
        add_button = customtkinter.CTkButton(
            self,
            text=BTN_ADD_RULE if initial_rule is None else BTN_SAVE_CHANGES,
            command=self._add_button_command,
            font=APP_FONT,
        )
        add_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        cancel_button = customtkinter.CTkButton(
            self, text=BTN_CANCEL, command=self.destroy, font=APP_FONT
        )
        cancel_button.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

    def _add_button_command(self):
        rule_data = {
            "type": self.type_optionmenu.get(),
            "value": self.value_entry.get(),
            "action": self.action_optionmenu.get(),
        }
        if self.callback:
            self.callback(rule_data)
        self.destroy()


class SubscriptionManagerDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, subscriptions, log_callback):
        super().__init__(parent)
        self.parent = parent
        self.subscriptions = subscriptions
        self.log = log_callback

        self.title(TITLE_SUB_MANAGER)
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scrollable_frame = customtkinter.CTkScrollableFrame(
            self, label_text=LBL_SUBSCRIPTIONS
        )
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.sub_widgets = []
        self.populate_subscriptions()

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        add_button = customtkinter.CTkButton(
            button_frame, text=BTN_ADD, command=self.add_subscription
        )
        add_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        close_button = customtkinter.CTkButton(
            button_frame, text=BTN_CLOSE, command=self.destroy
        )
        close_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def populate_subscriptions(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, sub in enumerate(self.subscriptions):
            sub_frame = customtkinter.CTkFrame(self.scrollable_frame)
            sub_frame.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            sub_frame.grid_columnconfigure(1, weight=1)

            enabled_var = customtkinter.BooleanVar(value=sub.get("enabled", True))
            checkbox = customtkinter.CTkCheckBox(
                sub_frame,
                text="",
                variable=enabled_var,
                command=lambda index=i: self.toggle_subscription(index, enabled_var),
            )
            checkbox.grid(row=0, column=0, padx=5)

            name_label = customtkinter.CTkLabel(sub_frame, text=sub["name"], anchor="w")
            name_label.grid(row=0, column=1, padx=5, sticky="ew")

            edit_button = customtkinter.CTkButton(
                sub_frame,
                text=BTN_EDIT,
                width=60,
                command=lambda index=i: self.edit_subscription(index),
            )
            edit_button.grid(row=0, column=2, padx=5)

            delete_button = customtkinter.CTkButton(
                sub_frame,
                text=BTN_DELETE,
                width=60,
                command=lambda index=i: self.delete_subscription(index),
            )
            delete_button.grid(row=0, column=3, padx=5)

    def toggle_subscription(self, index, var):
        self.subscriptions[index]["enabled"] = var.get()
        self.log(
            f"Subscription '{self.subscriptions[index]['name']}' {'enabled' if var.get() else 'disabled'}.",
            LogLevel.INFO,
        )

    def add_subscription(self):
        dialog = SubscriptionEditDialog(self, TITLE_ADD_SUB)
        self.wait_window(dialog)
        if dialog.result:
            self.subscriptions.append(dialog.result)
            self.populate_subscriptions()
            self.log(f"Added subscription: {dialog.result['name']}", LogLevel.INFO)

    def edit_subscription(self, index):
        dialog = SubscriptionEditDialog(self, TITLE_EDIT_SUB, self.subscriptions[index])
        self.wait_window(dialog)
        if dialog.result:
            self.subscriptions[index] = dialog.result
            self.populate_subscriptions()
            self.log(f"Edited subscription: {dialog.result['name']}", LogLevel.INFO)

    def delete_subscription(self, index):
        sub_name = self.subscriptions[index]["name"]
        if messagebox.askyesno(
            TITLE_CONFIRM_DELETE,
            f"Are you sure you want to delete subscription '{sub_name}'?",
        ):
            del self.subscriptions[index]
            self.populate_subscriptions()
            self.log(f"Deleted subscription: {sub_name}", LogLevel.INFO)


class SubscriptionEditDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, title, sub=None):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.sub = sub

        self.title(title)
        self.geometry("400x200")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(self, text=LBL_NAME).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.name_entry = customtkinter.CTkEntry(self)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(self, text=LBL_URL).grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.url_entry = customtkinter.CTkEntry(self)
        self.url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        if sub:
            self.name_entry.insert(0, sub.get("name", ""))
            self.url_entry.insert(0, sub.get("url", ""))

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        save_button = customtkinter.CTkButton(
            button_frame, text=BTN_SAVE, command=self.save
        )
        save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        cancel_button = customtkinter.CTkButton(
            button_frame, text=BTN_CANCEL, command=self.destroy
        )
        cancel_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def save(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        if name and url:
            self.result = {
                "name": name,
                "url": url,
                "enabled": self.sub.get("enabled", True) if self.sub else True,
            }
            self.destroy()
        else:
            messagebox.showwarning("Input Error", MSG_INPUT_ERROR_EMPTY, parent=self)
