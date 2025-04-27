# AI llama training


## Purpose

- Automatically generate prompt-completion pairs from your golden Terraform modules.
- Focus on enforcing:
    - Correct usage of modules
    - Mandatory parameters
    - Default values
    - Best practices (like tagging, TLS minimums, etc.)
- Output the dataset in JSONL (newline-separated JSON) format ready for fine-tuning.

## Script to Dataset Generation Script

What `terraform_dataset_builder.py` script does:

- Defines your golden module standards (you can easily expand them). 
- Generates fake "bad" resource code snippets (simulates misaligned developer code).
- Generates corrected "good" module usage completions based on your standards.
- Packages prompt-completion pairs into a clean JSONL file.


## How to use it

1. Install the required libraries:
```bash
python3 -m venv .venv ; source .venv/bin/activate
pip install -r requirements.txt
```
2. Run the script:
```bash
python terraform_dataset_builder.py --output_dir ./data/ --num_samples 1000
```

3. Train the model:
```bash
python train.py --model_name_or_path ./data/ --output_dir ./output/ --num_train_epochs 3 --per_device_train_batch_size 4
```
4. Evaluate the model:
```bash
python evaluate.py --model_name_or_path ./output/ --output_dir ./evaluation/
```
5. Generate completions:
```bash
python generate.py --model_name_or_path ./output/ --output_dir ./generated/ --num_samples 10
```
6. Run the tests:
```bash
pytest tests/
```