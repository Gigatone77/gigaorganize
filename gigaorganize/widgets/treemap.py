import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
from dataclasses import dataclass

from gigaorganize.utils.format import format_size, truncate


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


def _squarify(items, x, y, w, h, palette):
    rects = []
    remaining = sorted(items, key=lambda t: t[0], reverse=True)
    cx, cy, cw, ch = x, y, w, h
    for i, (area, label, sublabel) in enumerate(remaining):
        if cw <= 0 or ch <= 0:
            break
        if cw >= ch:
            row_h = area / cw if cw else 0
            rects.append((Rect(cx, cy, cw, row_h), label, sublabel, palette[i % len(palette)]))
            cy += row_h
            ch -= row_h
        else:
            col_w = area / ch if ch else 0
            rects.append((Rect(cx, cy, col_w, ch), label, sublabel, palette[i % len(palette)]))
            cx += col_w
            cw -= col_w
    return rects


PALETTE = [
    "#2E86AB", "#A23B72", "#F18F01", "#C73E1D",
    "#44BBA4", "#E94F37", "#393E41", "#8E9AAF",
    "#CBC0D3", "#EFD3D7", "#6B4226", "#D4A373",
]


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


class TreemapWidget(Gtk.DrawingArea):
    __gtype_name__ = "TreemapWidget"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self._entries = []
        self._hovered = -1
        self._on_activated_callback = None
        self.set_draw_func(self._draw)

        click = Gtk.GestureClick()
        click.connect("released", self._on_click)
        self.add_controller(click)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self.add_controller(motion)

    def set_activated_callback(self, callback):
        self._on_activated_callback = callback

    def set_data(self, entries):
        self._entries = list(entries)
        self.queue_draw()

    def _layout(self, w, h):
        items = []
        total = sum(e.size for e in self._entries if e.size > 0)
        if total == 0:
            return []
        for e in self._entries[:40]:
            if e.size > 0:
                area = (e.size / total) * w * h
                items.append((area, e.path.name, format_size(e.size)))
        return _squarify(items, 0, 0, w, h, PALETTE)

    def _draw(self, area, cr, w, h):
        cr.set_source_rgb(0.12, 0.12, 0.12)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        rectangles = self._layout(w, h)

        for rect, label, sublabel, color in rectangles:
            r, g, b = _hex_to_rgb(color)
            cr.set_source_rgb(r, g, b)
            cr.rectangle(rect.x + 1, rect.y + 1, rect.w - 2, rect.h - 2)
            cr.fill()

            if rect.w > 50 and rect.h > 25:
                cr.set_source_rgb(1, 1, 1)
                cr.select_font_face("sans-serif", 0, 1)
                font_size = max(9, min(13, rect.w / 8))
                cr.set_font_size(font_size)
                cr.move_to(rect.x + 4, rect.y + font_size + 2)
                cr.show_text(truncate(label, int(rect.w / font_size)))

                if rect.h > 40:
                    cr.set_font_size(max(8, font_size - 2))
                    cr.move_to(rect.x + 4, rect.y + font_size * 2 + 2)
                    cr.show_text(sublabel)

    def _on_click(self, gesture, n_press, x, y):
        for rect, label, _, _ in self._layout(self.get_width(), self.get_height()):
            if rect.contains(x, y):
                if self._on_activated_callback:
                    self._on_activated_callback(label)
                break

    def _on_motion(self, controller, x, y):
        for i, (rect, label, sublabel, _) in enumerate(
            self._layout(self.get_width(), self.get_height())
        ):
            if rect.contains(x, y):
                if i != self._hovered:
                    self._hovered = i
                    self.set_tooltip_text(f"{label}: {sublabel}")
                return
        self._hovered = -1
        self.set_tooltip_text(None)
