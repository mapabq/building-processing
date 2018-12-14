from io import BytesIO
import simplejson as json
from pathlib import Path
from typing import Generator, List, Tuple, Type
from urllib.request import urlopen

import ijson.backends.yajl2_cffi as ijson

from rtree import index
from shapely.geometry import shape
from shapely.errors import TopologicalError


def geojson_gen(buildings: Generator) -> Generator:
    """ takes in Generator of features from ijson and yields a tuple for bulk loading into rtree index in the form (id, geometry, object) 
    http://toblerity.org/rtree/tutorial.html#using-rtree-as-a-cheapo-spatial-database 
    """
    for i, building in enumerate(buildings):
        yield (i, shape(building["geometry"]).bounds, building)


def intersection_candidates(features: Generator, idx: Type[index.Index]) -> Generator:
    """ finds all features which do not intersect with building """
    for _, bbox, feature in geojson_gen(features):
        buildings = [n.object for n in idx.intersection(bbox, objects=True)]
        if len(buildings):
            yield (feature, buildings)


def non_intersection_candidates(
    features: Generator, idx: Type[index.Index]
) -> Generator:
    """ finds all features which do not intersect with building"""
    for _, bbox, feature in geojson_gen(features):
        buildings = [n.object for n in idx.intersection(bbox, objects=True)]
        if not len(buildings):
            yield (feature, buildings)


def building_block_intersection(overlaps_candidates: Generator) -> Generator:
    """ """
    for candidate in overlaps_candidates:
        buildings = []
        for building in candidate[1]:
            try:
                intersect = shape(building["geometry"]).intersection(
                    shape(candidate[0]["geometry"])
                )
            except TopologicalError:
                continue
            if intersect:
                buildings.append(building)
        if len(buildings):
            yield (candidate[0]["properties"]["TRACTCE10"], buildings)


def block_building_intersection(overlaps_candidates: Generator) -> Generator:
    """ """
    for candidate in overlaps_candidates:
        for building in candidate[1]:
            try:
                intersect = shape(building["geometry"]).intersection(
                    shape(candidate[0]["geometry"])
                )
            except TopologicalError:
                pass
            if intersect:
                yield candidate[0]


def census_wo_intersection(overlaps_candidates: Generator) -> Generator:
    """ """
    for candidate in overlaps_candidates:
        contains = False
        for building in candidate[1]:
            intersect = shape(building["geometry"]).intersection(
                shape(candidate[0]["geometry"])
            )
            if intersect:
                contains = True
        if not contains:
            yield candidate[0]


def bbox_filter(in_gen: Generator, bbox: Tuple[float, float]) -> Generator:
    """ filters input Generator to bounding box coordinates. Bounding box in format (left, bottom, right, top) """
    for item in in_gen:
        feature = shape(item["geometry"])
        xs, ys = feature.exterior.coords.xy
        x_in_bounds = False
        y_in_bounds = False
        for x in xs:
            if x < bbox[2] and x > bbox[0]:
                x_in_bounds = True
        for y in ys:
            if y < bbox[3] and y > bbox[1]:
                y_in_bounds = True
        if x_in_bounds and y_in_bounds:
            yield item


BBOX = (-106.79191589355469, 34.9805024453652, -106.41426086425781, 35.28878715881986)


def main():
    """ main function """
    with open("./data/abq_building.geojson", "rb") as building_file, open(
        "./data/NewMexico.json", "rb"
    ) as ms_buildings, open("./data/blocks_wgs84.geojson", "rb") as block_file:
        abq_features = ijson.items(building_file, "features.item")
        census_blocks = ijson.items(block_file, "features.item")
        ms_features = ijson.items(ms_buildings, "features.item")
        ms_features = bbox_filter(ms_features, BBOX)
        ms_gen = geojson_gen(ms_features)
        print("indexing ms buildings")
        ms_idx = index.Index(ms_gen, filename="ms_building_idx")
        abq_gen = geojson_gen(abq_features)
        print("indexing osm buildings")
        abq_idx = index.Index(abq_gen, filename="building_idx")
        empty_candidates = non_intersection_candidates(census_blocks, abq_idx)
        empty_blocks = census_wo_intersection(empty_candidates)
        ms_candidates = intersection_candidates(empty_blocks, ms_idx)
        ms_blocks = building_block_intersection(ms_candidates)
        geojson = """{
            "type": "FeatureCollection",
            "features": [\n"""
        print("writing tract files")
        for block in ms_blocks:
            for building in block[1]:
                building["properties"] = {"building": "yes"}
            buildings = [json.dumps(building) for building in block[1]]
            filename = f"./out/tract_{block[0]}.geojson"
            if Path(filename).is_file():
                with open(filename, "a+") as f:
                    data = f.read()
                    for building in buildings:
                        f.write(building)
                        f.write(",")
            else:
                with open(filename, "w") as f:
                    f.write(geojson)
                    for building in buildings:
                        f.write(building)
                        f.write(",")
        files = [path for path in Path("./out").iterdir()]
        for item in files:
            content = b""
            with item.open(mode="rb") as f:
                data = f.read()
                content = data[:-1]
            with item.open(mode="wb") as f:
                content += b"]\n}"
                f.write(content)
        for item in files:
            with item.open(mode="r+") as f:
                data = f.read()
                json_data = json.loads(data)
                features = json_data["features"]
                buildings = list(set([json.dumps(building) for building in features]))
                deduped = [json.loads(building) for building in buildings]
                json_data["features"] = deduped
                f.seek(0)
                f.write(json.dumps(json_data))
                f.truncate()

if __name__ == "__main__":
    main()
