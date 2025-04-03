import os
import sys
import subprocess

# Hardcoded path to the Inkscape executable.
# Adjust this path as necessary for your OS/environment.
INKSCAPE_PATH = "C:\\Program Files\\Inkscape\\inkscape.exe"

def convert_with_inkscape(input_path, output_path):
    """
    Uses Inkscape v0.92's command-line interface (using verbs) to convert the SVG so that strokes are
    converted to filled paths and exports a plain SVG.
    """
    # Build the command. Inkscape v0.92 uses the --verb flags.
    cmd = [
        INKSCAPE_PATH,
        input_path,
        "--verb=EditSelectAll",
        "--verb=StrokeToPath",
        "--verb=FileSave",
        "--verb=FileQuit",
        "--export-plain-svg=" + output_path
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Processed with Inkscape: {input_path} -> {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path} with Inkscape: {e}")

def process_svg_file(input_path, output_path):
    convert_with_inkscape(input_path, output_path)

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
