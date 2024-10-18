#!/bin/bash

# Create and clear the output directory on the host machine
rm -rf output    # Remove the existing output directory and its contents
mkdir -p output  # Recreate the output directory

# Use a Docker container with the ants:latest image
docker run --rm -v "$(pwd)/output":/output antsx/ants:v2.5.3 bash -c "
    # Make sure the /output directory and the commands_docs subdirectory exist in the container
    mkdir -p /output/commands_docs

    # List all commands in the /opt/ants/bin directory
    commands=\$(ls /opt/ants/bin)
    total_commands=\$(echo \"\$commands\" | wc -w)  # Count total number of commands
    count=0  # Initialize a counter

    # Write all command names to a file 'commands.txt'
    echo \"\$commands\" > /output/commands.txt

    # For each command, extract its docstring (if available) and write to a separate file
    for cmd in \$commands; do
        # Increment the counter
        count=\$((count + 1))

        # Print progress
        echo \"Processing command \$count of \$total_commands: \$cmd\"

        # Get the full path to the command
        command_path=/opt/ants/bin/\$cmd

        # Check if the command is executable and not a .R or .pl file
        if [[ -x \$command_path && \$cmd != *.R && \$cmd != *.pl ]]; then
            # Debug: Log the command being run
            echo \"Running: \$command_path\" >> /output/debug.log

            # Use 'bash -c' to run the command to prevent potential subshell issues
            doc=\$(bash -c \"\$command_path --help\" 2>&1)

            # Check if the output is empty
            if [[ -z \"\$doc\" ]]; then
                echo \"No output for \$cmd\" >> /output/debug.log
            else
                # Debug: Log the output of the command
                echo \"Output for \$cmd:\" >> /output/debug.log
                echo \"\$doc\" >> /output/debug.log

                # Write the docstring to a file named after the command in the commands_docs directory
                echo \"\$doc\" > /output/commands_docs/\${cmd}.txt
            fi
        else
            # Log if the command is not executable or is a .R or .pl file
            if [[ \$cmd == *.R ]]; then
                echo \"Skipping .R file: \$cmd\" >> /output/debug.log
            elif [[ \$cmd == *.pl ]]; then
                echo \"Skipping .pl file: \$cmd\" >> /output/debug.log
            else
                echo \"Skipping non-executable: \$cmd\" >> /output/debug.log
            fi
        fi
    done

    echo \"Processing complete.\"
"
