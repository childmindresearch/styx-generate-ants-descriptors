#!/bin/bash

# extract.sh
#
# Purpose:
# This script extracts documentation and help information from executable files
# within a specified directory in a Docker container. It's designed to work with
# neuroimaging software packages like AFNI, FSL, and ANTs.
#
# Usage:
# ./extract.sh <output_directory> <docker_tag> <binaries_directory> <timeout_duration> <max_output_size>
#
# Parameters:
# - output_directory: Directory where the extracted documentation will be saved
# - docker_tag: Docker image tag to use (e.g., "afni/afni_make_build:AFNI_24.2.06")
# - binaries_directory: Directory within the Docker container containing the executables
# - timeout_duration: Maximum time (in seconds) allowed for each command execution
# - max_output_size: Maximum size (in bytes) for each command's output
#
# Functionality:
# 1. Creates and clears the specified output directory
# 2. Runs a Docker container using the provided image tag
# 3. Within the container:
#    a. Lists all executable files in the specified directory (excluding .so files)
#    b. Sorts the list of executables for reproducibility
#    c. Creates a 'commands.txt' file with all executable names
#    d. For each executable:
#       - Runs the command with --help, -help, and no arguments
#       - Captures the output, limiting it to the specified maximum size
#       - Saves the output to individual files in the 'commands_docs' subdirectory
#    e. Logs timeouts and truncations
#    f. Creates a summary of timeouts
#
# Output:
# - commands.txt: List of all executable names
# - commands_docs/: Directory containing individual documentation files for each command
# - debug.log: Log file with debug information
# - timeouts.log: Log file with timeout information and summary
#
# Notes:
# - The script uses 'LC_ALL=C sort' for consistent sorting across different systems
# - Empty output files are removed to save space
# - Progress is displayed in the terminal during execution
#
# Example usage for AFNI:
# ./extract.sh "output/afni" "afni/afni_make_build:AFNI_24.2.06" "/opt/afni/src/../install" 10 100000
#
# This example extracts documentation for AFNI, with a 10-second timeout per command
# and a maximum output size of 100KB per command.


# Check if all required arguments are provided
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <output_directory> <docker_tag> <binaries_directory> <timeout_duration> <max_output_size>"
    exit 1
fi

OUTPUT_DIR="$1"
DOCKER_TAG="$2"
BIN_DIR="$3"
TIMEOUT_DURATION="$4"
MAX_OUTPUT_SIZE="$5"  # Maximum output size in bytes

# Create and clear the output directory on the host machine
rm -rf "$OUTPUT_DIR"    # Remove the existing output directory and its contents
mkdir -p "$OUTPUT_DIR"  # Recreate the output directory

# Use a Docker container with the specified image
docker run --rm -v "$(pwd)/$OUTPUT_DIR":/output "$DOCKER_TAG" bash -c '
    # Make sure the /output directory and the commands_docs subdirectory exist in the container
    mkdir -p /output/commands_docs

    # List all executable files in the specified directory (without descending into subdirectories and excluding .so files)
    # Then sort the list for reproducibility, using LC_ALL=C to ensure consistent sorting
    executables=$(find '"$BIN_DIR"' -maxdepth 1 -type f -executable ! -name "*.so" | LC_ALL=C sort)
    total_executables=$(echo "$executables" | wc -l)  # Count total number of executables
    count=0  # Initialize a counter

    # Write all executable names (without path and excluding .so files) to a file '"'"'commands.txt'"'"'
    find '"$BIN_DIR"' -maxdepth 1 -type f -executable ! -name "*.so" -printf "%f\n" | LC_ALL=C sort > /output/commands.txt

    # Create a file to log timeouts
    touch /output/timeouts.log

    # Function to run command with timeout and header, and truncate output if necessary
    run_with_timeout_and_header() {
        local cmd=$1
        local args=$2
        local header=$3
        local output_file=/output/commands_docs/$(basename ${cmd}).txt
        echo -e "$header" >> $output_file
        timeout '"$TIMEOUT_DURATION"'s bash -c "$cmd $args" 2>&1 | {
            head -c '"$MAX_OUTPUT_SIZE"' >> $output_file
            if [ "$(wc -c < $output_file)" -gt '"$MAX_OUTPUT_SIZE"' ]; then
                echo -e "\n\n... Output truncated due to size limit ..." >> $output_file
                return 124  # Return timeout status to indicate truncation
            fi
        }
        local exit_status=${PIPESTATUS[0]}
        if [ $exit_status -eq 124 ]; then
            echo "Command '"'"'$cmd $args'"'"' timed out after '"$TIMEOUT_DURATION"' seconds" >> /output/timeouts.log
            echo "Command timed out after '"$TIMEOUT_DURATION"' seconds" >> $output_file
        fi
        return $exit_status
    }

    # For each executable, extract its help text (if available) and write to a separate file
    for cmd in $executables; do
        # Increment the counter
        count=$((count + 1))

        # Print progress (to stderr so it appears in terminal)
        echo "Processing executable $count of $total_executables: $cmd" >&2

        # Debug: Log the command being run
        echo "Running: $cmd" >> /output/debug.log

        # Run all three options for each command
        run_with_timeout_and_header "$cmd" "--help" "\n=== Output of '"'"'$(basename ${cmd}) --help'"'"' ===\n"
        run_with_timeout_and_header "$cmd" "-help" "\n=== Output of '"'"'$(basename ${cmd}) -help'"'"' ===\n"
        run_with_timeout_and_header "$cmd" "" "\n=== Output of '"'"'$(basename ${cmd})'"'"' (no arguments) ===\n"

        # Check if the output file is empty
        if [ ! -s /output/commands_docs/$(basename ${cmd}).txt ]; then
            echo "No output for $(basename ${cmd})" >> /output/debug.log
            rm /output/commands_docs/$(basename ${cmd}).txt  # Remove empty file
        else
            # Debug: Log that output was captured
            echo "Output captured for $(basename ${cmd})" >> /output/debug.log
        fi
    done

    echo "Processing complete." >&2
    
    # Print summary of timeouts
    echo -e "\nTimeout Summary:" >> /output/timeouts.log
    LC_ALL=C sort /output/timeouts.log | uniq -c | LC_ALL=C sort -nr >> /output/timeouts.log
'
