# ============================================================
# QGIS 4 — CEF 2026 — FERLD Forest Loss
# Extensions > Console Python > Éditeur > Exécuter
# ============================================================

from pathlib import Path
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLegend,
    QgsLayoutItemLabel, QgsLayoutItemScaleBar, QgsLayoutItemShape,
    QgsLayoutSize, QgsUnitTypes,
    QgsLayoutExporter, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsSymbol, QgsWkbTypes,
    QgsLegendStyle,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRasterShader, QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
)
from qgis.PyQt.QtGui import QColor, QFont, QPen
from qgis.PyQt.QtCore import QRectF, Qt

OUTPUTS = Path("/Users/jano/Library/CloudStorage/GoogleDrive-avegae@gmail.com/My Drive/Workshop/Outputs")
LIMITS_DIR = OUTPUTS.parent / "Limits"
FERLD_PATH = LIMITS_DIR / "FERLD.geojson"

project = QgsProject.instance()
root    = project.layerTreeRoot()
CRS_UTM = QgsCoordinateReferenceSystem("EPSG:32618")

project.removeAllMapLayers()
project.setCrs(CRS_UTM)

FONT = "Arial"

COLORS = {
    "ink": "#1f2933",
    "muted": "#5b6770",
    "panel": "#ffffff",
    "panel_border": "#d8dee4",
    "forest": "#1b7837",
    "stable": "#f7f7f7",
    "loss": "#e6007e",
    "ferld": "#ffd43b",
    "buffer": "#42c5f5",
    "sample_0": "#111827",
    "sample_1": "#e11d48",
}


def make_font(size, bold=False):
    font = QFont(FONT, size)
    font.setBold(bold)
    return font


def add_label(layout, text, rect, size=8, bold=False, color="ink"):
    label = QgsLayoutItemLabel(layout)
    layout.addLayoutItem(label)
    label.setText(text)
    label.setFont(make_font(size, bold))
    label.setFontColor(QColor(COLORS[color]))
    label.attemptSetSceneRect(QRectF(*rect))
    return label


def add_panel(layout, rect, fill="panel", stroke="panel_border"):
    panel = QgsLayoutItemShape(layout)
    layout.addLayoutItem(panel)
    try:
        panel.setShapeType(QgsLayoutItemShape.Shape.Rectangle)
    except AttributeError:
        panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.setBrush(QColor(COLORS[fill]))
    panel.setPen(QPen(QColor(COLORS[stroke])))
    panel.attemptSetSceneRect(QRectF(*rect))
    return panel


def polygon_outline(color, width=0.75):
    sym = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
    layer = sym.symbolLayer(0)
    layer.setFillColor(QColor(0, 0, 0, 0))
    layer.setStrokeColor(QColor(color))
    layer.setStrokeWidth(width)
    return sym


def point_symbol(color, size=1.25):
    sym = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
    sym.setColor(QColor(color))
    sym.setSize(size)
    sym.symbolLayer(0).setStrokeStyle(Qt.PenStyle.NoPen)
    return sym

# ============================================================
# Diagnostic
# ============================================================
print("=== Fichiers disponibles ===")
for p in sorted(OUTPUTS.rglob("*")):
    if p.is_file() and not p.name.startswith("."):
        print(f"  {p.stat().st_size/1024:>8.1f} KB  {p.name}")
print()

# ============================================================
# 1. ESRI Satellite basemap
# ============================================================

esri_url = (
    "type=xyz"
    "&url=https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    "&zmax=19&zmin=0"
)
lyr_basemap = QgsRasterLayer(esri_url, "ESRI Satellite", "wms")
if lyr_basemap.isValid():
    project.addMapLayer(lyr_basemap, False)
    root.addLayer(lyr_basemap)
    print("✓ ESRI Satellite")
else:
    print("⚠ ESRI Satellite invalide")
    lyr_basemap = None

# ============================================================
# 2. RF classification raster — couverture complète du territoire
#    0 = pas de perte (vert), 1 = perte (orange)
#    C'est le produit correct pour couvrir tout le territoire
# ============================================================

rf_tif_path = OUTPUTS / "FERLD_RF_forest_loss_no_loss.tif"
if not rf_tif_path.exists():
    raise FileNotFoundError(f"TIF manquant : {rf_tif_path}\nRelancez le notebook v8 complet.")

lyr_rf = QgsRasterLayer(str(rf_tif_path), "RF — Classification perte de forêt", "gdal")
if not lyr_rf.isValid():
    raise ValueError(f"Raster invalide : {rf_tif_path.name}")

