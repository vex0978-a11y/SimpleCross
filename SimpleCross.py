import configparser
import ctypes
import sys
from pathlib import Path
from tkinter import BooleanVar, Frame, HORIZONTAL, Label, StringVar, Tk, Toplevel, ttk

try:
    from PIL import Image, ImageChops, ImageFilter, ImageTk
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it with: pip install pillow"
    ) from exc


APP_NAME = "SimpleCross"
TRANSPARENT_COLOR = "magenta"
TRANSPARENT_COLOR_CANDIDATES = (
    (255, 0, 255),
    (0, 255, 0),
    (0, 255, 255),
    (255, 255, 0),
    (0, 0, 255),
    (255, 0, 0),
)
DEFAULT_SIZE = 64
DEFAULT_OPACITY = 1.0
DEFAULT_HIDDEN = False
DEFAULT_X_OFFSET = 0
DEFAULT_Y_OFFSET = 0
DEFAULT_ROTATION = 0
DEFAULT_RED = 255
DEFAULT_GREEN = 255
DEFAULT_BLUE = 255
DEFAULT_OUTLINE_RED = 0
DEFAULT_OUTLINE_GREEN = 0
DEFAULT_OUTLINE_BLUE = 0
DEFAULT_OUTLINE_OPACITY = 0.0
DEFAULT_OUTLINE_THICKNESS = 0
DEFAULT_AIM_HOTKEY = "MouseRight"
DEFAULT_HIDE_HOTKEY = "Ctrl+H"
MIN_SIZE = 1
MAX_SIZE = 256
MIN_OPACITY = 0.0
MAX_OPACITY = 1.0
MIN_OFFSET = -500
MAX_OFFSET = 500
MIN_ROTATION = 0
MAX_ROTATION = 360
MIN_RGB = 0
MAX_RGB = 255
MIN_OUTLINE_THICKNESS = 0
MAX_OUTLINE_THICKNESS = 32
SHAPE_PREVIEW_SIZE = 56
COLOR_PREVIEW_SIZE = 36
ALPHA_KEY_THRESHOLD = 8
HOTKEY_POLL_MS = 25
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

VK_ALIASES = {
    "BackSpace": 0x08,
    "Tab": 0x09,
    "Return": 0x0D,
    "Escape": 0x1B,
    "Space": 0x20,
    "Prior": 0x21,
    "Next": 0x22,
    "End": 0x23,
    "Home": 0x24,
    "Left": 0x25,
    "Up": 0x26,
    "Right": 0x27,
    "Down": 0x28,
    "Insert": 0x2D,
    "Delete": 0x2E,
    "Shift": 0x10,
    "Control": 0x11,
    "Alt": 0x12,
    "MouseLeft": 0x01,
    "MouseRight": 0x02,
    "MouseMiddle": 0x04,
    "MouseX1": 0x05,
    "MouseX2": 0x06,
}

