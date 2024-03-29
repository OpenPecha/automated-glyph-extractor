import json
import gzip
import re
import os
from openpecha.utils import load_yaml
from pathlib import Path
from utils import crop_and_resize

essential_list = Path(f"./data/tibetan_essential_list.txt").read_text().split("\n")


def get_bounding_poly_for_symbol(ocr_path):
    curr = []
    bounding_polys = []
    ocr_objects = json.load(gzip.open(str(ocr_path), "rb"))
    if ocr_objects == {}:
        return
    if "fullTextAnnotation" not in ocr_objects:
        return
    for blocks in ocr_objects["fullTextAnnotation"]["pages"][0]['blocks']:
        if blocks["paragraphs"] == []:
            continue
        for bounding_box in blocks["paragraphs"][0]['words']:
            symbols_dict = bounding_box["symbols"]
            for symbol_dict in symbols_dict:
                text = symbol_dict["text"]
                vertices = symbol_dict["boundingBox"]["vertices"]
                curr = [{
                    'text': text,
                    'vertices': vertices
                    }]
                bounding_polys.append(curr)
                curr = {}
    return bounding_polys


def numerical_sort(file_path):
    numbers = re.findall(r'\d+', str(file_path))
    return int(numbers[0]) if numbers else 0

def get_image_name(output_dir, text):
    if any(output_dir.iterdir()) == False:
        return f"{text}_1"
    else:
        image_path = sorted(list(output_dir.iterdir()), key=numerical_sort)[-1]
        curr_name = image_path.stem
        name = int(curr_name.split("_")[-1])
        image_name = f"{text}_"+str(name + 1)  
        return image_name

def get_source_image_path(ocr_path, source_dir_path):
    filename = (ocr_path.stem).split(".")[0]
    for image_path in source_dir_path.iterdir():
        image_name = image_path.stem
        if filename == image_name:
            return image_path

def update_csv(cropped_image_path, vertices, image_path, font_name):
    filename = cropped_image_path.split("/")[-1]
    with open(f"./{font_name}_glyphs.csv", "a") as f:
        f.write(f"{filename}, {image_path}, {vertices}\n")

def extract_symbols(ocr_paths, source_dir_path, done_list, font_name):
    for num, ocr_path in enumerate(ocr_paths, 1):
        print(num)
        source_image_path = get_source_image_path(ocr_path, source_dir_path)
        bounding_polys = get_bounding_poly_for_symbol(ocr_path)
        if bounding_polys == None:
            continue
        for value in bounding_polys:
            text = value[0]['text']
            if text in done_list:
                continue
            if text in essential_list:
                vertices = value[0]['vertices']
                output_path = Path(f"./data/glyphs/{text}")
                if output_path.exists() == False:
                    output_path.mkdir(parents=True, exist_ok=True)
                image_name = get_image_name(output_path, text)
                if int(image_name.split("_")[-1]) > 100 :
                    continue
                cropped_image_path = f"{output_path}/{image_name}.png"
                cropped_image, new_vertices = crop_and_resize(source_image_path, vertices)
                if cropped_image == None:
                    continue
                cropped_image.save(cropped_image_path, 'PNG')
                update_csv(cropped_image_path, new_vertices, source_image_path, font_name)
                
