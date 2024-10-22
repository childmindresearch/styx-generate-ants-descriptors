# LLM Neuroimaging Boutiques Descriptor Generator

This repository contains scripts to automatically generate Boutiques descriptors for various neuroimaging software packages, including ANTs (Advanced Normalization Tools), FSL, AFNI and FreeSurfer.

## Overview

The process of generating Boutiques descriptors is divided into three main steps:

1. **Documentation Extraction**: Extracts help texts and documentation from neuroimaging software commands.
2. **Descriptor Generation**: Uses AI language models to generate Boutiques descriptors from the extracted documentation.
3. **Package Compilation**: Compiles the generated descriptors into a structured package.

## Scripts

1. `extract_<package>.sh`: Extracts documentation for commands from specified neuroimaging software packages using Docker containers.
2. `llm.py <package>`: Generates Boutiques descriptors from command help texts using AI language models (e.g., OpenAI's GPT-4).
3. `build.py <package>`: Compiles the generated descriptors into a structured package.

## Requirements

- Docker
- Python 3.11+
- OpenAI API key (if using OpenAI's models)