for index in range(1, 13):
    VK_ALIASES[f"F{index}"] = 0x70 + index - 1


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
        self.rotation = DEFAULT_ROTATION
        self.red = DEFAULT_RED
        self.green = DEFAULT_GREEN
        self.blue = DEFAULT_BLUE
        self.outline_red = DEFAULT_OUTLINE_RED
        self.outline_green = DEFAULT_OUTLINE_GREEN
        self.outline_blue = DEFAULT_OUTLINE_BLUE
        self.outline_opacity = DEFAULT_OUTLINE_OPACITY
        self.outline_thickness = DEFAULT_OUTLINE_THICKNESS
        self.aim_hotkey = DEFAULT_AIM_HOTKEY
        self.hide_hotkey = DEFAULT_HIDE_HOTKEY
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
        self.rotation = self._clamp_int(
            self._read_value(section, "rotation", DEFAULT_ROTATION),
            MIN_ROTATION,
            MAX_ROTATION,
            DEFAULT_ROTATION,
        )
        self.red = self._clamp_int(
            self._read_value(section, "red", DEFAULT_RED),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_RED,
        )
        self.green = self._clamp_int(
            self._read_value(section, "green", DEFAULT_GREEN),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_GREEN,
        )
        self.blue = self._clamp_int(
            self._read_value(section, "blue", DEFAULT_BLUE),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_BLUE,
        )
        self.outline_red = self._clamp_int(
            self._read_value(section, "outline_red", DEFAULT_OUTLINE_RED),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_OUTLINE_RED,
        )
        self.outline_green = self._clamp_int(
            self._read_value(section, "outline_green", DEFAULT_OUTLINE_GREEN),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_OUTLINE_GREEN,
        )
        self.outline_blue = self._clamp_int(
            self._read_value(section, "outline_blue", DEFAULT_OUTLINE_BLUE),
            MIN_RGB,
            MAX_RGB,
            DEFAULT_OUTLINE_BLUE,
        )
        self.outline_opacity = self._clamp_float(
            self._read_value(section, "outline_opacity", DEFAULT_OUTLINE_OPACITY),
            MIN_OPACITY,
            MAX_OPACITY,
            DEFAULT_OUTLINE_OPACITY,
        )
        self.outline_thickness = self._clamp_int(
            self._read_value(section, "outline_thickness", DEFAULT_OUTLINE_THICKNESS),
            MIN_OUTLINE_THICKNESS,
            MAX_OUTLINE_THICKNESS,
            DEFAULT_OUTLINE_THICKNESS,
        )
        self.aim_hotkey = str(
            self._read_value(section, "aim_hotkey", DEFAULT_AIM_HOTKEY)
        ).strip() or DEFAULT_AIM_HOTKEY
        self.hide_hotkey = str(
            self._read_value(section, "hide_hotkey", DEFAULT_HIDE_HOTKEY)
        ).strip() or DEFAULT_HIDE_HOTKEY
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
            "rotation": str(current["rotation"]),
            "red": str(current["red"]),
            "green": str(current["green"]),
            "blue": str(current["blue"]),
            "outline_red": str(current["outline_red"]),
            "outline_green": str(current["outline_green"]),
            "outline_blue": str(current["outline_blue"]),
            "outline_opacity": f"{current['outline_opacity']:.2f}",
            "outline_thickness": str(current["outline_thickness"]),
            "aim_hotkey": current["aim_hotkey"],
            "hide_hotkey": current["hide_hotkey"],
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
            "rotation": int(self.rotation),
            "red": int(self.red),
            "green": int(self.green),
            "blue": int(self.blue),
            "outline_red": int(self.outline_red),
            "outline_green": int(self.outline_green),
            "outline_blue": int(self.outline_blue),
            "outline_opacity": round(float(self.outline_opacity), 2),
            "outline_thickness": int(self.outline_thickness),
            "aim_hotkey": self.aim_hotkey,
            "hide_hotkey": self.hide_hotkey,
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
        self._hotkey_after_id = None
        self._updating_controls = False
        self._aim_pressed = False
        self._hide_pressed = False
        self._shape_preview_photo = None
        self._color_preview_photo = None

        self.crosshair_window = Toplevel(self.root)
        self.crosshair_window.overrideredirect(True)
        self.crosshair_window.attributes("-topmost", True)
        self.crosshair_window.configure(bg=self._transparent_tk_color())
        if sys.platform != "win32":
            self.crosshair_window.attributes(
                "-transparentcolor", self._transparent_tk_color()
            )

        self.crosshair_label = Label(
            self.crosshair_window,
            bg=self._transparent_tk_color(),
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
        self.rotation_var = StringVar(value=str(self.settings.rotation))
        self.red_var = StringVar(value=str(self.settings.red))
        self.green_var = StringVar(value=str(self.settings.green))
        self.blue_var = StringVar(value=str(self.settings.blue))
        self.outline_red_var = StringVar(value=str(self.settings.outline_red))
        self.outline_green_var = StringVar(value=str(self.settings.outline_green))
        self.outline_blue_var = StringVar(value=str(self.settings.outline_blue))
        self.outline_opacity_var = StringVar(
            value=str(int(self.settings.outline_opacity * 100))
        )
        self.outline_thickness_var = StringVar(
            value=str(self.settings.outline_thickness)
        )
        self.hidden_var = BooleanVar(value=self.settings.hidden)
        self.crosshair_var = StringVar(value=self.settings.crosshair)
        self.aim_hotkey_var = StringVar(value=self.settings.aim_hotkey)
        self.hide_hotkey_var = StringVar(value=self.settings.hide_hotkey)

        self._build_settings_window()
        self._refresh_previews()
        self._refresh_crosshair()
        self._poll_hotkeys()

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        if self._save_after_id is not None:
            self.root.after_cancel(self._save_after_id)
            self._save_after_id = None
        if self._hotkey_after_id is not None:
            self.root.after_cancel(self._hotkey_after_id)
            self._hotkey_after_id = None
        self.settings.save_if_changed()
        self.root.destroy()

    def _find_crosshairs(self) -> list[str]:
        return sorted(
            path.name
            for path in CROSSHAIRS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() == ".png"
        )

    def _build_settings_window(self) -> None:
        notebook = ttk.Notebook(self.settings_window)
        notebook.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        shape_tab = ttk.Frame(notebook, padding=8)
        color_tab = ttk.Frame(notebook, padding=8)
        offset_tab = ttk.Frame(notebook, padding=8)
        hotkeys_tab = ttk.Frame(notebook, padding=8)
        notebook.add(shape_tab, text="Shape")
        notebook.add(color_tab, text="Color")
        notebook.add(offset_tab, text="Offset")
        notebook.add(hotkeys_tab, text="Hotkeys")

        self._build_shape_tab(shape_tab)
        self._build_color_tab(color_tab)
        self._build_offset_tab(offset_tab)
        self._build_hotkeys_tab(hotkeys_tab)

    def _build_shape_tab(self, frame: ttk.Frame) -> None:
        self.shape_preview_box = Frame(
            frame,
            width=SHAPE_PREVIEW_SIZE,
            height=SHAPE_PREVIEW_SIZE,
            bg="black",
            borderwidth=1,
            relief="solid",
        )
        self.shape_preview_box.grid(
            row=0, column=0, rowspan=7, sticky="n", padx=(0, 8)
        )
        self.shape_preview_box.grid_propagate(False)
        self.shape_preview = Label(
            self.shape_preview_box,
            bg="black",
            borderwidth=0,
            highlightthickness=0,
        )
        self.shape_preview.pack(fill="both", expand=True)

        ttk.Label(frame, text="PNG").grid(row=0, column=1, sticky="w")
        self.crosshair_combo = ttk.Combobox(
            frame,
            textvariable=self.crosshair_var,
            values=self.crosshairs,
            state="readonly" if self.crosshairs else "disabled",
            width=24,
        )
        self.crosshair_combo.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        self.crosshair_combo.bind("<<ComboboxSelected>>", self._on_crosshair_changed)

        self.size_scale = self._add_scale_row(
            frame,
            row=1,
            label="Size",
            variable=self.size_var,
            minimum=MIN_SIZE,
            maximum=MAX_SIZE,
            value=self.settings.size,
            command=self._on_size_changed,
            commit=self._commit_size_entry,
        )
        self.opacity_scale = self._add_scale_row(
            frame,
            row=2,
            label="Opacity",
            variable=self.opacity_var,
            minimum=MIN_OPACITY * 100,
            maximum=MAX_OPACITY * 100,
            value=self.settings.opacity * 100,
            command=self._on_opacity_changed,
            commit=self._commit_opacity_entry,
        )
        self.outline_opacity_scale = self._add_scale_row(
            frame,
            row=3,
            label="Outline opacity",
            variable=self.outline_opacity_var,
            minimum=MIN_OPACITY * 100,
            maximum=MAX_OPACITY * 100,
            value=self.settings.outline_opacity * 100,
            command=self._on_outline_opacity_changed,
            commit=self._commit_outline_opacity_entry,
        )
        self.outline_thickness_scale = self._add_scale_row(
            frame,
            row=4,
            label="Outline width",
            variable=self.outline_thickness_var,
            minimum=MIN_OUTLINE_THICKNESS,
            maximum=MAX_OUTLINE_THICKNESS,
            value=self.settings.outline_thickness,
            command=self._on_outline_thickness_changed,
            commit=self._commit_outline_thickness_entry,
        )

        ttk.Checkbutton(
            frame,
            text="Hide",
            variable=self.hidden_var,
            command=self._on_hidden_changed,
        ).grid(row=5, column=1, columnspan=3, sticky="w", pady=(8, 0))

        ttk.Button(frame, text="Refresh list", command=self._refresh_crosshair_list).grid(
            row=6, column=1, columnspan=3, sticky="w", pady=(8, 0)
        )

        if not self.crosshairs:
            ttk.Label(
                frame,
                text="Put PNG files into the crosshairs folder.",
                foreground="red",
            ).grid(row=7, column=0, columnspan=4, sticky="w", pady=(12, 0))

    def _build_color_tab(self, frame: ttk.Frame) -> None:
        self.color_preview = Frame(
            frame,
            width=COLOR_PREVIEW_SIZE,
            height=COLOR_PREVIEW_SIZE,
            bg=self._rgb_hex(),
            borderwidth=1,
            relief="solid",
        )
        self.color_preview.grid(row=0, column=0, rowspan=9, sticky="n", padx=(0, 8))
        self.color_preview.grid_propagate(False)

        ttk.Label(frame, text="Crosshair").grid(row=0, column=1, columnspan=3, sticky="w")
        self.red_scale = self._add_scale_row(
            frame,
            row=1,
            label="Red",
            variable=self.red_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.red,
            command=lambda value: self._on_rgb_changed("red", value),
            commit=lambda event=None: self._commit_rgb_entry("red"),
        )
        self.green_scale = self._add_scale_row(
            frame,
            row=2,
            label="Green",
            variable=self.green_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.green,
            command=lambda value: self._on_rgb_changed("green", value),
            commit=lambda event=None: self._commit_rgb_entry("green"),
        )
        self.blue_scale = self._add_scale_row(
            frame,
            row=3,
            label="Blue",
            variable=self.blue_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.blue,
            command=lambda value: self._on_rgb_changed("blue", value),
            commit=lambda event=None: self._commit_rgb_entry("blue"),
        )
        ttk.Label(frame, text="Outline").grid(
            row=4, column=1, columnspan=3, sticky="w", pady=(10, 0)
        )
        self.outline_red_scale = self._add_scale_row(
            frame,
            row=5,
            label="Red",
            variable=self.outline_red_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.outline_red,
            command=lambda value: self._on_rgb_changed("outline_red", value),
            commit=lambda event=None: self._commit_rgb_entry("outline_red"),
        )
        self.outline_green_scale = self._add_scale_row(
            frame,
            row=6,
            label="Green",
            variable=self.outline_green_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.outline_green,
            command=lambda value: self._on_rgb_changed("outline_green", value),
            commit=lambda event=None: self._commit_rgb_entry("outline_green"),
        )
        self.outline_blue_scale = self._add_scale_row(
            frame,
            row=7,
            label="Blue",
            variable=self.outline_blue_var,
            minimum=MIN_RGB,
            maximum=MAX_RGB,
            value=self.settings.outline_blue,
            command=lambda value: self._on_rgb_changed("outline_blue", value),
            commit=lambda event=None: self._commit_rgb_entry("outline_blue"),
        )

    def _build_offset_tab(self, frame: ttk.Frame) -> None:
        self.x_offset_scale = self._add_scale_row(
            frame,
            row=0,
            label="X",
            variable=self.x_offset_var,
            minimum=MIN_OFFSET,
            maximum=MAX_OFFSET,
            value=self.settings.x_offset,
            command=self._on_x_offset_changed,
            commit=self._commit_x_offset_entry,
        )
        self.y_offset_scale = self._add_scale_row(
            frame,
            row=1,
            label="Y",
            variable=self.y_offset_var,
            minimum=MIN_OFFSET,
            maximum=MAX_OFFSET,
            value=self.settings.y_offset,
            command=self._on_y_offset_changed,
            commit=self._commit_y_offset_entry,
        )
        self.rotation_scale = self._add_scale_row(
            frame,
            row=2,
            label="Rotation",
            variable=self.rotation_var,
            minimum=MIN_ROTATION,
            maximum=MAX_ROTATION,
            value=self.settings.rotation,
            command=self._on_rotation_changed,
            commit=self._commit_rotation_entry,
        )

    def _build_hotkeys_tab(self, frame: ttk.Frame) -> None:
        ttk.Label(frame, text="Aim").grid(row=0, column=0, sticky="w")
        aim_entry = ttk.Entry(frame, textvariable=self.aim_hotkey_var, width=14)
        aim_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        aim_entry.bind("<KeyPress>", lambda event: self._capture_hotkey(event, "aim"))
        aim_entry.bind("<ButtonPress>", lambda event: self._capture_mouse_hotkey(event, "aim"))

        ttk.Label(frame, text="Hide").grid(row=1, column=0, sticky="w", pady=(8, 0))
        hide_entry = ttk.Entry(frame, textvariable=self.hide_hotkey_var, width=14)
        hide_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        hide_entry.bind("<KeyPress>", lambda event: self._capture_hotkey(event, "hide"))
        hide_entry.bind("<ButtonPress>", lambda event: self._capture_mouse_hotkey(event, "hide"))

    def _add_scale_row(
        self,
        frame: ttk.Frame,
        row: int,
        label: str,
        variable: StringVar,
        minimum: float,
        maximum: float,
        value: float,
        command,
        commit,
    ) -> ttk.Scale:
        ttk.Label(frame, text=label).grid(row=row, column=1, sticky="w", pady=(7, 0))
        scale = ttk.Scale(
            frame,
            from_=minimum,
            to=maximum,
            orient=HORIZONTAL,
            command=command,
        )
        scale.set(value)
        scale.grid(row=row, column=2, sticky="ew", padx=(8, 0), pady=(7, 0))
        entry = ttk.Entry(frame, textvariable=variable, width=5)
        entry.grid(row=row, column=3, sticky="e", padx=(6, 0), pady=(7, 0))
        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        frame.columnconfigure(2, minsize=165)
        return scale

    def _on_crosshair_changed(self, _event=None) -> None:
        self.settings.crosshair = self.crosshair_var.get()
        self.settings.save_if_changed()
        self._refresh_previews()
        self._refresh_crosshair()

    def _on_size_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.size = Settings._clamp_int(value, MIN_SIZE, MAX_SIZE, DEFAULT_SIZE)
        self.size_var.set(str(self.settings.size))
        self._schedule_save()
        self._refresh_previews()
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

    def _on_outline_opacity_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        percent = Settings._clamp_float(value, MIN_OPACITY * 100, MAX_OPACITY * 100, 0)
        percent = int(percent + 0.5)
        self.settings.outline_opacity = round(percent / 100, 2)
        self.outline_opacity_var.set(str(percent))
        self._schedule_save()
        self._refresh_crosshair()

    def _on_outline_thickness_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.outline_thickness = Settings._clamp_int(
            value,
            MIN_OUTLINE_THICKNESS,
            MAX_OUTLINE_THICKNESS,
            DEFAULT_OUTLINE_THICKNESS,
        )
        self.outline_thickness_var.set(str(self.settings.outline_thickness))
        self._schedule_save()
        self._refresh_crosshair()

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

    def _on_rotation_changed(self, value: str) -> None:
        if self._updating_controls:
            return
        self.settings.rotation = Settings._clamp_int(
            value, MIN_ROTATION, MAX_ROTATION, DEFAULT_ROTATION
        )
        self.rotation_var.set(str(self.settings.rotation))
        self._schedule_save()
        self._refresh_previews()
        self._refresh_crosshair()

    def _on_rgb_changed(self, channel: str, value: str) -> None:
        if self._updating_controls:
            return
        number = Settings._clamp_int(value, MIN_RGB, MAX_RGB, DEFAULT_RED)
        setattr(self.settings, channel, number)
        getattr(self, f"{channel}_var").set(str(number))
        self._schedule_save()
        self._refresh_previews()
        self._refresh_crosshair()

    def _commit_size_entry(self, _event=None):
        size = Settings._clamp_int(self.size_var.get(), MIN_SIZE, MAX_SIZE, self.settings.size)
        self.settings.size = size
        self.size_var.set(str(size))
        self._updating_controls = True
        self.size_scale.set(size)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_previews()
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

    def _commit_outline_opacity_entry(self, _event=None):
        percent = Settings._clamp_float(
            self.outline_opacity_var.get(),
            MIN_OPACITY * 100,
            MAX_OPACITY * 100,
            self.settings.outline_opacity * 100,
        )
        percent = int(percent + 0.5)
        self.settings.outline_opacity = round(percent / 100, 2)
        self.outline_opacity_var.set(str(percent))
        self._updating_controls = True
        self.outline_opacity_scale.set(percent)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_crosshair()
        return "break"

    def _commit_outline_thickness_entry(self, _event=None):
        thickness = Settings._clamp_int(
            self.outline_thickness_var.get(),
            MIN_OUTLINE_THICKNESS,
            MAX_OUTLINE_THICKNESS,
            self.settings.outline_thickness,
        )
        self.settings.outline_thickness = thickness
        self.outline_thickness_var.set(str(thickness))
        self._updating_controls = True
        self.outline_thickness_scale.set(thickness)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_crosshair()
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

    def _commit_rotation_entry(self, _event=None):
        rotation = Settings._clamp_int(
            self.rotation_var.get(),
            MIN_ROTATION,
            MAX_ROTATION,
            self.settings.rotation,
        )
        self.settings.rotation = rotation
        self.rotation_var.set(str(rotation))
        self._updating_controls = True
        self.rotation_scale.set(rotation)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_previews()
        self._refresh_crosshair()
        return "break"

    def _commit_rgb_entry(self, channel: str):
        variable = getattr(self, f"{channel}_var")
        scale = getattr(self, f"{channel}_scale")
        current = getattr(self.settings, channel)
        number = Settings._clamp_int(variable.get(), MIN_RGB, MAX_RGB, current)
        setattr(self.settings, channel, number)
        variable.set(str(number))
        self._updating_controls = True
        scale.set(number)
        self._updating_controls = False
        self.settings.save_if_changed()
        self._refresh_previews()
        self._refresh_crosshair()
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
        self._refresh_previews()
        self._refresh_crosshair()

    def _refresh_previews(self) -> None:
        self._refresh_shape_preview()
        self._refresh_color_preview()

    def _refresh_shape_preview(self) -> None:
        selected = self.settings.crosshair
        image_path = CROSSHAIRS_DIR / selected if selected else None
        if not image_path or not image_path.exists():
            self.shape_preview.configure(image="")
            self._shape_preview_photo = None
            return

        image = self._load_shape_image(image_path)
        image = self._resize_to_fit(image, SHAPE_PREVIEW_SIZE - 10)
        image = self._colorize_image(image, (255, 255, 255))
        background = Image.new(
            "RGBA", (SHAPE_PREVIEW_SIZE, SHAPE_PREVIEW_SIZE), (0, 0, 0, 255)
        )
        x = (SHAPE_PREVIEW_SIZE - image.width) // 2
        y = (SHAPE_PREVIEW_SIZE - image.height) // 2
        background.alpha_composite(image, (x, y))
        self._shape_preview_photo = ImageTk.PhotoImage(background)
        self.shape_preview.configure(image=self._shape_preview_photo)

    def _refresh_color_preview(self) -> None:
        self.color_preview.configure(bg=self._rgb_hex())

    def _refresh_crosshair(self) -> None:
        selected = self.settings.crosshair
        image_path = CROSSHAIRS_DIR / selected if selected else None
        self._apply_transparent_background()

        if self._is_effectively_hidden() or not image_path or not image_path.exists():
            self.crosshair_label.configure(image="")
            self.crosshair_photo = None
            self.crosshair_window.withdraw()
            return

        image = self._load_rendered_crosshair(image_path)

        self.crosshair_photo = ImageTk.PhotoImage(image)
        self.crosshair_label.configure(image=self.crosshair_photo)
        self.crosshair_window.deiconify()
        self._center_crosshair(image.width, image.height)
        self._apply_crosshair_window_styles()

    def _refresh_crosshair_position(self) -> None:
        if self.crosshair_photo is None or self._is_effectively_hidden():
            return
        self._center_crosshair(self.crosshair_photo.width(), self.crosshair_photo.height())

    def _is_effectively_hidden(self) -> bool:
        return bool(self.settings.hidden or self._aim_pressed)

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
            self._colorref(self._transparent_rgb()),
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
    def _colorref(color: tuple[int, int, int]) -> int:
        red, green, blue = color
        return red | (green << 8) | (blue << 16)

    def _load_rendered_crosshair(self, image_path: Path) -> Image.Image:
        image = self._load_shape_image(image_path)
        image = self._resize_to_size(image, self.settings.size)
        image = self._render_crosshair_layers(image)
        if self.settings.rotation % 360:
            image = image.rotate(
                -self.settings.rotation,
                resample=Image.NEAREST,
                expand=True,
            )
        return self._prepare_for_color_key(image)

    def _render_crosshair_layers(self, image: Image.Image) -> Image.Image:
        crosshair = self._colorize_image(image, self._rgb_tuple())
        if not self._outline_enabled():
            return crosshair

        thickness = self.settings.outline_thickness
        size = (image.width + thickness * 2, image.height + thickness * 2)
        alpha = image.getchannel("A").point(
            lambda value: 255 if value > ALPHA_KEY_THRESHOLD else 0
        )
        alpha_padded = Image.new("L", size, 0)
        alpha_padded.paste(alpha, (thickness, thickness))

        dilated = alpha_padded.filter(ImageFilter.MaxFilter(thickness * 2 + 1))
        outline_mask = ImageChops.subtract(dilated, alpha_padded)
        outline_alpha = max(0, min(255, int(self.settings.outline_opacity * 255)))
        outline_mask = outline_mask.point(
            lambda value: outline_alpha if value > ALPHA_KEY_THRESHOLD else 0
        )

        outline = Image.new("RGBA", size, (*self._outline_rgb_tuple(), 255))
        outline.putalpha(outline_mask)
        result = Image.new("RGBA", size, (0, 0, 0, 0))
        result.alpha_composite(outline)
        result.alpha_composite(crosshair, (thickness, thickness))
        return result

    @staticmethod
    def _load_shape_image(image_path: Path) -> Image.Image:
        return Image.open(image_path).convert("RGBA")

    @staticmethod
    def _resize_to_fit(image: Image.Image, maximum: int) -> Image.Image:
        width, height = image.size
        if width <= 0 or height <= 0:
            return image
        scale = min(1.0, maximum / max(width, height))
        new_size = (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        )
        return image.resize(new_size, Image.NEAREST)

    @staticmethod
    def _resize_to_size(image: Image.Image, size: int) -> Image.Image:
        width, height = image.size
        if width <= 0 or height <= 0:
            return image
        scale = size / max(width, height)
        new_size = (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        )
        return image.resize(new_size, Image.NEAREST)

    @staticmethod
    def _colorize_image(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
        alpha = image.getchannel("A")
        mask = alpha.point(lambda value: 255 if value > ALPHA_KEY_THRESHOLD else 0)
        colored = Image.new("RGBA", image.size, (*color, 255))
        colored.putalpha(mask)
        return colored

    def _prepare_for_color_key(self, image: Image.Image) -> Image.Image:
        mask = image.getchannel("A").point(
            lambda alpha: 255 if alpha > ALPHA_KEY_THRESHOLD else 0
        )
        background = Image.new("RGBA", image.size, (*self._transparent_rgb(), 255))
        background.alpha_composite(image)
        keyed = Image.new("RGB", image.size, self._transparent_rgb())
        return Image.composite(background.convert("RGB"), keyed, mask)

    def _center_crosshair(self, width: int, height: int) -> None:
        screen_width = self.crosshair_window.winfo_screenwidth()
        screen_height = self.crosshair_window.winfo_screenheight()
        x = (screen_width - width) // 2 + self.settings.x_offset
        y = (screen_height - height) // 2 + self.settings.y_offset
        self.crosshair_window.geometry(f"{width}x{height}+{x}+{y}")

    def _rgb_tuple(self) -> tuple[int, int, int]:
        return (self.settings.red, self.settings.green, self.settings.blue)

    def _rgb_hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self._rgb_tuple())

    def _outline_rgb_tuple(self) -> tuple[int, int, int]:
        return (
            self.settings.outline_red,
            self.settings.outline_green,
            self.settings.outline_blue,
        )

    def _outline_enabled(self) -> bool:
        return self.settings.outline_thickness > 0 and self.settings.outline_opacity > 0

    def _transparent_rgb(self) -> tuple[int, int, int]:
        visible_colors = {self._rgb_tuple()}
        if self._outline_enabled():
            visible_colors.add(self._outline_rgb_tuple())
        for candidate in TRANSPARENT_COLOR_CANDIDATES:
            if candidate not in visible_colors:
                return candidate
        return (1, 2, 3)

    def _transparent_tk_color(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(*self._transparent_rgb())

    def _apply_transparent_background(self) -> None:
        color = self._transparent_tk_color()
        self.crosshair_window.configure(bg=color)
        self.crosshair_label.configure(bg=color)
        if sys.platform != "win32":
            self.crosshair_window.attributes("-transparentcolor", color)

    def _capture_hotkey(self, event, target: str):
        hotkey = self._event_to_hotkey(event)
        self._set_hotkey(target, hotkey)
        return "break"

    def _capture_mouse_hotkey(self, event, target: str):
        if event.num == 1 and self.settings_window.focus_get() is not event.widget:
            return None
        hotkey = self._mouse_event_to_hotkey(event)
        self._set_hotkey(target, hotkey)
        return "break"

    def _set_hotkey(self, target: str, hotkey: str) -> None:
        if target == "aim":
            self.settings.aim_hotkey = hotkey
            self.aim_hotkey_var.set(hotkey)
        else:
            self.settings.hide_hotkey = hotkey
            self.hide_hotkey_var.set(hotkey)
        self.settings.save_if_changed()

    def _event_to_hotkey(self, event) -> str:
        key = self._normalize_keysym(event.keysym)
        if key in {"Control", "Shift", "Alt"}:
            return key
        return "+".join([*self._modifier_names(key), key])

    def _mouse_event_to_hotkey(self, event) -> str:
        button_names = {
            1: "MouseLeft",
            2: "MouseMiddle",
            3: "MouseRight",
            4: "MouseX1",
            5: "MouseX2",
        }
        key = button_names.get(event.num, f"Mouse{event.num}")
        return "+".join([*self._modifier_names(key), key])

    def _modifier_names(self, key: str) -> list[str]:
        modifiers = []

        if self._modifier_is_pressed("Control") and key != "Control":
            modifiers.append("Ctrl")
        if self._modifier_is_pressed("Shift") and key != "Shift":
            modifiers.append("Shift")
        if self._modifier_is_pressed("Alt") and key != "Alt":
            modifiers.append("Alt")
        return modifiers

    @staticmethod
    def _modifier_is_pressed(key: str) -> bool:
        if sys.platform != "win32":
            return False
        vk = VK_ALIASES[key]
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

    @staticmethod
    def _normalize_keysym(keysym: str) -> str:
        key = keysym.replace("_L", "").replace("_R", "")
        if len(key) == 1:
            return key.upper()
        aliases = {
            "Control": "Control",
            "Shift": "Shift",
            "Alt": "Alt",
            "Return": "Return",
            "Escape": "Escape",
            "space": "Space",
        }
        return aliases.get(key, key)

    def _poll_hotkeys(self) -> None:
        if sys.platform == "win32":
            aim_pressed = self._hotkey_is_pressed(self.settings.aim_hotkey)
            if aim_pressed != self._aim_pressed:
                self._aim_pressed = aim_pressed
                self._refresh_crosshair()

            hide_pressed = self._hotkey_is_pressed(self.settings.hide_hotkey)
            if hide_pressed and not self._hide_pressed:
                self.hidden_var.set(not self.hidden_var.get())
                self._on_hidden_changed()
            self._hide_pressed = hide_pressed

        self._hotkey_after_id = self.root.after(HOTKEY_POLL_MS, self._poll_hotkeys)

    def _hotkey_is_pressed(self, hotkey: str) -> bool:
        virtual_keys = self._hotkey_to_vk_codes(hotkey)
        if not virtual_keys:
            return False
        user32 = ctypes.windll.user32
        return all(user32.GetAsyncKeyState(vk) & 0x8000 for vk in virtual_keys)

    @staticmethod
    def _hotkey_to_vk_codes(hotkey: str) -> list[int]:
        keys = []
        for part in hotkey.split("+"):
            key = part.strip()
            if not key:
                continue
            if key == "Ctrl":
                key = "Control"
            if key in VK_ALIASES:
                keys.append(VK_ALIASES[key])
            elif len(key) == 1:
                keys.append(ord(key.upper()))
        return keys


if __name__ == "__main__":
    SimpleCrossApp().run()
