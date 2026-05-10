import configparser
import ctypes
import sys
from pathlib import Path
from tkinter import BooleanVar, HORIZONTAL, Label, StringVar, Tk, Toplevel, ttk

try:
    from PIL import Image, ImageTk
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it with: pip install pillow"
    ) from exc


APP_NAME = "SimpleCross"
TRANSPARENT_COLOR = "magenta"
DEFAULT_SIZE = 64
DEFAULT_OPACITY = 1.0
DEFAULT_HIDDEN = False
DEFAULT_X_OFFSET = 0
DEFAULT_Y_OFFSET = 0
MIN_SIZE = 1
MAX_SIZE = 256
MIN_OPACITY = 0.0
MAX_OPACITY = 1.0
MIN_OFFSET = -500
MAX_OFFSET = 500
ALPHA_KEY_THRESHOLD = 8
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = app_dir()
CROSSHAIRS_DIR = BASE_DIR / "crosshairs"
SETTINGS_PATH = BASE_DIR / "settings.ini"


class Settings:
    def __init__(self, path: Path):
        self.path = path
        self.size = DEFAULT_SIZE
        self.opacity = DEFAULT_OPACITY
        self.hidden = DEFAULT_HIDDEN
        self.x_offset = DEFAULT_X_OFFSET
        self.y_offset = DEFAULT_Y_OFFSET
        self.crosshair = ""
        self._loaded = {}

    def load(self) -> None:
        parser = configparser.ConfigParser()
        parser.read(self.path, encoding="utf-8")
        section = parser["SimpleCross"] if parser.has_section("SimpleCross") else {}

        self.size = self._clamp_int(
            self._read_value(section, "size", DEFAULT_SIZE),
            MIN_SIZE,
            MAX_SIZE,
            DEFAULT_SIZE,
        )
        self.opacity = self._clamp_float(
            self._read_value(section, "opacity", DEFAULT_OPACITY),
            MIN_OPACITY,
            MAX_OPACITY,
            DEFAULT_OPACITY,
        )
        self.hidden = self._clamp_bool(
            self._read_value(section, "hidden", DEFAULT_HIDDEN),
            DEFAULT_HIDDEN,
        )
        self.x_offset = self._clamp_int(
            self._read_value(section, "x_offset", DEFAULT_X_OFFSET),
            MIN_OFFSET,
            MAX_OFFSET,
            DEFAULT_X_OFFSET,
        )
        self.y_offset = self._clamp_int(
            self._read_value(section, "y_offset", DEFAULT_Y_OFFSET),
            MIN_OFFSET,
            MAX_OFFSET,
            DEFAULT_Y_OFFSET,
        )
        self.crosshair = str(self._read_value(section, "crosshair", "")).strip()
        self._loaded = self.as_dict()

    def save_if_changed(self) -> None:
        current = self.as_dict()
        if current == self._loaded:
            return

        parser = configparser.ConfigParser()
        parser["SimpleCross"] = {
            "size": str(current["size"]),
            "opacity": f"{current['opacity']:.2f}",
            "hidden": str(current["hidden"]),
            "x_offset": str(current["x_offset"]),
            "y_offset": str(current["y_offset"]),
            "crosshair": current["crosshair"],
        }
        with self.path.open("w", encoding="utf-8") as file:
            parser.write(file)
        self._loaded = current

    def as_dict(self) -> dict:
        return {
            "size": int(self.size),
            "opacity": round(float(self.opacity), 2),
            "hidden": bool(self.hidden),
            "x_offset": int(self.x_offset),
            "y_offset": int(self.y_offset),
            "crosshair": self.crosshair,
        }

    @staticmethod
    def _read_value(section, key, default):
        try:
            return section.get(key, default)
        except AttributeError:
            return default

    @staticmethod
    def _clamp_int(value, minimum, maximum, default):
        try:
            number = int(float(value))
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, number))

    @staticmethod
    def _clamp_float(value, minimum, maximum, default):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, number))

    @staticmethod
    def _clamp_bool(value, default):
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "yes", "true", "on"}:
            return True
        if normalized in {"0", "no", "false", "off"}:
            return False
        return default


