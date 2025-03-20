import os
import sys
import xml.etree.ElementTree as ET
import re

def clean_svg_content(svg_content):
    """
    Cleans an SVG string by:
      1. Removing everything before the first <svg tag.
      2. Removing XML declarations, DOCTYPE (including entity definitions), comments,
         and any namespace declarations with a prefix (e.g., xmlns:x="...").
      3. Removing leftover undefined entity references.
      4. Removing <style>, <metadata>, and unused definitions.
      5. Rebuilding an <svg> that only contains <path> elements.
    """
    # Remove everything before the first <svg tag.
    svg_index = svg_content.find('<svg')
    if svg_index != -1:
        svg_content = svg_content[svg_index:]
    else:
        print("No <svg> tag found!")
        return None

    # Remove XML declarations
    svg_content = re.sub(r'<\?xml.*?\?>', '', svg_content, flags=re.DOTALL)
    # Remove DOCTYPE block (including entity definitions)
    svg_content = re.sub(r'<!DOCTYPE.*?\]>', '', svg_content, flags=re.DOTALL)
    # Remove comments
    svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)
    # Remove any namespace declarations with a prefix (e.g., xmlns:x="...")
    svg_content = re.sub(r'\s+xmlns:[^=]+="[^"]*"', '', svg_content)
    # Remove leftover entity references (like &ns_extend;)
    svg_content = re.sub(r'&[a-zA-Z0-9_]+;', '', svg_content)

    try:
        tree = ET.ElementTree(ET.fromstring(svg_content))
    except ET.ParseError as e:
        print("Error parsing SVG:", e)
        return None

    # Remove namespaces from the parsed tree for simpler tag matching.
    for elem in tree.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    root = tree.getroot()

    # Collect essential attributes from the original <svg>.
    attribs = {}
    for key in ['version', 'xmlns', 'x', 'y', 'viewBox']:
        if key in root.attrib:
            attribs[key] = root.attrib[key]
    # Ensure we have the essential xmlns for SVG.
    if 'xmlns' not in attribs:
        attribs['xmlns'] = "http://www.w3.org/2000/svg"

    # Create a new <svg> element with the essential attributes.
    new_svg = ET.Element('svg', attrib=attribs)

    # Find all <path> elements in the original SVG.
    for path in root.iter('path'):
        # Remove class and style attributes.
        for attr in ['class', 'style']:
            if attr in path.attrib:
                del path.attrib[attr]
        new_svg.append(path)

    # Convert new_svg to a string.
    new_svg_str = ET.tostring(new_svg, encoding='unicode')
    # Add line breaks between tags for readability.
    new_svg_str = re.sub(r'(>)(<)', r'\1\n\2', new_svg_str)
    return new_svg_str.strip()

def process_svg_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = clean_svg_content(content)
    if cleaned is not None:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Processed: {input_path} -> {output_path}")
    else:
        print(f"Skipping {input_path} due to parse errors.")

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for file in os.listdir(input_folder):
        if file.lower().endswith('.svg'):
            in_path = os.path.join(input_folder, file)
            out_path = os.path.join(output_folder, file)
            process_svg_file(in_path, out_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_svg_to_path.py <input_folder> <output_folder>")
        sys.exit(1)
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    process_folder(input_folder, output_folder)
