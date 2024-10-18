import json
import os
import glob
import pathlib
from jsonschema import validate
from openai import OpenAI
from tqdm import tqdm
import concurrent.futures

# Configuration for the OpenAI API
client = OpenAI(
    api_key=os.environ["OAI_API_KEY"],
    organization=os.environ["OAI_ORG"],
)

# Load the Boutiques schema
with open("descriptor.schema.json", 'r') as f:
    BOUTIQUES_SCHEMA = json.load(f)

def load_file(filename):
    """Load the contents of a file."""
    with open(filename, 'r') as f:
        return f.read()

def generate_system_prompt():
    """Generate the system prompt for the OpenAI API."""
    example_help_text = load_file("examples/ants_help.txt")
    example_descriptor_text = load_file("examples/ants_descriptor.json")

    return (
        "You are BoutiquesGeneratorGPT. You convert command line tool help texts to Boutiques descriptors.\n\n"
        f"Here is an example help text:\n\n{example_help_text}\n\n"
        f"And here is the corresponding Boutiques descriptor (this is what you should produce):\n\n{example_descriptor_text}\n\n"
        "Respond only with JSON formatted text. You can use the example help text as a reference."
    )

def generate_boutiques_descriptor(help_text):
    """Generate a Boutiques descriptor from the help text using OpenAI API."""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": generate_system_prompt()},
            {"role": "user", "content": help_text}
        ]
    )
    return completion.choices[0].message.content

def save_boutiques_descriptor(descriptor, filename):
    """Save the Boutiques descriptor to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(descriptor, f, indent=2)

def clean_and_validate_descriptor(boutiques_descriptor):
    """Clean the response and validate against the schema."""
    lines = boutiques_descriptor.strip().split("\n")
    start = next((i for i, line in enumerate(lines) if line == "```json"), 0)
    end = next((i for i, line in enumerate(lines[start+1:], start+1) if line == "```"), len(lines))
    
    boutiques_descriptor = "\n".join(lines[start+1:end])
    boutiques_descriptor = json.loads(boutiques_descriptor)
    validate(boutiques_descriptor, BOUTIQUES_SCHEMA)
    return boutiques_descriptor

def process_help_file(file, output_dir):
    """Process a single help file and generate the corresponding Boutiques descriptor."""
    tool = pathlib.Path(file).stem
    out_path = os.path.join(output_dir, f"{tool}.json")

    if os.path.exists(out_path):
        return f"Descriptor for {tool} already exists. Skipping."

    help_text = load_file(file)
    if tool not in help_text:
        help_text = f"{tool}\n\n{help_text}"

    for attempt in range(5):  # Retry up to 5 times
        try:
            boutiques_descriptor = generate_boutiques_descriptor(help_text)
            boutiques_descriptor = clean_and_validate_descriptor(boutiques_descriptor)
            save_boutiques_descriptor(boutiques_descriptor, out_path)
            return f"Successfully generated descriptor for {tool}."
        except Exception as e:
            if attempt == 4:  # Last attempt
                return f"Failed to generate descriptor for {tool} after multiple attempts: {e}"

def process_help_files(help_files_pattern="output/commands_docs/*.txt", output_dir="descriptors", max_workers=5):
    """Process each help file and generate the corresponding Boutiques descriptor in parallel."""
    os.makedirs(output_dir, exist_ok=True)
    files = glob.glob(help_files_pattern)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_help_file, file, output_dir): file for file in files}
        for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(files), desc="Processing help files"):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                tqdm.write(result)  # Print the result without interfering with the progress bar
            except Exception as exc:
                tqdm.write(f'{file} generated an exception: {exc}')

    return results

if __name__ == "__main__":
    process_help_files()