class SimpleCrossApp:
    def __init__(self):
        CROSSHAIRS_DIR.mkdir(exist_ok=True)

        self.settings = Settings(SETTINGS_PATH)
        self.settings.load()
        self.crosshairs = self._find_crosshairs()

        if self.crosshairs and self.settings.crosshair not in self.crosshairs:
            self.settings.crosshair = self.crosshairs[0]

        self.root = Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._save_after_id = None
        self._updating_controls = False

        self.crosshair_window = Toplevel(self.root)
        self.crosshair_window.overrideredirect(True)
        self.crosshair_window.attributes("-topmost", True)
        self.crosshair_window.configure(bg=TRANSPARENT_COLOR)
        if sys.platform != "win32":
            self.crosshair_window.attributes("-transparentcolor", TRANSPARENT_COLOR)

        self.crosshair_label = Label(
            self.crosshair_window,
            bg=TRANSPARENT_COLOR,
            borderwidth=0,
            highlightthickness=0,
        )
        self.crosshair_label.pack()
        self.crosshair_photo = None

        self.settings_window = Toplevel(self.root)
        self.settings_window.title("SimpleCross Settings")
        self.settings_window.resizable(False, False)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close)

        self.size_var = StringVar(value=str(self.settings.size))
        self.opacity_var = StringVar(value=str(int(self.settings.opacity * 100)))
        self.x_offset_var = StringVar(value=str(self.settings.x_offset))
        self.y_offset_var = StringVar(value=str(self.settings.y_offset))
        self.hidden_var = BooleanVar(value=self.settings.hidden)
        self.crosshair_var = StringVar(value=self.settings.crosshair)

        self._build_settings_window()
        self._refresh_crosshair()

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        if self._save_after_id is not None:
            self.root.after_cancel(self._save_after_id)
            self._save_after_id = None
        self.settings.save_if_changed()
        self.root.destroy()

    def _find_crosshairs(self) -> list[str]:
        return sorted(
            path.name
            for path in CROSSHAIRS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() == ".png"
        )

    def _build_settings_window(self) -> None:
        frame = ttk.Frame(self.settings_window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Crosshair").grid(row=0, column=0, sticky="w")
        self.crosshair_combo = ttk.Combobox(
            frame,
            textvariable=self.crosshair_var,
            values=self.crosshairs,
            state="readonly" if self.crosshairs else "disabled",
            width=28,
        )
        self.crosshair_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.crosshair_combo.bind("<<ComboboxSelected>>", self._on_crosshair_changed)

        ttk.Label(frame, text="Size").grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.size_scale = ttk.Scale(
            frame,
            from_=MIN_SIZE,
            to=MAX_SIZE,
            orient=HORIZONTAL,
            command=self._on_size_changed,
        )
        self.size_scale.set(self.settings.size)
        self.size_scale.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(12, 0))
        size_entry = ttk.Entry(frame, textvariable=self.size_var, width=5)
        size_entry.grid(
            row=1, column=2, sticky="e", padx=(8, 0), pady=(12, 0)
        )
        size_entry.bind("<Return>", self._commit_size_entry)
        size_entry.bind("<FocusOut>", self._commit_size_entry)

        ttk.Label(frame, text="Opacity").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.opacity_scale = ttk.Scale(
            frame,
            from_=MIN_OPACITY * 100,
            to=MAX_OPACITY * 100,
            orient=HORIZONTAL,
            command=self._on_opacity_changed,
        )
        self.opacity_scale.set(self.settings.opacity * 100)
        self.opacity_scale.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(12, 0))
        opacity_entry = ttk.Entry(frame, textvariable=self.opacity_var, width=5)
        opacity_entry.grid(
            row=2, column=2, sticky="e", padx=(8, 0), pady=(12, 0)
        )
        opacity_entry.bind("<Return>", self._commit_opacity_entry)
        opacity_entry.bind("<FocusOut>", self._commit_opacity_entry)
        ttk.Checkbutton(
            frame,
            text="Hide",
            variable=self.hidden_var,
            command=self._on_hidden_changed,
        ).grid(row=2, column=3, sticky="w", padx=(10, 0), pady=(12, 0))

        ttk.Label(frame, text="X").grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.x_offset_scale = ttk.Scale(
            frame,
            from_=MIN_OFFSET,
            to=MAX_OFFSET,
            orient=HORIZONTAL,
            command=self._on_x_offset_changed,
        )
        self.x_offset_scale.set(self.settings.x_offset)
        self.x_offset_scale.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(12, 0))
        x_offset_entry = ttk.Entry(frame, textvariable=self.x_offset_var, width=5)
        x_offset_entry.grid(row=3, column=2, sticky="e", padx=(8, 0), pady=(12, 0))
        x_offset_entry.bind("<Return>", self._commit_x_offset_entry)
        x_offset_entry.bind("<FocusOut>", self._commit_x_offset_entry)

        ttk.Label(frame, text="Y").grid(row=4, column=0, sticky="w", pady=(12, 0))
        self.y_offset_scale = ttk.Scale(
            frame,
            from_=MIN_OFFSET,
            to=MAX_OFFSET,
            orient=HORIZONTAL,
            command=self._on_y_offset_changed,
        )
        self.y_offset_scale.set(self.settings.y_offset)
        self.y_offset_scale.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(12, 0))
        y_offset_entry = ttk.Entry(frame, textvariable=self.y_offset_var, width=5)
        y_offset_entry.grid(row=4, column=2, sticky="e", padx=(8, 0), pady=(12, 0))
        y_offset_entry.bind("<Return>", self._commit_y_offset_entry)
        y_offset_entry.bind("<FocusOut>", self._commit_y_offset_entry)

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(16, 0))
        ttk.Button(buttons, text="Refresh list", command=self._refresh_crosshair_list).pack(
            side="left"
        )

        if not self.crosshairs:
            ttk.Label(
                frame,
                text="Put PNG files into the crosshairs folder.",
                foreground="red",
            ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(12, 0))

    def _on_crosshair_changed(self, _event=None) -> None:
        self.settings.crosshair = self.crosshair_var.get()
        self.settings.save_if_changed()
        self._refresh_crosshair()

    def _on_size_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.size = Settings._clamp_int(value, MIN_SIZE, MAX_SIZE, DEFAULT_SIZE)
        self.size_var.set(str(self.settings.size))
        self._schedule_save()
        self._refresh_crosshair()

    def _on_opacity_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        percent = Settings._clamp_float(value, MIN_OPACITY * 100, MAX_OPACITY * 100, 100)
        percent = int(percent + 0.5)
        self.settings.opacity = round(percent / 100, 2)
        self.opacity_var.set(str(percent))
        self._apply_crosshair_window_styles()
        self._schedule_save()

    def _on_x_offset_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.x_offset = Settings._clamp_int(
            value, MIN_OFFSET, MAX_OFFSET, DEFAULT_X_OFFSET
        )
        self.x_offset_var.set(str(self.settings.x_offset))
        self._schedule_save()
        self._refresh_crosshair_position()

    def _on_y_offset_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.y_offset = Settings._clamp_int(
            value, MIN_OFFSET, MAX_OFFSET, DEFAULT_Y_OFFSET
        )
        self.y_offset_var.set(str(self.settings.y_offset))
        self._schedule_save()
        self._refresh_crosshair_position()

    def _commit_size_entry(self, _event=None):
        size = Settings._clamp_int(self.size_var.get(), MIN_SIZE, MAX_SIZE, self.settings.size)
        self.settings.size = size
        self.size_var.set(str(size))
        self._updating_controls = True
        self.size_scale.set(size)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_crosshair()
        return "break"

    def _commit_opacity_entry(self, _event=None):
        percent = Settings._clamp_float(
            self.opacity_var.get(),
            MIN_OPACITY * 100,
            MAX_OPACITY * 100,
            self.settings.opacity * 100,
        )
        percent = int(percent + 0.5)
        self.settings.opacity = round(percent / 100, 2)
        self.opacity_var.set(str(percent))
        self._updating_controls = True
        self.opacity_scale.set(percent)
        self._updating_controls = False
        self._apply_crosshair_window_styles()
        self.settings.save_if_changed()
        return "break"

    def _commit_x_offset_entry(self, _event=None):
        x_offset = Settings._clamp_int(
            self.x_offset_var.get(), MIN_OFFSET, MAX_OFFSET, self.settings.x_offset
        )
        self.settings.x_offset = x_offset
        self.x_offset_var.set(str(x_offset))
        self._updating_controls = True
        self.x_offset_scale.set(x_offset)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_crosshair_position()
        return "break"

    def _commit_y_offset_entry(self, _event=None):
        y_offset = Settings._clamp_int(
            self.y_offset_var.get(), MIN_OFFSET, MAX_OFFSET, self.settings.y_offset
        )
        self.settings.y_offset = y_offset
        self.y_offset_var.set(str(y_offset))
        self._updating_controls = True
        self.y_offset_scale.set(y_offset)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_crosshair_position()
        return "break"

    def _on_hidden_changed(self) -> None:
        self.settings.hidden = bool(self.hidden_var.get())
        self.settings.save_if_changed()
        self._refresh_crosshair()

    def _schedule_save(self) -> None:
        if self._save_after_id is not None:
            self.root.after_cancel(self._save_after_id)
        self._save_after_id = self.root.after(400, self._save_settings)

    def _save_settings(self) -> None:
        self._save_after_id = None
        self.settings.save_if_changed()

    def _refresh_crosshair_list(self) -> None:
        self.crosshairs = self._find_crosshairs()
        self.crosshair_combo.configure(
            values=self.crosshairs,
            state="readonly" if self.crosshairs else "disabled",
        )

        if self.crosshairs and self.settings.crosshair not in self.crosshairs:
            self.settings.crosshair = self.crosshairs[0]
            self.crosshair_var.set(self.settings.crosshair)
            self.settings.save_if_changed()
        self._refresh_crosshair()

    def _refresh_crosshair(self) -> None:
        selected = self.settings.crosshair
        image_path = CROSSHAIRS_DIR / selected if selected else None

        if self.settings.hidden or not image_path or not image_path.exists():
            self.crosshair_label.configure(image="")
            self.crosshair_photo = None
            self.crosshair_window.withdraw()
            return

        image = self._load_scaled_image(image_path)

        self.crosshair_photo = ImageTk.PhotoImage(image)
        self.crosshair_label.configure(image=self.crosshair_photo)
        self.crosshair_window.deiconify()
        self._center_crosshair(image.width, image.height)
        self._apply_crosshair_window_styles()

    def _refresh_crosshair_position(self) -> None:
        if self.crosshair_photo is None or self.settings.hidden:
            return
        self._center_crosshair(self.crosshair_photo.width(), self.crosshair_photo.height())

    def _apply_crosshair_window_styles(self) -> None:
        if sys.platform != "win32":
            self.crosshair_window.attributes("-alpha", self.settings.opacity)
            return

        self.crosshair_window.update_idletasks()
        user32 = ctypes.windll.user32
        get_parent = user32.GetParent
        get_window_long = user32.GetWindowLongPtrW
        set_window_long = user32.SetWindowLongPtrW
        set_layered_window_attributes = user32.SetLayeredWindowAttributes
        set_window_pos = user32.SetWindowPos

        get_parent.argtypes = [ctypes.c_void_p]
        get_parent.restype = ctypes.c_void_p
        get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
        get_window_long.restype = ctypes.c_longlong
        set_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_longlong]
        set_window_long.restype = ctypes.c_longlong
        set_layered_window_attributes.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_ubyte,
            ctypes.c_uint,
        ]
        set_layered_window_attributes.restype = ctypes.c_int
        set_window_pos.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        set_window_pos.restype = ctypes.c_int

        child_hwnd = self.crosshair_window.winfo_id()
        hwnd = get_parent(child_hwnd)
        if not hwnd:
            hwnd = child_hwnd

        child_style = get_window_long(child_hwnd, GWL_EXSTYLE)
        child_style |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        set_window_long(child_hwnd, GWL_EXSTYLE, child_style)

        style = get_window_long(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        set_window_long(hwnd, GWL_EXSTYLE, style)
        opacity = max(0, min(255, int(self.settings.opacity * 255)))
        set_layered_window_attributes(
            hwnd,
            self._colorref(TRANSPARENT_COLOR),
            opacity,
            LWA_COLORKEY | LWA_ALPHA,
        )
        set_window_pos(
            hwnd,
            None,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

    @staticmethod
    def _colorref(color_name: str) -> int:
        colors = {
            "magenta": (255, 0, 255),
        }
        red, green, blue = colors[color_name]
        return red | (green << 8) | (blue << 16)

    def _load_scaled_image(self, image_path: Path) -> Image.Image:
        image = Image.open(image_path).convert("RGBA")
        width, height = image.size

        if width <= 0 or height <= 0:
            return self._prepare_for_color_key(image)

        scale = self.settings.size / max(width, height)
        new_size = (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        )
        image = image.resize(new_size, Image.NEAREST)

        return self._prepare_for_color_key(image)

    def _prepare_for_color_key(self, image: Image.Image) -> Image.Image:
        mask = image.getchannel("A").point(
            lambda alpha: 255 if alpha > ALPHA_KEY_THRESHOLD else 0
        )
        background = Image.new("RGB", image.size, TRANSPARENT_COLOR)
        return Image.composite(image.convert("RGB"), background, mask)

    def _center_crosshair(self, width: int, height: int) -> None:
        screen_width = self.crosshair_window.winfo_screenwidth()
        screen_height = self.crosshair_window.winfo_screenheight()
        x = (screen_width - width) // 2 + self.settings.x_offset
        y = (screen_height - height) // 2 + self.settings.y_offset
        self.crosshair_window.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    SimpleCrossApp().run()