print(f"✓ RF TIF — CRS: {lyr_rf.crs().authid()}")
print(f"  Étendue : {lyr_rf.extent()}")
print(f"  Taille  : {rf_tif_path.stat().st_size/1024:.0f} KB")

# Style raster exact — stable is almost transparent; predicted loss is high contrast.
shader    = QgsRasterShader()
colorRamp = QgsColorRampShader()
colorRamp.setColorRampType(QgsColorRampShader.Type.Exact)
colorRamp.setColorRampItemList([
    QgsColorRampShader.ColorRampItem(0, QColor(247, 247, 247, 35), "Pas de perte prédite"),
    QgsColorRampShader.ColorRampItem(1, QColor(COLORS["loss"]), "Perte de forêt prédite RF"),
])
shader.setRasterShaderFunction(colorRamp)
renderer = QgsSingleBandPseudoColorRenderer(lyr_rf.dataProvider(), 1, shader)
lyr_rf.setRenderer(renderer)
lyr_rf.setOpacity(0.92)
lyr_rf.triggerRepaint()

project.addMapLayer(lyr_rf, False)
root.insertLayer(0, lyr_rf)
print("✓ Style RF raster appliqué")

# ============================================================
# 3. Points d'échantillonnage — par-dessus le raster
# ============================================================

samples_path = OUTPUTS / "FERLD_RF_forest_loss_training_samples.gpkg"
lyr_samples  = None

if samples_path.exists():
    lyr_samples = QgsVectorLayer(
        f"{samples_path}|layername=rf_samples",
        "Points d'échantillonnage RF", "ogr"
    )
    if lyr_samples.isValid():
        cats_pts = [
            QgsRendererCategory(0, point_symbol(COLORS["sample_0"], 1.1), "Pas de perte (0)"),
            QgsRendererCategory(1, point_symbol(COLORS["sample_1"], 1.25), "Perte Hansen (1)"),
        ]
        lyr_samples.setRenderer(QgsCategorizedSymbolRenderer("forest_loss", cats_pts))
        lyr_samples.triggerRepaint()
        project.addMapLayer(lyr_samples, False)
        root.insertLayer(0, lyr_samples)
        print(f"✓ Points d'échantillonnage — {lyr_samples.featureCount()} points")
    else:
        print("⚠ Points d'échantillonnage invalides")
        lyr_samples = None

# ============================================================
# 4. Limites — FERLD (jaune) + ROI élargie (cyan)
# ============================================================

lyr_ferld    = None
lyr_roi_exp  = None

if FERLD_PATH.exists():
    # --- Limite FERLD — contour jaune, corps vide
    lyr_ferld = QgsVectorLayer(str(FERLD_PATH), "Limite FERLD", "ogr")
    if lyr_ferld.isValid():
        lyr_ferld.renderer().setSymbol(polygon_outline(COLORS["ferld"], 1.0))
        lyr_ferld.triggerRepaint()
        project.addMapLayer(lyr_ferld, False)
        root.insertLayer(0, lyr_ferld)
        print("✓ Limite FERLD")

    # --- ROI élargie 10 km — buffer sur la géométrie FERLD, contour cyan
    import processing
    result = processing.run("native:buffer", {
        "INPUT"        : str(FERLD_PATH),
        "DISTANCE"     : 10000,          # 10 km en mètres (CRS doit être métrique)
        "SEGMENTS"     : 5,
        "END_CAP_STYLE": 0,
        "JOIN_STYLE"   : 0,
        "MITER_LIMIT"  : 2,
        "DISSOLVE"     : True,
        "OUTPUT"       : "TEMPORARY_OUTPUT",
    })
    lyr_roi_exp = result["OUTPUT"]
    if isinstance(lyr_roi_exp, str):
        lyr_roi_exp = QgsVectorLayer(lyr_roi_exp, "ROI élargie 10 km", "ogr")
    else:
        lyr_roi_exp.setName("ROI élargie 10 km")

    if lyr_roi_exp.isValid():
        lyr_roi_exp.renderer().setSymbol(polygon_outline(COLORS["buffer"], 0.85))
        lyr_roi_exp.triggerRepaint()
        project.addMapLayer(lyr_roi_exp, False)
        root.insertLayer(0, lyr_roi_exp)
        print("✓ ROI élargie 10 km")
else:
    print(f"⚠ FERLD.geojson introuvable : {FERLD_PATH}")

# ============================================================
# 5. Zoom canvas sur le raster RF
# ============================================================

ext_src = lyr_rf.extent()
src_crs = lyr_rf.crs()

if src_crs != CRS_UTM:
    xform   = QgsCoordinateTransform(src_crs, CRS_UTM, project)
    ext_map = xform.transformBoundingBox(ext_src)
