import csv
import json
import os
from pathlib import Path

REPO_ROOT = Path(".")
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"
RUNS_DIR = DATA_DIR / "runs" / "glm_batch"
HUMAN_LABELS_DIR = REPO_ROOT / "human_label _res"

def load_human_labels():
    """Load existing human labels."""
    file_path = "human_label _res/human_labels_complete.csv"
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

def create_glm_human_label_entry(data):
    """Create a human label entry from GLM data."""
    task_id = data['task_id']

    # Read task info from task_bank.csv to fill in missing fields
    task_info = {}
    with open(DATA_DIR / "task_bank.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['task_id'] == task_id:
                task_info = row
                break

    # Create entry matching the CSV format
    entry = {
        'task_id': task_id,
        'policy_id': 'pl_glm_47_flashx',
        'run_id': 'glm_batch',
        'annotator_id': 'glm_4.7_flashx_auto',
        'quality_score': '',  # Need manual review
        'correctness_score': '',  # Need manual review
        'completeness_score': '',  # Need manual review
        'risk_score': '',  # Need manual review
        'hallucination_flag': '',  # Need manual review
        'human_time_base_min': '',  # Fill from task_info if available
        'human_time_ai_min': '',  # Could estimate based on response length
        'review_effort_min': '',  # Estimate based on complexity
        'notes': f'GLM-4.7-flashx auto-generated response. Latency: {data.get("latency_sec", 0):.2f}s. Response length: {len(data.get("response_text", ""))} chars.'
    }

    # Fill in task info if available
    if task_info:
        entry['sector'] = task_info.get('sector', '')
        entry['task_source'] = task_info.get('task_source', '')
        entry['task_text'] = task_info.get('task_text', '')
        entry['risk_class'] = task_info.get('risk_class', '')
        entry['difficulty_label'] = task_info.get('difficulty_label', '')

    return entry

def load_glm_results():
    """Load successful GLM results from JSON files."""
    results = []
    json_files = list(RUNS_DIR.glob("*__pl_glm_47_flashx.json"))
    print(f"Found {len(json_files)} flashx files in {RUNS_DIR}")
    if len(json_files) == 0:
        print("No files found! Listing directory contents:")
        print(os.listdir(RUNS_DIR))

    for i, json_file in enumerate(json_files):
        if i < 3:  # Debug first 3 files
            print(f"Checking {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if i < 3:
                    print(f"Error: {data.get('error')}")
                    print(f"Response text exists: {data.get('response_text') is not None}")
                    print(f"Response text length: {len(data.get('response_text', ''))}")

                # Skip failed results
                if data.get('error') or data.get('response_text') is None:
                    continue

                entry = create_glm_human_label_entry(data)
                results.append(entry)
                if i < 3:
                    print(f"Added successful result for {data['task_id']}")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    return results

def main():
    print("Loading existing human labels...")
    existing_labels, fieldnames = load_human_labels()
    print(f"Found {len(existing_labels)} existing entries")

    print("Loading GLM results...")
    glm_results = load_glm_results()
    print(f"Found {len(glm_results)} successful GLM results")

    if not glm_results:
        print("No successful GLM results found!")
        return

    # Combine existing with new GLM results
    all_entries = existing_labels + glm_results

    # Write combined file
    output_path = HUMAN_LABELS_DIR / "human_labels_complete_with_glm.csv"
    # Write combined file
    output_path = HUMAN_LABELS_DIR / "human_labels_complete_with_glm.csv"

    # Get all possible fieldnames
    all_fieldnames = set(fieldnames)
    for entry in all_entries:
        all_fieldnames.update(entry.keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_fieldnames)
        writer.writeheader()
        writer.writerows(all_entries)

    print(f"Wrote {len(all_entries)} entries to {output_path}")

    # Show some statistics
    glm_count = len([r for r in all_entries if r.get('model') == 'glm-4.7-flashx'])
    print(f"GLM entries added: {glm_count}")

if __name__ == "__main__":
    main()