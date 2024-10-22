import json
from pathlib import Path
import argparse

def read_commands(file_path):
    """Read commands from the specified file."""
    with file_path.open('r') as f:
        return [line.strip() for line in f if line.strip()]

def get_descriptor_status(command, descriptor_dir):
    """Check if a descriptor exists for the given command and determine its status."""
    descriptor_path = Path(descriptor_dir) / f"{command}.json"
    if descriptor_path.exists():
        return "done", f"descriptors/{descriptor_dir.name}/{command}.json"
    return "missing", None

def copy_and_patch_descriptor(src_path, dest_path, package_data):
    """Copy the descriptor to the new location and patch it with additional fields."""
    with src_path.open('r') as f:
        descriptor = json.load(f)
    
    # Update fields
    descriptor['name'] = src_path.stem
    descriptor['author'] = package_data['author']
    descriptor['url'] = package_data['url']
    descriptor['tool-version'] = package_data['version']
    descriptor["container-image"] = {
        "type": "docker",
        "image": package_data['container']
    }
    
    # Write updated descriptor to new location
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open('w') as f:
        json.dump(descriptor, f, indent=2)

def generate_package_json(package_id, commands_file, output_file):
    """Generate the package JSON file and copy+patch existing descriptors."""
    commands = read_commands(commands_file)
    
    # Load package-specific data (you might want to store this in a separate config file)
    package_data = {
        "ants": {
            "name": "ANTs",
            "author": "ANTs developers",
            "url": "https://github.com/ANTsX/ANTs",
            "approach": "Manual",
            "status": "In progress",
            "container": "antsx/ants:v2.5.3",
            "version": "2.5.3",
            "description": "Advanced Normalization Tools (ANTs) is a C++ library available through the command line that computes high-dimensional mappings to capture the statistics of brain structure and function. It allows one to organize, visualize and statistically explore large biomedical image sets. Additionally, it integrates imaging modalities in space + time and works across species or organ systems with minimal customization.\n\nThe ANTs library is considered a state-of-the-art medical image registration and segmentation toolkit which depends on the Insight ToolKit, a widely used medical image processing library to which ANTs developers contribute. ANTs-related tools have also won several international, unbiased competitions such as MICCAI, BRATS, and STACOM.",
        },
        "fsl": {
            "name": "FSL",
            "author": "FMRIB Analysis Group, University of Oxford",
            "url": "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki",
            "approach": "Manual",
            "status": "In progress",
            "container": "mcin/fsl:6.0.5",
            "version": "6.0.5",
            "description": "FSL is a comprehensive library of analysis tools for FMRI, MRI and diffusion brain imaging data. It runs on macOS (Intel and M1/M2/M3), Linux, and Windows via the Windows Subsystem for Linux, and is very easy to install. Most of the tools can be run both from the command line and as GUIs (\"point-and-click\" graphical user interfaces). To quote the relevant references for FSL tools you should look in the individual tools' manual pages, and also please reference one or more of the FSL overview papers:\n\nM.W. Woolrich, S. Jbabdi, B. Patenaude, M. Chappell, S. Makni, T. Behrens, C. Beckmann, M. Jenkinson, S.M. Smith. Bayesian analysis of neuroimaging data in FSL. NeuroImage, 45:S173-86, 2009\n\nS.M. Smith, M. Jenkinson, M.W. Woolrich, C.F. Beckmann, T.E.J. Behrens, H. Johansen-Berg, P.R. Bannister, M. De Luca, I. Drobnjak, D.E. Flitney, R. Niazy, J. Saunders, J. Vickers, Y. Zhang, N. De Stefano, J.M. Brady, and P.M. Matthews. Advances in functional and structural MR image analysis and implementation as FSL. NeuroImage, 23(S1):208-19, 2004\n\nM. Jenkinson, C.F. Beckmann, T.E. Behrens, M.W. Woolrich, S.M. Smith. FSL. NeuroImage, 62:782-90, 2012",
        },
        "afni": {
            "name": "AFNI",
            "author": "AFNI Developers",
            "url": "https://afni.nimh.nih.gov/",
            "approach": "Manual",
            "status": "In progress",
            "container": "afni/afni_make_build:AFNI_24.2.06",
            "version": "24.2.06",
            "description": "AFNI (Analysis of Functional NeuroImages) is a leading software suite of C, Python, R programs and shell scripts primarily developed for the analysis and display of multiple MRI modalities: anatomical, functional MRI (FMRI) and diffusion weighted (DW) data. It is freely available (both as open source code and as precompiled binaries) for research purposes. The software is made to run on virtually any Unix system with X11 and Motif displays. Binary packages are provided for MacOS and Linux systems such as Fedora, CentOS/Red Hat and Ubuntu (which includes the Windows Subsystem for Linux).",
        },
        "freesurfer": {
            "name": "FreeSurfer",
            "author": "FreeSurfer Developers",
            "url": "https://github.com/freesurfer/freesurfer",
            "approach": "Manual",
            "status": "In progress",
            "container": "freesurfer/freesurfer:7.4.1",
            "version": "7.4.1",
            "description": "FreeSurfer is a software package for the analysis and visualization of neuroimaging data from cross-sectional and longitudinal studies. It is developed by the Laboratory for Computational Neuroimaging at the Martinos Center for Biomedical Imaging.\n\nFreeSurfer provides full processing streams for structural and functional MRI and includes tools for linear and nonlinear registration, cortical and subcortical segmentation, cortical surface reconstruction, statistical analysis of group morphometry, diffusion MRI, PET analysis, and much more. It is also the structural MRI analysis software of choice for the Human Connectome Project.",
        },
        # Add more package data as needed
    }
    
    if package_id not in package_data:
        raise ValueError(f"Unknown package ID: {package_id}")
    
    data = package_data[package_id]
    data["id"] = package_id
    data["api"] = {"endpoints": []}
    
    descriptor_dir = Path("descriptors") / package_id
    for command in commands:
        status, descriptor_path = get_descriptor_status(command, descriptor_dir)
        endpoint = {
            "target": command,
            "status": status
        }
        if descriptor_path:
            endpoint["descriptor"] = descriptor_path
            # Copy and patch the descriptor
            src_full_path = Path("descriptors") / package_id / Path(descriptor_path).name
            dest_full_path = Path("dist") / descriptor_path
            copy_and_patch_descriptor(src_full_path, dest_full_path, data)
        data["api"]["endpoints"].append(endpoint)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        json.dump(data, f, indent=2)

    print(f"Generated {output_file}")
    print(f"Copied and patched descriptors.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate package JSON and patch descriptors")
    parser.add_argument("package_id", help="ID of the neuroimaging package (e.g., 'ants', 'fsl')")
    args = parser.parse_args()

    commands_file = Path(f"output/{args.package_id}/commands.txt")
    output_file = Path(f"dist/packages/{args.package_id}.json")
    
    generate_package_json(args.package_id, commands_file, output_file)
