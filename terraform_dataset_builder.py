import os
import json
import random

# Configurations
GOLDEN_MODULES_DIR = "./golden-terraform-modules"  # Path to your golden modules
OUTPUT_DATASET_FILE = "terraform_governance_dataset.jsonl"  # Output dataset file

# Example of golden module references
GOLDEN_REFERENCES = {
    "azure/storage_account": {
        "mandatory_parameters": [
            "resource_group_name", "location", "account_tier",
            "account_replication_type", "min_tls_version",
            "allow_blob_public_access", "tags"
        ],
        "defaults": {
            "min_tls_version": "TLS1_2",
            "allow_blob_public_access": False
        },
        "constraints": {
            "tags.must_include": ["Environment", "Owner"]
        }
    },
    "azure/virtual_network": {
        "mandatory_parameters": [
            "resource_group_name", "location", "address_space", "tags"
        ],
        "defaults": {},
        "constraints": {
            "tags.must_include": ["Environment", "Owner"]
        }
    }
}

# Prompt Templates
PROMPT_TEMPLATE = (
    "Given the following Terraform resource code snippet, rewrite it using the approved module standard. "
    "Ensure all mandatory parameters are included, defaults are respected, and best practices applied.\n\n"
    "Terraform Resource Code:\n{code}\n\n"
    "Golden Module Standard: {module_path}\n"
)

# Completion Template
COMPLETION_TEMPLATE = """module "{module_name}" {{
  source = "{module_source}"
{parameters}
}}"""

# Function to generate a fake resource block (for simulation)
def generate_fake_resource(module_name, reference, error_type=None):
    code_lines = [f'resource \"{module_name.replace("/", "_")}_resource\" \"example\" {{']
    params = reference["mandatory_parameters"].copy()
    
    if error_type == "missing_params":
        params = random.sample(params, max(1, len(params) - 2))
    for param in params:
        if param == "tags":
            if error_type == "wrong_tags":
                code_lines.append("  tags = { App = \"MyApp\" }")
            else:
                code_lines.append("  tags = {}")
        else:
            if error_type == "wrong_defaults" and param in reference.get("defaults", {}):
                wrong_value = "TLS1_0" if param == "min_tls_version" else "example_wrong"
                code_lines.append(f"  {param} = \"{wrong_value}\"")
            else:
                code_lines.append(f"  {param} = \"example\"")
    code_lines.append("}")
    return "\n".join(code_lines)

def generate_partial_module(module_name, reference):
    code_lines = [f'module \"{module_name.split("/")[-1]}\" {{']
    code_lines.append(f'  source = \"../modules/{module_name}\"')
    params = random.sample(reference["mandatory_parameters"], max(1, len(reference["mandatory_parameters"]) - 1))
    for param in params:
        code_lines.append(f"  {param} = \"example\"")
    code_lines.append("}")
    return "\n".join(code_lines)

# Function to generate completion block
def generate_completion(module_name, reference):
    param_lines = []
    for param in reference["mandatory_parameters"]:
        if param == "tags":
            param_lines.append("    tags = {\n      Environment = \"Production\"\n      Owner = \"DevOps Team\"\n    }")
        else:
            default_value = reference["defaults"].get(param, "example")
            val = f'\"{default_value}\"' if isinstance(default_value, str) else str(default_value).lower()
            param_lines.append(f"    {param} = {val}")
    return COMPLETION_TEMPLATE.format(
        module_name=module_name.split("/")[-1],
        module_source=f"../modules/{module_name}",
        parameters="\n".join(param_lines)
    )

# Main generator
def generate_dataset():
    samples = []
    for module_path, reference in GOLDEN_REFERENCES.items():
        # 1. Direct resource usage
        fake_code = generate_fake_resource(module_path, reference)
        prompt = PROMPT_TEMPLATE.format(code=fake_code, module_path=module_path)
        completion = generate_completion(module_path, reference)
        samples.append({"input": prompt.strip(), "output": completion.strip()})

        # 2. Missing parameters
        fake_code = generate_fake_resource(module_path, reference, error_type="missing_params")
        prompt = PROMPT_TEMPLATE.format(code=fake_code, module_path=module_path)
        samples.append({"input": prompt.strip(), "output": completion.strip()})

        # 3. Wrong default values
        fake_code = generate_fake_resource(module_path, reference, error_type="wrong_defaults")
        prompt = PROMPT_TEMPLATE.format(code=fake_code, module_path=module_path)
        samples.append({"input": prompt.strip(), "output": completion.strip()})

        # 4. Wrong or missing tags
        fake_code = generate_fake_resource(module_path, reference, error_type="wrong_tags")
        prompt = PROMPT_TEMPLATE.format(code=fake_code, module_path=module_path)
        samples.append({"input": prompt.strip(), "output": completion.strip()})

        # 5. Partial module usage
        partial_module_code = generate_partial_module(module_path, reference)
        prompt = PROMPT_TEMPLATE.format(code=partial_module_code, module_path=module_path)
        samples.append({"input": prompt.strip(), "output": completion.strip()})

    return samples

# Write to JSONL

def save_dataset(samples, file_path):
    with open(file_path, 'w') as f:
        for sample in samples:
            json.dump(sample, f)
            f.write("\n")

if __name__ == "__main__":
    dataset_samples = generate_dataset()
    save_dataset(dataset_samples, OUTPUT_DATASET_FILE)
    print(f"Generated {len(dataset_samples)} samples into {OUTPUT_DATASET_FILE}")
