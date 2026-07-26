"""AI Prompt Enhancer - Wispr Flow-style tool that enhances the currently selected prompt."""
import os, sys, time, threading
import tkinter as tk
from tkinter import scrolledtext
import requests
from dotenv import load_dotenv

try:
    import keyboard
except ImportError:
    keyboard = None
try:
    import pyperclip
except ImportError:
    pyperclip = None

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.getenv("API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "gpt-4o-mini")
HOTKEY = os.getenv("HOTKEY", "ctrl+alt+e")
try:
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.4"))
except ValueError:
    TEMPERATURE = 0.4

SYSTEM_PROMPT = (
    "You are an expert prompt engineer. Rewrite the user text into a clear, "
    "detailed, and effective prompt for a large language model. "
    "Preserve the original intent and language. Add helpful structure, "
    "context, and explicit instructions where useful. "
    "Return ONLY the improved prompt with no preamble and no markdown fences."
)

def enhance_prompt(text):
    if not API_KEY:
        raise RuntimeError("API_KEY is not set. Edit your .env file.")
    url = BASE_URL + "/chat/completions"
    headers = {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": MODEL_ID,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError("API error %s: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected API response: " + str(data)[:300])


def _release_modifiers():
    """Release any hotkey modifiers that may still be held down so they
    do not corrupt the synthetic Ctrl+C / Ctrl+V we send."""
    for key in ("ctrl", "alt", "shift", "windows"):
        try:
            keyboard.release(key)
        except Exception:
            pass


def get_selected_text():
    if not (keyboard and pyperclip):
        raise RuntimeError("keyboard/pyperclip not installed.")
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = ""
    # Sentinel so we can tell if the clipboard truly changed.
    sentinel = "__PE_NO_SELECTION__"
    try:
        pyperclip.copy(sentinel)
    except Exception:
        pass
    # Release the held hotkey modifiers before issuing Ctrl+C.
    _release_modifiers()
    time.sleep(0.12)
    try:
        keyboard.press_and_release("ctrl+c")
    except Exception:
        keyboard.send("ctrl+c")
    # Poll the clipboard for up to ~1.2s until it changes.
    selected = ""
    for _ in range(24):
        time.sleep(0.05)
        try:
            current = pyperclip.paste()
        except Exception:
            continue
        if current and current != sentinel:
            selected = current
            break
    if not selected.strip() or selected == sentinel:
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
        return ""
    return selected


def replace_selection_with(text):
    if not (keyboard and pyperclip):
        raise RuntimeError("keyboard/pyperclip not installed.")
    pyperclip.copy(text)
    _release_modifiers()
    time.sleep(0.12)
    try:
        keyboard.press_and_release("ctrl+v")
    except Exception:
        keyboard.send("ctrl+v")
    time.sleep(0.05)


class EnhancerUI:
    BG = "#1e1e2e"
    FG = "#cdd6f4"
    ACCENT = "#89b2fa"
    GREEN = "#a6e3a1"
    RED = "#f38ba8"
    CARD = "#313244"

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self._popup = None

    def call(self, fn, *args):
        self.root.after(0, lambda: fn(*args))

    def run(self):
        self.root.mainloop()

    def show_status(self, message, color=None):
        self._destroy_popup()
        color = color or self.ACCENT
        win = self._make_window(360, 90)
        tk.Label(win, text=message, bg=self.BG, fg=color,
                 font=("Segoe UI", 11, "bold"), wraplength=330,
                 justify="center").pack(expand=True, fill="both", padx=16, pady=16)
        self._popup = win
        win.after(2500, lambda: self._destroy_if(win))


    def show_result(self, original, enhanced):
        self._destroy_popup()
        win = self._make_window(560, 440)
        tk.Label(win, text="Enhanced Prompt", bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        box = scrolledtext.ScrolledText(win, wrap="word", bg=self.CARD, fg=self.FG,
                        insertbackground=self.FG, font=("Consolas", 11),
                        relief="flat", borderwidth=0, height=12)
        box.insert("1.0", enhanced)
        box.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        btn_row = tk.Frame(win, bg=self.BG)
        btn_row.pack(fill="x", padx=18, pady=(0, 16))

        def approve():
            final_text = box.get("1.0", "end-1c")
            self._destroy_if(win)
            self.root.after(250, lambda: self._do_replace(final_text))

        def decline():
            self._destroy_if(win)

        tk.Button(btn_row, text="Approve", command=approve, bg=self.GREEN,
                  fg="#1e1e2e", font=("Segoe UI", 11, "bold"), relief="flat",
                  activebackground="#94d3a2", cursor="hand2", padx=20,
                  pady=8).pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Decline", command=decline, bg=self.RED,
                  fg="#1e1e2e", font=("Segoe UI", 11, "bold"), relief="flat",
                  activebackground="#f59ab0", cursor="hand2", padx=20,
                  pady=8).pack(side="right")
        tk.Label(btn_row, text="(edit above before approving)", bg=self.BG,
                 fg="#7f849c", font=("Segoe UI", 8)).pack(side="left")
        self._popup = win
        win.bind("<Escape>", lambda e: decline())

    def _do_replace(self, text):
        try:
            replace_selection_with(text)
        except Exception as exc:
            self.show_status("Paste failed: %s" % exc, self.RED)


    def _make_window(self, width, height):
        win = tk.Toplevel(self.root)
        win.configure(bg=self.BG)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.98)
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = sw - width - 40
        y = sh - height - 80
        win.geometry("%dx%d+%d+%d" % (width, height, x, y))
        win.configure(highlightbackground=self.ACCENT, highlightthickness=1)
        self._enable_drag(win)
        return win

    def _enable_drag(self, win):
        state = {"x": 0, "y": 0}
        def start(e):
            state["x"], state["y"] = e.x, e.y
        def move(e):
            win.geometry("+%d+%d" % (win.winfo_x() + e.x - state["x"],
                                 win.winfo_y() + e.y - state["y"]))
        win.bind("<Button-1>", start)
        win.bind("<B1-Motion>", move)

    def _destroy_if(self, win):
        try:
            if win and win.winfo_exists():
                win.destroy()
        except Exception:
            pass
        if win is self._popup:
            self._popup = None

    def _destroy_popup(self):
        self._destroy_if(self._popup)


ui = EnhancerUI()
_busy = threading.Lock()


def on_hotkey():
    if not _busy.acquire(blocking=False):
        return
    threading.Thread(target=_worker, daemon=True).start()


def _worker():
    try:
        selected = get_selected_text()
        if not selected.strip():
            ui.call(ui.show_status, "No text selected. Select a prompt first.", EnhancerUI.RED)
            return
        ui.call(ui.show_status, "Enhancing prompt...", EnhancerUI.ACCENT)
        enhanced = enhance_prompt(selected)
        ui.call(ui.show_result, selected, enhanced)
    except Exception as exc:
        ui.call(ui.show_status, "Error: %s" % exc, EnhancerUI.RED)
    finally:
        _busy.release()


def main():
    if keyboard is None or pyperclip is None:
        print("Missing dependencies. Run: pip install -r requirements.txt")
        sys.exit(1)
    if not API_KEY:
        print("WARNING: API_KEY not set. Copy .env.example to .env and fill it in.")
    print("=" * 56)
    print("  AI Prompt Enhancer is running")
    print("  Hotkey : " + HOTKEY)
    print("  Model  : " + MODEL_ID)
    print("  Base   : " + BASE_URL)
    print("  Select text anywhere, then press the hotkey.")
    print("  Press Ctrl+C here to quit.")
    print("=" * 56)
    try:
        keyboard.add_hotkey(HOTKEY, on_hotkey)
    except Exception as exc:
        print("Failed to register hotkey: %s" % exc)
        print("Try running this terminal as Administrator.")
        sys.exit(1)
    ui.run()


if __name__ == "__main__":
    main()
