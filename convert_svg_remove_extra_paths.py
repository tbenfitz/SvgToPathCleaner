import os
import sys
import re
import xml.etree.ElementTree as ET

def remove_inner_subpaths(d_value):
    """
    Given a 'd' attribute string, this function finds all subpaths that start with 'M' (or 'm')
    and end with 'z' (or 'Z'). If more than one subpath is found, it returns only the first one.
    Otherwise, it returns the original d_value.
    """
    # This regex finds subpaths: it looks for an 'M' followed by any characters (non-greedy)
    # until the first 'z' or 'Z'.
    parts = re.findall(r'(M.*?[zZ])', d_value, flags=re.IGNORECASE)
    if len(parts) > 1:
        return parts[0]
    return d_value

def process_svg_file(input_path, output_path):
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {input_path}: {e}")
        return

    # Optionally, remove namespaces for easier matching (if present)
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]

    modified = False
    # Process each <path> element
    for path in root.iter('path'):
        d_attr = path.get("d")
        if d_attr:
            new_d = remove_inner_subpaths(d_attr)
            if new_d != d_attr:
                path.set("d", new_d)
                modified = True

    # Write out the updated SVG file
    tree.write(output_path, encoding="utf-8", xml_declaration=False)
    if modified:
        print(f"Modified {input_path} -> {output_path}")
    else:
        print(f"No changes for {input_path}, file written to {output_path}")

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for file in os.listdir(input_folder):
        if file.lower().endswith('.svg'):
            input_file = os.path.join(input_folder, file)
            output_file = os.path.join(output_folder, file)
            process_svg_file(input_file, output_file)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python remove_inner_subpath.py <input_folder> <output_folder>")
        sys.exit(1)
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    process_folder(input_folder, output_folder)
