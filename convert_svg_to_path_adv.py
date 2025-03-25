import os
import sys
import xml.etree.ElementTree as ET
import re

def rect_to_path(elem):
    try:
        x = float(elem.get("x", "0"))
        y = float(elem.get("y", "0"))
        width = float(elem.get("width", "0"))
        height = float(elem.get("height", "0"))
    except ValueError:
        return None
    # Optional rounded corners
    rx = elem.get("rx")
    ry = elem.get("ry")
    if rx is None or ry is None:
        rx = ry = 0
    else:
        try:
            rx = float(rx)
            ry = float(ry)
        except ValueError:
            rx = ry = 0

    if rx == 0 and ry == 0:
        # Simple rectangle
        d = f"M{x},{y} h{width} v{height} h{-width} Z"
    else:
        # Rounded rectangle approximation
        d = (
            f"M{x+rx},{y} "
            f"H{x+width-rx} "
            f"A{rx},{ry} 0 0 1 {x+width},{y+ry} "
            f"V{y+height-ry} "
            f"A{rx},{ry} 0 0 1 {x+width-rx},{y+height} "
            f"H{x+rx} "
            f"A{rx},{ry} 0 0 1 {x},{y+height-ry} "
            f"V{y+ry} "
            f"A{rx},{ry} 0 0 1 {x+rx},{y} Z"
        )
    return d

def circle_to_path(elem):
    try:
        cx = float(elem.get("cx", "0"))
        cy = float(elem.get("cy", "0"))
        r = float(elem.get("r", "0"))
    except ValueError:
        return None
    # Create a circle path using two arc commands.
    d = (
        f"M{cx - r},{cy} "
        f"a{r},{r} 0 1,0 {2*r},0 "
        f"a{r},{r} 0 1,0 {-2*r},0 Z"
    )
    return d

def ellipse_to_path(elem):
    try:
        cx = float(elem.get("cx", "0"))
        cy = float(elem.get("cy", "0"))
        rx = float(elem.get("rx", "0"))
        ry = float(elem.get("ry", "0"))
    except ValueError:
        return None
    d = (
        f"M{cx - rx},{cy} "
        f"a{rx},{ry} 0 1,0 {2*rx},0 "
        f"a{rx},{ry} 0 1,0 {-2*rx},0 Z"
    )
    return d

def line_to_path(elem):
    try:
        x1 = float(elem.get("x1", "0"))
        y1 = float(elem.get("y1", "0"))
        x2 = float(elem.get("x2", "0"))
        y2 = float(elem.get("y2", "0"))
    except ValueError:
        return None
    d = f"M{x1},{y1} L{x2},{y2}"
    return d

def polyline_to_path(elem):
    points = elem.get("points", "").strip()
    if not points:
        return None
    # Normalize the points string (replace commas with spaces)
    points = re.sub(r',', ' ', points)
    parts = points.split()
    if len(parts) < 2:
        return None
    try:
        coords = [float(p) for p in parts]
    except ValueError:
        return None
    pairs = [f"{coords[i]},{coords[i+1]}" for i in range(0, len(coords), 2)]
    d = "M" + " L".join(pairs)
    return d

def polygon_to_path(elem):
    d = polyline_to_path(elem)
    if d is not None:
        d += " Z"
    return d

def convert_element_to_path(elem):
    tag = elem.tag.lower()
    if tag == "path":
        return elem.get("d")
    elif tag == "rect":
        return rect_to_path(elem)
    elif tag == "circle":
        return circle_to_path(elem)
    elif tag == "ellipse":
        return ellipse_to_path(elem)
    elif tag == "line":
        return line_to_path(elem)
    elif tag == "polyline":
        return polyline_to_path(elem)
    elif tag == "polygon":
        return polygon_to_path(elem)
    return None

def clean_svg_content(svg_content, keep_newlines=False):
    """
    Cleans an SVG string by:
      1. Removing everything before the first <svg> tag.
      2. Removing XML declarations, DOCTYPE (including entity definitions), comments,
         and any namespace declarations with a prefix (e.g., xmlns:x="...").
      3. Removing leftover undefined entity references.
      4. Removing <style>, <metadata>, and unused definitions.
      5. Rebuilding an <svg> that contains only <path> elements, converting shapes to paths.
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

    # Remove namespaces for simpler tag matching.
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

    # Process common shape elements.
    shape_tags = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
    for elem in root.iter():
        if elem.tag.lower() in shape_tags:
            d = convert_element_to_path(elem)
            if d:
                new_path = ET.Element('path', attrib={'d': d})
                # Optionally, remove unwanted attributes.
                new_svg.append(new_path)

    # Convert the new SVG tree back to a string.
    new_svg_str = ET.tostring(new_svg, encoding='unicode')
    new_svg_str = re.sub(r'(>)(<)', r'\1\n\2', new_svg_str)  # add line breaks for readability
    
     # Convert the new SVG tree back to a string.
    new_svg_str = ET.tostring(new_svg, encoding='unicode')
    
    if keep_newlines:
        # Add line breaks between tags for readability.
        new_svg_str = re.sub(r'(>)(<)', r'\1\n\2', new_svg_str)
    else:
        # Remove all extraneous whitespace so it's all on one line.
        new_svg_str = re.sub(r'\s+', ' ', new_svg_str).strip()

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
