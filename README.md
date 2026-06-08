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

## Notebooks

- `cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb`
- `cef2026_ferld_cartographic_reports_colab.ipynb`

The main notebook walks through a complete remote-sensing workflow:

- Google Earth Engine authentication from Python/Colab
- FERLD area-of-interest loading
- Sentinel-2 composites for 2017, 2020, and 2023
- Hansen Global Forest Change labels
- Spectral and terrain predictor generation
- Random Forest classification with scikit-learn
- Delta NDVI temporal analysis
- Export of GeoTIFF and GeoJSON outputs to Google Drive
- Colab-based cartographic report generation

## Colab Cartographic Report

The recommended publication workflow is fully Colab-based:

1. Run `cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb`.
2. Confirm `FERLD_RF_forest_loss_no_loss.tif` exists in `My Drive/Workshop/Outputs`.
3. Run `cef2026_ferld_cartographic_reports_colab.ipynb`.

The cartographic notebook generates a PDF and PNG map directly in:

`My Drive/Workshop/Outputs/Reports`

Generated files:

- `CEF2026_carte_FERLD_colab.pdf/png`

This workflow does not require QGIS or local computer paths.

## Data And Outputs

The workflow expects the FERLD area of interest and writes geospatial outputs to Google Drive. Large generated outputs are intentionally not versioned here.

## Contributors

- Joel Masimo Kabuanga
- Naveen Verabhadraswamy
- Osvaldo Valeria
- Alejandro Vega Escobar

## Suggested Citation

If you use or adapt these materials, please cite:

Kabuanga, J. M., Verabhadraswamy, N., Vega Escobar, A., and Valeria, O. 2026. CEF 2026 FERLD Forest Loss Workshop. Workshop materials, CEF 2026 Workshop, Université Laval, Québec City, May 27, 2026.
