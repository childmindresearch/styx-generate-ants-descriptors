# ANTs Boutiques Descriptor Generator

This repository contains scripts to automatically generate Boutiques descriptors for ANTs (Advanced Normalization Tools) commands.

## Scripts

1. `extract.sh`: Extracts documentation for ANTs commands using a Docker container.
2. `llm.py`: Generates Boutiques descriptors from command help texts using OpenAI's GPT-4o.
3. `build.py`: Compiles the generated descriptors into a structured package.

## Requirements

- Docker
- Python 3.11
- OpenAI API key

## Output

The final output is stored in the `dist` directory, containing:
- Individual Boutiques descriptors for ANTs commands
- An `ants.json` file with package metadata and command statuses

Contents of the folder can then be merged into [NiWrap](https://github.com/childmindresearch/niwrap) for human review.
