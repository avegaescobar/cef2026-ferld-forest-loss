# CEF 2026 FERLD Forest Loss Workshop

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/avegaescobar/cef2026-ferld-forest-loss/blob/main/cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb)

[![Open cartographic reports in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/avegaescobar/cef2026-ferld-forest-loss/blob/main/cef2026_ferld_cartographic_reports_colab.ipynb)

Google Earth Engine + Python/Colab workshop material for detecting forest cover loss over the Foret d'enseignement et de recherche du lac Duparquet (FERLD), Abitibi-Temiscamingue, Quebec.

This repository contains the FERLD forest-loss pipeline developed for the CEF 2026 Google Earth Engine workshop.

## Workshop Context

The broader CEF 2026 workshop has two parts:

- Introduction to Google Earth Engine, presented by Joel Masimo Kabuanga, Naveen Verabhadraswamy, and Osvaldo Valeria.
- Forest-loss detection over FERLD, developed by Alejandro Vega Escobar.

The introductory workshop site is available at:
https://forestcguy.github.io/cef2026-gee-workshop/

## Notebook

- `cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb`
- `cef2026_ferld_cartographic_reports_colab.ipynb`
- `Import_GEE.py`
- `NDVI.py`

The notebook walks through a complete remote-sensing workflow:

- Google Earth Engine authentication from Python/Colab
- FERLD area-of-interest loading
- Sentinel-2 composites for 2017, 2020, and 2023
- Hansen Global Forest Change labels
- Spectral and terrain predictor generation
- Random Forest classification with scikit-learn
- Delta NDVI temporal analysis
- Export of GeoTIFF and GeoJSON outputs for QGIS
- Automatic cartographic layout generation with Python and QGIS

## Colab Cartographic Reports

The recommended publication workflow is fully Colab-based:

1. Run `cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb`.
2. Confirm the expected GeoTIFF/GeoJSON outputs exist in `My Drive/Workshop/Outputs`.
3. Run `cef2026_ferld_cartographic_reports_colab.ipynb`.

The cartographic notebook generates PDF and PNG reports directly in:

`My Drive/Workshop/Outputs/Reports`

Generated reports:

- `CEF2026_carte_FERLD_colab.pdf/png`
- `CEF2026_carte_temporelle_NDVI_colab.pdf/png`
- `CEF2026_tableau_statistique_NDVI_colab.pdf/png`

This workflow does not require QGIS or local computer paths.

## Optional QGIS Scripts

The QGIS scripts are optional local helpers for users who want to build layouts inside QGIS after the Colab notebook has exported the expected files to `My Drive/Workshop/Outputs`.

- `Import_GEE.py` loads the forest-loss classification outputs and exports the main FERLD map PDF.
- `NDVI.py` loads the classification and temporal NDVI outputs, then exports the forest-loss map, temporal NDVI map, and NDVI statistics PDF.

## Data And Outputs

The workflow expects the FERLD area of interest and writes geospatial outputs suitable for QGIS. Large generated outputs are intentionally not versioned here.

## Contributors

- Joel Masimo Kabuanga
- Naveen Verabhadraswamy
- Osvaldo Valeria
- Alejandro Vega Escobar

## Citation

If you reuse this material, please cite the CEF 2026 Google Earth Engine workshop and link back to the workshop site and this repository.
