import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPolygonF


def make_icon(kind: str, size: int = 18, color: str = "#FFFFFF") -> QPixmap:
    """Renders crisp vector icons using QPainter with zero emoji glyphs."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QColor(color)
    pen = QPen(c, max(1.6, size * 0.1))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(c))

    m = size * 0.18
    w = size - 2 * m
    h = size - 2 * m

    if kind == "play":
        poly = QPolygonF([
            QPointF(m + w * 0.18, m + h * 0.08),
            QPointF(m + w * 0.88, m + h * 0.5),
            QPointF(m + w * 0.18, m + h * 0.92),
        ])
        p.drawPolygon(poly)

    elif kind == "pause":
        bw = w * 0.24
        p.drawRoundedRect(QRectF(m + w * 0.16, m + h * 0.1, bw, h * 0.8), 1.5, 1.5)
        p.drawRoundedRect(QRectF(m + w * 0.60, m + h * 0.1, bw, h * 0.8), 1.5, 1.5)

    elif kind == "next":
        poly = QPolygonF([
            QPointF(m + w * 0.12, m + h * 0.14),
            QPointF(m + w * 0.68, m + h * 0.5),
            QPointF(m + w * 0.12, m + h * 0.86),
        ])
        p.drawPolygon(poly)
        p.drawRoundedRect(QRectF(m + w * 0.74, m + h * 0.14, w * 0.16, h * 0.72), 1.0, 1.0)

    elif kind == "prev":
        p.drawRoundedRect(QRectF(m + w * 0.10, m + h * 0.14, w * 0.16, h * 0.72), 1.0, 1.0)
        poly = QPolygonF([
            QPointF(m + w * 0.88, m + h * 0.14),
            QPointF(m + w * 0.32, m + h * 0.5),
            QPointF(m + w * 0.88, m + h * 0.86),
        ])
        p.drawPolygon(poly)

    elif kind == "heart_filled":
        cx = size / 2.0
        top_y = m + h * 0.22
        r = w * 0.24
        p.drawEllipse(QPointF(cx - r * 0.9, top_y + r * 0.6), r, r)
        p.drawEllipse(QPointF(cx + r * 0.9, top_y + r * 0.6), r, r)
        poly = QPolygonF([
            QPointF(cx - r * 1.82, top_y + r * 0.95),
            QPointF(cx + r * 1.82, top_y + r * 0.95),
            QPointF(cx, m + h * 0.92),
        ])
        p.drawPolygon(poly)

    elif kind == "heart_outline":
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx = size / 2.0
        top_y = m + h * 0.24
        r = w * 0.23
        p.drawArc(QRectF(cx - r * 1.9, top_y, r * 2.0, r * 2.0), 0, 180 * 16)
        p.drawArc(QRectF(cx - r * 0.1, top_y, r * 2.0, r * 2.0), 0, 180 * 16)
        p.drawLine(QPointF(cx - r * 1.9, top_y + r), QPointF(cx, m + h * 0.9))
        p.drawLine(QPointF(cx + r * 1.9, top_y + r), QPointF(cx, m + h * 0.9))

    elif kind == "star_filled" or kind == "star_outline":
        if kind == "star_outline":
            p.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = size / 2.0, size / 2.0
        outer_r = min(w, h) * 0.52
        inner_r = outer_r * 0.44
        pts = []
        for i in range(10):
            ang = -math.pi / 2.0 + i * (math.pi / 5.0)
            rad = outer_r if i % 2 == 0 else inner_r
            pts.append(QPointF(cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        p.drawPolygon(QPolygonF(pts))

    elif kind == "plus":
        cx, cy = size / 2.0, size / 2.0
        p.drawLine(QPointF(cx, m + h * 0.15), QPointF(cx, m + h * 0.85))
        p.drawLine(QPointF(m + w * 0.15, cy), QPointF(m + w * 0.85, cy))

    elif kind == "download":
        cx = size / 2.0
        p.drawLine(QPointF(cx, m + h * 0.12), QPointF(cx, m + h * 0.68))
        p.drawLine(QPointF(cx - w * 0.24, m + h * 0.46), QPointF(cx, m + h * 0.68))
        p.drawLine(QPointF(cx + w * 0.24, m + h * 0.46), QPointF(cx, m + h * 0.68))
        p.drawLine(QPointF(m + w * 0.15, m + h * 0.88), QPointF(m + w * 0.85, m + h * 0.88))

    elif kind == "mini":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(m, m + h * 0.15, w, h * 0.7), 2, 2)
        p.setBrush(QBrush(c))
        p.drawRoundedRect(QRectF(m + w * 0.46, m + h * 0.46, w * 0.42, h * 0.32), 1.5, 1.5)

    elif kind == "expand":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(m, m, w, h), 2, 2)
        p.drawLine(QPointF(m + w * 0.35, m + h * 0.65), QPointF(m + w * 0.72, m + h * 0.28))
        p.drawLine(QPointF(m + w * 0.46, m + h * 0.28), QPointF(m + w * 0.72, m + h * 0.28))
        p.drawLine(QPointF(m + w * 0.72, m + h * 0.28), QPointF(m + w * 0.72, m + h * 0.54))

    elif kind == "volume":
        p.drawPolygon(QPolygonF([
            QPointF(m + w * 0.12, m + h * 0.36),
            QPointF(m + w * 0.38, m + h * 0.36),
            QPointF(m + w * 0.66, m + h * 0.14),
            QPointF(m + w * 0.66, m + h * 0.86),
            QPointF(m + w * 0.38, m + h * 0.64),
            QPointF(m + w * 0.12, m + h * 0.64),
        ]))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(m + w * 0.55, m + h * 0.26, w * 0.36, h * 0.48), -60 * 16, 120 * 16)

    elif kind == "shuffle":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(m + w * 0.1, m + h * 0.28), QPointF(m + w * 0.38, m + h * 0.28))
        p.drawLine(QPointF(m + w * 0.38, m + h * 0.28), QPointF(m + w * 0.68, m + h * 0.72))
        p.drawLine(QPointF(m + w * 0.68, m + h * 0.72), QPointF(m + w * 0.9, m + h * 0.72))
        p.drawLine(QPointF(m + w * 0.1, m + h * 0.72), QPointF(m + w * 0.38, m + h * 0.72))
        p.drawLine(QPointF(m + w * 0.38, m + h * 0.72), QPointF(m + w * 0.68, m + h * 0.28))
        p.drawLine(QPointF(m + w * 0.68, m + h * 0.28), QPointF(m + w * 0.9, m + h * 0.28))

    elif kind == "repeat":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(m + w * 0.12, m + h * 0.24, w * 0.76, h * 0.52), 4, 4)

    elif kind == "search":
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = w * 0.34
        p.drawEllipse(QPointF(m + w * 0.42, m + h * 0.42), r, r)
        p.drawLine(QPointF(m + w * 0.66, m + h * 0.66), QPointF(m + w * 0.9, m + h * 0.9))

    elif kind == "home":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(QPolygonF([
            QPointF(size / 2.0, m + h * 0.12),
            QPointF(m + w * 0.92, m + h * 0.48),
            QPointF(m + w * 0.80, m + h * 0.48),
            QPointF(m + w * 0.80, m + h * 0.90),
            QPointF(m + w * 0.20, m + h * 0.90),
            QPointF(m + w * 0.20, m + h * 0.48),
            QPointF(m + w * 0.08, m + h * 0.48),
        ]))

    elif kind == "disc":
        p.setBrush(QBrush(QColor("#181818")))
        p.drawEllipse(QRectF(m, m, w, h))
        p.setBrush(QBrush(c))
        p.drawEllipse(QPointF(size / 2.0, size / 2.0), w * 0.14, h * 0.14)

    p.end()
    return pix
