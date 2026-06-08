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
import processing
import numpy as np
from osgeo import gdal

OUTPUTS    = Path("/Users/jano/Library/CloudStorage/GoogleDrive-avegae@gmail.com/My Drive/Workshop/Outputs")
LIMITS     = Path("/Users/jano/Library/CloudStorage/GoogleDrive-avegae@gmail.com/My Drive/Workshop/Limits")
FERLD_PATH = LIMITS / "FERLD.geojson"

project = QgsProject.instance()
root    = project.layerTreeRoot()
CRS_UTM = QgsCoordinateReferenceSystem("EPSG:32618")

project.removeAllMapLayers()
project.setCrs(CRS_UTM)
print("✓ Projet nettoyé")

FONT = "Arial"

COLORS = {
    "ink": "#1f2933",
    "muted": "#5b6770",
    "panel": "#ffffff",
    "panel_border": "#d8dee4",
    "forest": "#1b7837",
    "loss": "#d95f02",
    "loss_hot": "#e6007e",
    "gain": "#1a9641",
    "gain_hot": "#00b894",
    "neutral": "#f7f7f7",
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
print("\n=== Fichiers disponibles ===")
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
# 2. RF classification raster
# ============================================================
rf_tif_path = OUTPUTS / "FERLD_RF_forest_loss_no_loss.tif"
if not rf_tif_path.exists():
    raise FileNotFoundError(f"TIF manquant : {rf_tif_path}")

lyr_rf = QgsRasterLayer(str(rf_tif_path), "RF — Classification perte de forêt", "gdal")
if not lyr_rf.isValid():
    raise ValueError(f"Raster invalide : {rf_tif_path.name}")

print(f"✓ RF TIF — CRS: {lyr_rf.crs().authid()} | {rf_tif_path.stat().st_size/1024:.0f} KB")

shader    = QgsRasterShader()
colorRamp = QgsColorRampShader()
colorRamp.setColorRampType(QgsColorRampShader.Type.Exact)
colorRamp.setColorRampItemList([
    QgsColorRampShader.ColorRampItem(0, QColor(COLORS["forest"]), "Pas de perte détectée"),
    QgsColorRampShader.ColorRampItem(1, QColor(COLORS["loss"]), "Perte de forêt Hansen"),
])
shader.setRasterShaderFunction(colorRamp)
renderer = QgsSingleBandPseudoColorRenderer(lyr_rf.dataProvider(), 1, shader)
lyr_rf.setRenderer(renderer)
lyr_rf.setOpacity(0.62)
lyr_rf.triggerRepaint()
project.addMapLayer(lyr_rf, False)
root.insertLayer(0, lyr_rf)
print("✓ Style RF raster appliqué")

# ============================================================
# 3. Points d'échantillonnage
# ============================================================
lyr_samples  = None
samples_path = OUTPUTS / "FERLD_RF_forest_loss_training_samples.gpkg"

if samples_path.exists():
    lyr_samples = QgsVectorLayer(
        f"{samples_path}|layername=rf_samples",
        "Points d'échantillonnage RF", "ogr"
    )
    if lyr_samples.isValid():
        lyr_samples.setRenderer(QgsCategorizedSymbolRenderer("forest_loss", [
            QgsRendererCategory(0, point_symbol(COLORS["sample_0"], 1.1), "Pas de perte (0)"),
            QgsRendererCategory(1, point_symbol(COLORS["sample_1"], 1.25), "Perte Hansen (1)"),
        ]))
        lyr_samples.triggerRepaint()
        project.addMapLayer(lyr_samples, False)
        root.insertLayer(0, lyr_samples)
        print(f"✓ Points d'échantillonnage — {lyr_samples.featureCount()} points")

# ============================================================
# 4. Limites — FERLD (jaune) + ROI élargie 10 km (cyan)
# ============================================================
lyr_ferld   = None
lyr_roi_exp = None

if FERLD_PATH.exists():
    ferld_utm = processing.run("native:reprojectlayer", {
        "INPUT"     : str(FERLD_PATH),
        "TARGET_CRS": "EPSG:32618",
        "OUTPUT"    : "TEMPORARY_OUTPUT",
    })["OUTPUT"]

    ferld_buffer = processing.run("native:buffer", {
        "INPUT"        : ferld_utm,
        "DISTANCE"     : 10000,
        "SEGMENTS"     : 16,
        "END_CAP_STYLE": 0,
        "JOIN_STYLE"   : 0,
        "MITER_LIMIT"  : 2,
        "DISSOLVE"     : True,
        "OUTPUT"       : "TEMPORARY_OUTPUT",
    })["OUTPUT"]

    if not isinstance(ferld_utm, QgsVectorLayer):
        lyr_ferld = QgsVectorLayer(ferld_utm, "Limite FERLD", "ogr")
    else:
        lyr_ferld = ferld_utm
        lyr_ferld.setName("Limite FERLD")

    if lyr_ferld.isValid():
        lyr_ferld.renderer().setSymbol(polygon_outline(COLORS["ferld"], 1.0))
        lyr_ferld.triggerRepaint()
        project.addMapLayer(lyr_ferld, False)
        root.insertLayer(0, lyr_ferld)
        print("✓ Limite FERLD (UTM)")

    if not isinstance(ferld_buffer, QgsVectorLayer):
        lyr_roi_exp = QgsVectorLayer(ferld_buffer, "ROI élargie 10 km", "ogr")
    else:
        lyr_roi_exp = ferld_buffer
        lyr_roi_exp.setName("ROI élargie 10 km")

    if lyr_roi_exp.isValid():
        lyr_roi_exp.renderer().setSymbol(polygon_outline(COLORS["buffer"], 0.85))
        lyr_roi_exp.triggerRepaint()
        project.addMapLayer(lyr_roi_exp, False)
        root.insertLayer(0, lyr_roi_exp)
        print("✓ ROI élargie 10 km (UTM)")
else:
    print(f"⚠ FERLD.geojson introuvable : {FERLD_PATH}")

# ============================================================
# 5. Zoom canvas
# ============================================================
ext_src = lyr_rf.extent()
ext_map = ext_src if lyr_rf.crs() == CRS_UTM else \
          QgsCoordinateTransform(lyr_rf.crs(), CRS_UTM, project).transformBoundingBox(ext_src)
ext_map.grow(ext_map.width() * 0.03)

iface.mapCanvas().setDestinationCrs(CRS_UTM)
iface.mapCanvas().setExtent(ext_map)
iface.mapCanvas().refresh()
print("✓ Canvas centré — EPSG:32618")

# ============================================================
# 6. Layout 1 — RF classification A3 paysage
# ============================================================
LAYOUT_NAME = "CEF 2026 — FERLD Forest Loss"
manager = project.layoutManager()
ex = manager.layoutByName(LAYOUT_NAME)
if ex: manager.removeLayout(ex)

layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(LAYOUT_NAME)
layout.pageCollection().pages()[0].setPageSize(
    QgsLayoutSize(420, 297, QgsUnitTypes.LayoutUnit.Millimeters))

add_panel(layout, (4, 4, 412, 289))
add_panel(layout, (283, 25, 130, 260))

map_item = QgsLayoutItemMap(layout)
layout.addLayoutItem(map_item)
map_item.attemptSetSceneRect(QRectF(10, 25, 265, 260))
map_item.setFrameEnabled(True)
map_item.setFrameStrokeColor(QColor(COLORS["panel_border"]))
map_item.setCrs(CRS_UTM)
map_item.setExtent(ext_map)
map_item.setLayers([l for l in [lyr_ferld, lyr_roi_exp, lyr_samples, lyr_rf, lyr_basemap] if l])
map_item.setKeepLayerSet(True)
map_item.refresh()

add_label(
    layout,
    "Perte de couvert forestier — FERLD\n"
    "Random Forest · Hansen GFC v1.11 · 2001–2023",
    (10, 5, 265, 18),
    size=13,
    bold=True,
)

legend = QgsLayoutItemLegend(layout)
layout.addLayoutItem(legend)
legend.setLinkedMap(map_item)
legend.setTitle("Légende")
legend.setAutoUpdateModel(True)
legend.setStyleFont(QgsLegendStyle.Title, make_font(10, True))
legend.setStyleFont(QgsLegendStyle.Subgroup, make_font(8, True))
legend.setStyleFont(QgsLegendStyle.SymbolLabel, make_font(7))
legend.attemptSetSceneRect(QRectF(289, 31, 118, 95))

add_label(layout, "Méthode et données", (289, 130, 118, 8), size=10, bold=True)
add_label(
    layout,
    "Méthode\n"
    "  · Random Forest — 300 arbres\n"
    "  · 8 prédicteurs spectraux: B2–B12, NDVI, NDMI\n"
    "  · 400 points par classe\n"
    "  · Précision globale: ~74 %\n\n"
    "Données\n"
    "  · Sentinel-2 SR (ESA) 2023\n"
    "  · Hansen GFC v1.11\n"
    "  · ROI: FERLD + 10 km\n\n"
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
print(f"✓ Layout '{LAYOUT_NAME}'")

PDF_OUT = str(OUTPUTS / "CEF2026_carte_FERLD.pdf")
exporter = QgsLayoutExporter(layout)
result   = exporter.exportToPdf(PDF_OUT, QgsLayoutExporter.PdfExportSettings())
print(f"✓ PDF : {PDF_OUT}" if result == QgsLayoutExporter.ExportResult.Success
      else f"⚠ PDF échoué (code {result})")

# ============================================================
# 7. Layout 2 + Layout 3 — Temporel (si fichiers présents)
# ============================================================
temporal_files = {
    "ndvi_2017": OUTPUTS / "FERLD_temporal_NDVI_2017.tif",
    "ndvi_2020": OUTPUTS / "FERLD_temporal_NDVI_2020.tif",
    "ndvi_2023": OUTPUTS / "FERLD_temporal_NDVI_2023.tif",
    "delta"    : OUTPUTS / "FERLD_temporal_delta_NDVI_2017_2023.tif",
    "change"   : OUTPUTS / "FERLD_temporal_change_map_2017_2023.tif",
}

missing_temp = [k for k, v in temporal_files.items() if not v.exists()]
if missing_temp:
    print(f"\n⚠ Layouts temporels ignorés — fichiers manquants : {missing_temp}")
    print("  \u2192 Relancez les cellules 16H/16I dans Colab.")
else:
    print("\n\u2014 Layouts temporels NDVI \u2014")

    def load_ndvi_raster(path, name):
        lyr = QgsRasterLayer(str(path), name, "gdal")
        shader = QgsRasterShader()
        cr = QgsColorRampShader()
        cr.setColorRampType(QgsColorRampShader.Type.Interpolated)
        cr.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(0.0, QColor("#f7f7f7"), "0.0"),
            QgsColorRampShader.ColorRampItem(0.3, QColor("#d9f0a3"), "0.3"),
            QgsColorRampShader.ColorRampItem(0.6, QColor("#78c679"), "0.6"),
            QgsColorRampShader.ColorRampItem(1.0, QColor("#006837"), "1.0"),
        ])
        shader.setRasterShaderFunction(cr)
        r = QgsSingleBandPseudoColorRenderer(lyr.dataProvider(), 1, shader)
        r.setClassificationMin(0.0); r.setClassificationMax(1.0)
        lyr.setRenderer(r)
        project.addMapLayer(lyr, False); root.addLayer(lyr)
        return lyr

    def load_delta_raster(path, name):
        lyr = QgsRasterLayer(str(path), name, "gdal")
        shader = QgsRasterShader()
        cr = QgsColorRampShader()
        cr.setColorRampType(QgsColorRampShader.Type.Interpolated)
        cr.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(-0.4, QColor(COLORS["loss_hot"]), "-0.4"),
            QgsColorRampShader.ColorRampItem( 0.0, QColor(COLORS["neutral"]), "0"),
            QgsColorRampShader.ColorRampItem( 0.4, QColor(COLORS["gain_hot"]), "+0.4"),
        ])
        shader.setRasterShaderFunction(cr)
        r = QgsSingleBandPseudoColorRenderer(lyr.dataProvider(), 1, shader)
        r.setClassificationMin(-0.4); r.setClassificationMax(0.4)
        lyr.setRenderer(r)
        project.addMapLayer(lyr, False); root.addLayer(lyr)
        return lyr

    def load_change_raster(path, name):
        lyr = QgsRasterLayer(str(path), name, "gdal")
        shader = QgsRasterShader()
        cr = QgsColorRampShader()
        cr.setColorRampType(QgsColorRampShader.Type.Exact)
        cr.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(0, QColor(247, 247, 247, 55), "Stable"),
            QgsColorRampShader.ColorRampItem(1, QColor(COLORS["loss_hot"]), "Perte ΔNDVI"),
            QgsColorRampShader.ColorRampItem(2, QColor(COLORS["gain_hot"]), "Gain ΔNDVI"),
        ])
        shader.setRasterShaderFunction(cr)
        r = QgsSingleBandPseudoColorRenderer(lyr.dataProvider(), 1, shader)
        lyr.setRenderer(r)
        lyr.setOpacity(0.88)
        project.addMapLayer(lyr, False); root.addLayer(lyr)
        return lyr

    lyr_n17  = load_ndvi_raster(temporal_files["ndvi_2017"], "NDVI 2017")
    lyr_n20  = load_ndvi_raster(temporal_files["ndvi_2020"], "NDVI 2020")
    lyr_n23  = load_ndvi_raster(temporal_files["ndvi_2023"], "NDVI 2023")
    lyr_delt = load_delta_raster(temporal_files["delta"],    "\u0394NDVI continu 2017\u21922023")
    lyr_change = load_change_raster(temporal_files["change"], "Changement ΔNDVI 2017\u21922023")
    print("✓ 5 rasters temporels chargés")

    ext_t = lyr_n17.extent()
    if lyr_n17.crs() != CRS_UTM:
        ext_t = QgsCoordinateTransform(lyr_n17.crs(), CRS_UTM, project).transformBoundingBox(ext_t)
    ext_t.grow(ext_t.width() * 0.02)

    # ── Statistiques ─────────────────────────────────────────

    def count_pixels_by_class(tif_a_path, tif_b_path, loss_thr=-0.10, gain_thr=0.05):
        da = gdal.Open(str(tif_a_path))
        db = gdal.Open(str(tif_b_path))
        arr_a = da.GetRasterBand(1).ReadAsArray().astype(float)
        arr_b = db.GetRasterBand(1).ReadAsArray().astype(float)
        da = db = None
        r = min(arr_a.shape[0], arr_b.shape[0])
        c = min(arr_a.shape[1], arr_b.shape[1])
        arr_a, arr_b = arr_a[:r, :c], arr_b[:r, :c]
        valid  = (arr_a > -9999) & (arr_b > -9999)
        delta  = arr_b - arr_a
        perte  = int(np.sum((delta <  loss_thr) & valid))
        gain   = int(np.sum((delta >  gain_thr) & valid))
        stable = int(np.sum((delta >= loss_thr) & (delta <= gain_thr) & valid))
        px_ha  = 400 / 10000
        total  = perte + gain + stable
        return {
            "Stable": round(stable * px_ha),
            "Perte" : round(perte  * px_ha),
            "Gain"  : round(gain   * px_ha),
            "Total" : round(total  * px_ha),
            "pPerte": round(perte  / total * 100, 1) if total > 0 else 0.0,
            "pGain" : round(gain   / total * 100, 1) if total > 0 else 0.0,
        }

    tif_17 = temporal_files["ndvi_2017"]
    tif_20 = temporal_files["ndvi_2020"]
    tif_23 = temporal_files["ndvi_2023"]

    stats = {
        "2017\u21922020"       : count_pixels_by_class(tif_17, tif_20),
        "2020\u21922023"       : count_pixels_by_class(tif_20, tif_23),
        "2017\u21922023 cumulé": count_pixels_by_class(tif_17, tif_23),
    }

    print("\n=== Superficie de changement \u0394NDVI (ha) ===")
    print(f"{'Période':<24}{'Stable':>10}{'Perte':>10}{'Gain':>10}{'Total':>10}{'% Perte':>10}{'% Gain':>8}")
    print("-" * 82)
    for p, v in stats.items():
        print(f"{p:<24}{v['Stable']:>10,}{v['Perte']:>10,}{v['Gain']:>10,}{v['Total']:>10,}{v['pPerte']:>10.1f}{v['pGain']:>8.1f}")

    sep  = "\u2500" * 82
    hdr  = f"{'Période':<24}{'Stable (ha)':>12}{'Perte (ha)':>12}{'Gain (ha)':>10}{'Total (ha)':>11}{'% Perte':>9}{'% Gain':>8}"
    ttl  = "Superficie de changement \u0394NDVI  (seuil perte < \u22120.10  \u00b7  gain > +0.05)"
    rows = [
        f"{p:<24}{v['Stable']:>12,}{v['Perte']:>12,}{v['Gain']:>10,}{v['Total']:>11,}{v['pPerte']:>9.1f}{v['pGain']:>8.1f}"
        for p, v in stats.items()
    ]
    table_text = "\n".join([ttl, hdr, sep] + rows)

    # ── Layout 2 — cartes 2×2 A3 paysage ─────────────────────

    LAYOUT2 = "CEF 2026 \u2014 Analyse temporelle NDVI"
    ex2 = manager.layoutByName(LAYOUT2)
    if ex2: manager.removeLayout(ex2)

    lay2 = QgsPrintLayout(project)
    lay2.initializeDefaults()
    lay2.setName(LAYOUT2)
    lay2.pageCollection().pages()[0].setPageSize(
        QgsLayoutSize(420, 297, QgsUnitTypes.LayoutUnit.Millimeters))

    add_panel(lay2, (4, 4, 412, 289))

    M_TOP, M_BOT, M_LEFT, M_RIGHT = 16, 8, 8, 8
    LEG_W, GAP, NOTE_H = 46, 3, 6

    total_w = 420 - M_LEFT - M_RIGHT - LEG_W - GAP
    total_h = 297 - M_TOP - M_BOT - NOTE_H - GAP
    panel_w = (total_w - GAP) / 2
    panel_h = (total_h - GAP) / 2

    map_items2 = []
    for lyr_panel, label, col, row in [
        (lyr_n17,  "NDVI 2017",            0, 0),
        (lyr_n20,  "NDVI 2020",            1, 0),
        (lyr_n23,  "NDVI 2023",            0, 1),
        (lyr_change, "Changement 2017\u21922023", 1, 1),
    ]:
        x = M_LEFT + col * (panel_w + GAP)
        y = M_TOP  + row * (panel_h + GAP)
        mi = QgsLayoutItemMap(lay2)
        lay2.addLayoutItem(mi)
        mi.attemptSetSceneRect(QRectF(x, y, panel_w, panel_h))
        mi.setFrameEnabled(True)
        mi.setFrameStrokeColor(QColor(COLORS["panel_border"]))
        mi.setCrs(CRS_UTM)
        mi.setExtent(ext_t)
        mi.setLayers([l for l in [lyr_ferld, lyr_roi_exp, lyr_panel, lyr_basemap] if l])
        mi.setKeepLayerSet(True)
        mi.refresh()
        map_items2.append(mi)

        add_panel(lay2, (x + 1, y + 1, panel_w - 2, 8), fill="panel", stroke="panel_border")
        add_label(lay2, f" {label}", (x + 2, y + 2, panel_w - 4, 6), size=8, bold=True)

    add_label(
        lay2,
        "Évolution temporelle du NDVI — FERLD · 2017 / 2020 / 2023",
        (M_LEFT, 5, total_w + LEG_W + GAP, 10),
        size=11,
        bold=True,
    )

    legend2 = QgsLayoutItemLegend(lay2)
    lay2.addLayoutItem(legend2)
    legend2.setLinkedMap(map_items2[-1])
    legend2.setTitle("Légende")
    legend2.setAutoUpdateModel(True)
    legend2.setStyleFont(QgsLegendStyle.Title, make_font(9, True))
    legend2.setStyleFont(QgsLegendStyle.Subgroup, make_font(7, True))
    legend2.setStyleFont(QgsLegendStyle.SymbolLabel, make_font(6))
    legend2.attemptSetSceneRect(QRectF(M_LEFT + total_w + GAP, M_TOP, LEG_W - 2, total_h))

    scale2 = QgsLayoutItemScaleBar(lay2)
    lay2.addLayoutItem(scale2)
    scale2.setLinkedMap(map_items2[0])
    scale2.setStyle("Single Box")
    scale2.setUnits(QgsUnitTypes.DistanceKilometers)
    scale2.setUnitLabel("km")
    scale2.setNumberOfSegments(2)
    scale2.setNumberOfSegmentsLeft(0)
    scale2.setUnitsPerSegment(2)
    scale2.setFont(make_font(5))
    scale2.attemptSetSceneRect(QRectF(M_LEFT + 7, 297 - M_BOT - NOTE_H - 8, 42, 6))

    add_label(
        lay2,
        "Données: Sentinel-2 SR (ESA) · Composite médian juin–sept · "
        "Changement classé: perte ΔNDVI < −0.10 · gain > +0.05 · "
        "CRS: EPSG:32618 · CEF Workshop 2026 — GEE + Python",
        (M_LEFT, 297 - M_BOT - NOTE_H, total_w + LEG_W + GAP, NOTE_H),
        size=6,
        color="muted",
    )

    manager.addLayout(lay2)
    print(f"✓ Layout '{LAYOUT2}'")

    PDF2 = str(OUTPUTS / "CEF2026_carte_temporelle_NDVI.pdf")
    exp2 = QgsLayoutExporter(lay2)
    res2 = exp2.exportToPdf(PDF2, QgsLayoutExporter.PdfExportSettings())
    print(f"✓ PDF : {PDF2}" if res2 == QgsLayoutExporter.ExportResult.Success
          else f"⚠ PDF échoué (code {res2})")

    # ── Layout 3 — Tableau statistique A4 paysage ────────────

    LAYOUT3 = "CEF 2026 \u2014 Tableau statistique \u0394NDVI"
    ex3 = manager.layoutByName(LAYOUT3)
    if ex3: manager.removeLayout(ex3)

    lay3 = QgsPrintLayout(project)
    lay3.initializeDefaults()
    lay3.setName(LAYOUT3)
    lay3.pageCollection().pages()[0].setPageSize(
        QgsLayoutSize(297, 210, QgsUnitTypes.LayoutUnit.Millimeters))

    add_panel(lay3, (6, 6, 285, 198))
    add_panel(lay3, (15, 52, 267, 52))
    add_panel(lay3, (15, 110, 267, 64))

    add_label(
        lay3,
        "Analyse quantitative des changements de couvert végétal\n"
        "FERLD + zone tampon 10 km · Sentinel-2 SR · 2017 / 2020 / 2023",
        (15, 12, 267, 22),
        size=14,
        bold=True,
    )

    add_label(
        lay3,
        "Méthode: ΔNDVI médian estival (composite juin–septembre) · "
        "seuil perte < −0.10 · seuil gain > +0.05 · "
        "résolution 20 m · CRS EPSG:32618 (UTM 18N)",
        (15, 36, 267, 10),
        size=8,
        color="muted",
    )

    tbl3 = QgsLayoutItemLabel(lay3)
    lay3.addLayoutItem(tbl3)
    tbl3.setText(table_text)
    tbl3.setFont(QFont("Menlo", 8))
    tbl3.setFontColor(QColor(COLORS["ink"]))
    tbl3.attemptSetSceneRect(QRectF(20, 58, 257, 40))

    add_label(
        lay3,
        "Interprétation\n\n"
        "· Stable         Pixels où le ΔNDVI reste entre −0.10 et +0.05 — "
        "pas de changement spectral significatif.\n"
        "· Perte (magenta)  Pixels où le ΔNDVI chute sous −0.10 — perte de vigueur végétale "
        "(coupe, feu, chablis, défoliation sévère).\n"
        "· Gain (vert vif) Pixels où le ΔNDVI dépasse +0.05 — regain de vigueur "
        "(régénération, fermeture de couvert).\n\n"
        "Note: le ΔNDVI détecte les changements spectraux sans distinguer la cause. "
        "Pour une interprétation causale, croiser avec Hansen Global Forest Change (lossyear).",
        (20, 116, 257, 52),
        size=8,
        color="ink",
    )

    add_label(
        lay3,
        "Données: Sentinel-2 SR harmonisé (ESA / Copernicus) · "
        "Hansen Global Forest Change v1.11 (UMD) · "
        "Traitement: Google Earth Engine + Python · CEF Workshop 2026",
        (15, 190, 267, 8),
        size=7,
        color="muted",
    )

    manager.addLayout(lay3)
    print(f"✓ Layout '{LAYOUT3}'")

    PDF3 = str(OUTPUTS / "CEF2026_tableau_statistique_NDVI.pdf")
    exp3 = QgsLayoutExporter(lay3)
    res3 = exp3.exportToPdf(PDF3, QgsLayoutExporter.PdfExportSettings())
    print(f"✓ PDF : {PDF3}" if res3 == QgsLayoutExporter.ExportResult.Success
          else f"⚠ PDF échoué (code {res3})")

print("\n✓ Script terminé.")
