import json
from pathlib import Path

def read_commands(file_path):
    """Read commands from the specified file."""
    with file_path.open('r') as f:
        return [line.strip() for line in f if line.strip()]

def get_descriptor_status(command, descriptor_dir):
    """Check if a descriptor exists for the given command and determine its status."""
    if command.endswith(('.R', '.pl')):
        return "ignore", None
    
    descriptor_path = Path(descriptor_dir) / f"{command}.json"
    if descriptor_path.exists():
        return "done", f"descriptors/ants/{command}.json"
    return "missing", None

def copy_and_patch_descriptor(src_path, dest_path, ants_data):
    """Copy the descriptor to the new location and patch it with additional fields."""
    with src_path.open('r') as f:
        descriptor = json.load(f)
    
    # Update fields
    descriptor['name'] = src_path.stem
    descriptor['author'] = "ANTs developers"
    descriptor['description'] = ants_data['description']
    descriptor['url'] = ants_data['url']
    descriptor['tool-version'] = ants_data['version']
    descriptor["container-image"] = {
        "type": "docker",
        "image": "antsx/ants:v2.5.3"
    }
    
    # Write updated descriptor to new location
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open('w') as f:
        json.dump(descriptor, f, indent=2)

def generate_ants_json(commands_file, output_file):
    """Generate the ants.json file and copy+patch existing descriptors."""
    commands = read_commands(commands_file)
    
    ants_data = {
        "id": "ants",
        "name": "ANTs",
        "url": "https://github.com/ANTsX/ANTs",
        "approach": "Manual",
        "status": "In progress",
        "container": "antsx/ants:v2.5.3",
        "version": "2.5.3",
        "description": "Advanced Normalization Tools (ANTs) is a C++ library available through the command line that computes high-dimensional mappings to capture the statistics of brain structure and function. It allows one to organize, visualize and statistically explore large biomedical image sets. Additionally, it integrates imaging modalities in space + time and works across species or organ systems with minimal customization.\n\nThe ANTs library is considered a state-of-the-art medical image registration and segmentation toolkit which depends on the Insight ToolKit, a widely used medical image processing library to which ANTs developers contribute. ANTs-related tools have also won several international, unbiased competitions such as MICCAI, BRATS, and STACOM.",
        "api": {
            "endpoints": []
        }
    }
    
    for command in commands:
        status, descriptor_path = get_descriptor_status(command, descriptor_dir="descriptors")
        endpoint = {
            "target": command,
            "status": status
        }
        if descriptor_path:
            endpoint["descriptor"] = descriptor_path
            # Copy and patch the descriptor
            src_full_path = Path("descriptors") / Path(descriptor_path).name
            dest_full_path = Path("dist") / descriptor_path
            copy_and_patch_descriptor(src_full_path, dest_full_path, ants_data)
        ants_data["api"]["endpoints"].append(endpoint)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        json.dump(ants_data, f, indent=2)

    print(f"Generated {output_file}")
    print(f"Copied and patched descriptors.")

if __name__ == "__main__":
    commands_file = Path("output/commands.txt")
    output_file = Path("dist/packages/ants.json")
    
    generate_ants_json(commands_file, output_file)
