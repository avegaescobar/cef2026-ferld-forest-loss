# CEF 2026 FERLD Forest Loss Workshop

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/avegaescobar/cef2026-ferld-forest-loss/blob/main/cef2026_gee_python_colab_workshop_FOREST_LOSS_final.ipynb)

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

## Data And Outputs

The workflow expects the FERLD area of interest and writes geospatial outputs suitable for QGIS. Large generated outputs are intentionally not versioned here.

## Contributors

- Joel Masimo Kabuanga
- Naveen Verabhadraswamy
- Osvaldo Valeria
- Alejandro Vega Escobar

## Citation

If you reuse this material, please cite the CEF 2026 Google Earth Engine workshop and link back to the workshop site and this repository.