else:
    ext_map = ext_src

ext_map.grow(ext_map.width() * 0.03)

iface.mapCanvas().setDestinationCrs(CRS_UTM)
iface.mapCanvas().setExtent(ext_map)
iface.mapCanvas().refresh()
print(f"✓ Canvas centré — EPSG:32618")

# ============================================================
# 6. Layout A3 paysage
# ============================================================

LAYOUT_NAME = "CEF 2026 — FERLD Forest Loss"
manager  = project.layoutManager()
existing = manager.layoutByName(LAYOUT_NAME)
if existing:
    manager.removeLayout(existing)

layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(LAYOUT_NAME)

page = layout.pageCollection().pages()[0]
page.setPageSize(QgsLayoutSize(420, 297, QgsUnitTypes.LayoutUnit.Millimeters))

add_panel(layout, (4, 4, 412, 289))
add_panel(layout, (283, 25, 130, 260))

# Carte
map_item = QgsLayoutItemMap(layout)
layout.addLayoutItem(map_item)
map_item.attemptSetSceneRect(QRectF(10, 25, 265, 260))
map_item.setFrameEnabled(True)
map_item.setFrameStrokeColor(QColor(COLORS["panel_border"]))
map_item.setCrs(CRS_UTM)
map_item.setExtent(ext_map)

# Main PDF intentionally excludes training points: they add red noise at this scale.
map_layers = [l for l in [lyr_ferld, lyr_roi_exp, lyr_rf, lyr_basemap] if l is not None]
map_item.setLayers(map_layers)
map_item.setKeepLayerSet(True)
map_item.refresh()

add_label(
    layout,
    "Perte de couvert forestier — FERLD\nRandom Forest · Hansen GFC v1.11 · 2001–2023",
    (10, 5, 265, 18),
    size=13,
    bold=True,
)

# Légende
legend = QgsLayoutItemLegend(layout)
layout.addLayoutItem(legend)
legend.setLinkedMap(map_item)
legend.setTitle("Légende")
legend.setAutoUpdateModel(True)
legend.setStyleFont(QgsLegendStyle.Title, make_font(10, True))
legend.setStyleFont(QgsLegendStyle.Subgroup, make_font(8, True))
legend.setStyleFont(QgsLegendStyle.SymbolLabel, make_font(7))
legend.attemptSetSceneRect(QRectF(289, 31, 118, 95))

# Note méthodologique
add_label(layout, "Méthode et données", (289, 130, 118, 8), size=10, bold=True)
note = add_label(
    layout,
    "Méthode\n"
    "  · Random Forest — 300 arbres\n"
    "  · 8 prédicteurs spectraux: B2–B12, NDVI, NDMI\n"
    "  · 400 points par classe\n"
    "  · Précision globale: ~74 %\n\n"
    "Données\n"
    "  · Sentinel-2 SR (ESA) 2023\n"
    "  · Hansen GFC v1.11\n"
    "  · ROI : FERLD + 10 km\n\n"
    "CRS : EPSG:32618 (UTM 18N)\n"
    "CEF Workshop 2026 — GEE + Python",
    (289, 142, 118, 95),
    size=7,
    color="muted",
)

scale = QgsLayoutItemScaleBar(layout)
layout.addLayoutItem(scale)
scale.setLinkedMap(map_item)
scale.setStyle("Single Box")
scale.setUnits(QgsUnitTypes.DistanceKilometers)
scale.setUnitLabel("km")
scale.setNumberOfSegments(2)
scale.setNumberOfSegmentsLeft(0)
scale.setUnitsPerSegment(2)
scale.setFont(make_font(6))
scale.attemptSetSceneRect(QRectF(18, 274, 45, 7))

add_label(
    layout,
    "Centre d'étude de la forêt · CEF 2026 · Google Earth Engine + Python",
    (289, 271, 118, 7),
    size=6,
    color="muted",
)

manager.addLayout(layout)
print(f"✓ Layout '{LAYOUT_NAME}' → Projet > Mises en page")

# ============================================================
# 7. Export PDF
# ============================================================

PDF_OUT = str(OUTPUTS / "CEF2026_carte_FERLD.pdf")
exporter = QgsLayoutExporter(layout)
result   = exporter.exportToPdf(PDF_OUT, QgsLayoutExporter.PdfExportSettings())

if result == QgsLayoutExporter.ExportResult.Success:
    print(f"✓ PDF : {PDF_OUT}")
else:
    print(f"⚠ PDF échoué (code {result})")

print("\n✓ Script terminé.")
