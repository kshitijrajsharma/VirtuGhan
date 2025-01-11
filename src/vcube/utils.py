import os
import zipfile
from datetime import datetime, timedelta

import httpx
import numpy as np
import requests
from shapely.geometry import box, shape


def search_stac_api(bbox, start_date, end_date, cloud_cover, stac_api_url):
    search_params = {
        "collections": ["sentinel-2-l2a"],
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": cloud_cover}},
        "bbox": bbox,
        "limit": 100,
    }

    all_features = []
    next_link = None

    while True:
        response = requests.post(
            stac_api_url,
            json=search_params if not next_link else next_link["body"],
        )
        response.raise_for_status()
        response_json = response.json()

        all_features.extend(response_json["features"])

        next_link = next(
            (link for link in response_json["links"] if link["rel"] == "next"), None
        )
        if not next_link:
            break
    return all_features


async def search_stac_api_async(
    bbox_geojson, start_date, end_date, cloud_cover, stac_api_url
):
    search_params = {
        "collections": ["sentinel-2-l2a"],
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": cloud_cover}},
        "intersects": bbox_geojson,
        "limit": 100,
    }

    all_features = []
    next_link = None

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.post(
                stac_api_url,
                json=search_params if not next_link else next_link["body"],
            )
            response.raise_for_status()
            response_json = response.json()

            all_features.extend(response_json["features"])

            next_link = next(
                (link for link in response_json["links"] if link["rel"] == "next"), None
            )
            if not next_link:
                break

    return all_features


def zip_files(file_list, zip_path):
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in file_list:
            zipf.write(file, os.path.basename(file))
    print(f"Saved intermediate images ZIP to {zip_path}")
    for file in file_list:
        os.remove(file)


def filter_latest_image_per_grid(features):
    grid_latest = {}
    for feature in features:
        grid = feature["id"].split("_")[1]
        date = feature["properties"]["datetime"]
        if (
            grid not in grid_latest
            or date > grid_latest[grid]["properties"]["datetime"]
        ):
            grid_latest[grid] = feature
    return list(grid_latest.values())


def filter_intersected_features(features, bbox):
    bbox_polygon = box(bbox[0], bbox[1], bbox[2], bbox[3])
    return [
        feature
        for feature in features
        if shape(feature["geometry"]).contains(bbox_polygon)
    ]


def remove_overlapping_sentinel2_tiles(features):
    if not features:
        return []

    zone_counts = {}
    for feature in features:
        zone = feature["id"].split("_")[1][:2]
        zone_counts[zone] = zone_counts.get(zone, 0) + 1

    if not zone_counts:
        return []

    max_zone = max(zone_counts, key=zone_counts.get)

    filtered_features = {}
    for feature in features:
        parts = feature["id"].split("_")
        date = parts[2]
        zone = parts[1][:2]

        if zone == max_zone and date not in filtered_features:
            filtered_features[date] = feature

    return list(filtered_features.values())


def aggregate_time_series(data, operation):
    result_stack = np.ma.stack(data)

    operations = {
        "mean": np.ma.mean,
        "median": np.ma.median,
        "max": np.ma.max,
        "min": np.ma.min,
        "std": np.ma.std,
        "sum": np.ma.sum,
        "var": np.ma.var,
    }

    return operations[operation](result_stack, axis=0)


def smart_filter_images(features, start_date: str, end_date: str):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    total_days = (end - start).days

    if total_days <= 60:
        # For a time range of up to 2 months, select 1 image per week
        frequency = timedelta(weeks=1)
    elif total_days <= 365:
        # For a time range of up to 1 year, select 1 image per month
        frequency = timedelta(days=30)
    elif total_days <= 3 * 365:
        # For a time range of up to 3 years, select 1 image per 3 months
        frequency = timedelta(days=90)
    else:
        # rest, select 1 image per 6 months
        frequency = timedelta(days=180)

    filtered_features = []
    last_selected_date = None

    for feature in sorted(features, key=lambda x: x["properties"]["datetime"]):
        date = datetime.fromisoformat(feature["properties"]["datetime"].split("T")[0])
        if last_selected_date is None or date >= last_selected_date + frequency:
            filtered_features.append(feature)
            last_selected_date = date

    return filtered_features
