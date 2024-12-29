# scog-compute

## Purpose

The goal of this project is to efficiently do raster computation  on different zoom levels, similar to Google Earth Engine, but using Cloud Optimized GeoTIFFs (COGs) for Sentinel-2 imagery. When you zoom in and out on Google Earth Engine, it efficiently processes large images on the fly. We aim to replicate this capability in an open-source and scalable manner using COGs. This experiment demonstrates that on-the-fly computation at various zoom levels can be achieved with minimal and scalable hardware. Additionally, by leveraging a data cube, this approach can be expanded to include temporal dimensions.

![image](https://github.com/user-attachments/assets/e5741f6b-d6c2-4e47-a794-21c2244a7476)


Learn about COG and how to generate one for this project [Here](./cog.md)

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- [poetry](https://python-poetry.org/) 

### Install PDM

If you don't have poetry installed, you can install it using the following command:

```bash
pip install poetry
```


#### Install 
```bash
poetry install
```

#### Activate virtualenv 
```bash
poetry shell
```

#### Run 

```bash
poetry run uvicorn main:app --reload
```


## Resources and Credits 

- https://registry.opendata.aws/sentinel-2-l2a-cogs/ COGS Stac API for sentinel-2