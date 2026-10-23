import os, math
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtGui import QImage, QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush, QPainterPath
from PySide6.QtCore import QRectF, QPointF, Qt
from PIL import Image

S = 1024
img = QImage(S, S, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
p.setRenderHint(QPainter.SmoothPixmapTransform)
c = QPointF(S/2, S/2)

# --- rounded-square background with diagonal blue gradient ---
radius = 224
bg = QPainterPath(); bg.addRoundedRect(QRectF(0,0,S,S), radius, radius)
g = QLinearGradient(0,0,S,S)
g.setColorAt(0.0, QColor("#1e2a78"))
g.setColorAt(0.55, QColor("#2459d8"))
g.setColorAt(1.0, QColor("#3b82f6"))
p.fillPath(bg, QBrush(g))
# top highlight
hl = QRadialGradient(S*0.32, S*0.20, S*0.8)
hl.setColorAt(0.0, QColor(255,255,255,46)); hl.setColorAt(0.5, QColor(255,255,255,0))
p.fillPath(bg, QBrush(hl))
# bottom vignette
vg = QRadialGradient(S*0.5, S*0.95, S*0.9)
vg.setColorAt(0.0, QColor(0,0,20,60)); vg.setColorAt(0.6, QColor(0,0,20,0))
p.fillPath(bg, QBrush(vg))

p.save()
p.translate(c)
p.rotate(-26)   # tilt the whole orbital system

def ring(a, b, width, col, glow=0):
    if glow:
        pen = QPen(QColor(col.red(),col.green(),col.blue(),glow)); pen.setWidthF(width*3.2)
        p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(0,0), a, b)
    pen = QPen(col); pen.setWidthF(width); pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(0,0), a, b)

# faint secondary orbit
ring(300, 322, 10, QColor(255,255,255,55))
# main orbit ring with soft glow
ring(372, 150, 26, QColor(255,255,255,235), glow=40)

# core with shadow + radial gradient
p.setPen(Qt.NoPen)
p.setBrush(QColor(10,20,60,120)); p.drawEllipse(QPointF(0,14), 126, 126)  # shadow
core = QRadialGradient(-30,-30,210)
core.setColorAt(0.0, QColor("#ffffff")); core.setColorAt(0.55, QColor("#eaf2ff")); core.setColorAt(1.0, QColor("#9 cbff".replace(" ","")))
p.setBrush(QBrush(core)); p.drawEllipse(QPointF(0,0), 122, 122)

def node(a, b, theta_deg, r, bright=True):
    th = math.radians(theta_deg)
    x, y = a*math.cos(th), b*math.sin(th)
    glow = QRadialGradient(x, y, r*2.2)
    glow.setColorAt(0.0, QColor(255,255,255,200)); glow.setColorAt(1.0, QColor(255,255,255,0))
    p.setBrush(QBrush(glow)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(x,y), r*2.2, r*2.2)
    ng = QRadialGradient(x-r*0.3, y-r*0.3, r*1.6)
    ng.setColorAt(0.0, QColor("#ffffff")); ng.setColorAt(1.0, QColor("#cfe0ff"))
    p.setBrush(QBrush(ng)); p.drawEllipse(QPointF(x,y), r, r)

# orbiting node (main) + a small moon
node(372, 150, -52, 46)
node(300, 322, 150, 20)
p.restore()
p.end()

# save 512 png + multi-size ico
img.save(str("quickconvert/assets/logo.png"))
img512 = img.scaled(512,512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
img512.save("quickconvert/assets/icon.png")
# ico via PIL from the 512 png
pm = Image.open("quickconvert/assets/icon.png")
pm.save("quickconvert/assets/icon.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("logo + icon.png + icon.ico written")
