import csv
import json
import os
from pathlib import Path

# Set paths
DATA_DIR = Path("data/tessa_psa")
RUNS_DIR_V2 = DATA_DIR / "runs" / "glm_batch_v2"
HUMAN_LABELS_DIR = Path("human_label _res")

def load_human_labels():
    """Load existing human labels."""
    file_path = HUMAN_LABELS_DIR / "human_labels_complete_with_glm.csv"
    if not file_path.exists():
        file_path = HUMAN_LABELS_DIR / "human_labels_complete.csv"

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

def create_glm_human_label_entry(data, task_id):
    """Create a human label entry from GLM data."""
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
        'run_id': 'glm_batch_v2',
        'annotator_id': 'glm_4.7_flashx_auto_v2',
        'quality_score': '',  # Need manual review
        'correctness_score': '',  # Need manual review
        'completeness_score': '',  # Need manual review
        'risk_score': '',  # Need manual review
        'hallucination_flag': '',  # Need manual review
        'human_time_base_min': '',  # Fill from task_info if available
        'human_time_ai_min': '',  # Could estimate based on response length
        'review_effort_min': '',  # Estimate based on complexity
        'notes': f'GLM-4.7-flashx v2 auto-generated response. Latency: {data.get("latency_sec", 0):.2f}s. Response length: {len(data.get("response_text", ""))} chars.'
    }

    # Fill in task info if available
    if task_info:
        entry['sector'] = task_info.get('sector', '')
        entry['task_source'] = task_info.get('task_source', '')
        entry['task_text'] = task_info.get('task_text', '')
        entry['risk_class'] = task_info.get('risk_class', '')
        entry['difficulty_label'] = task_info.get('difficulty_label', '')

    return entry

def load_glm_v2_results():
    """Load successful GLM results from v2 JSON files."""
    results = []
    json_files = list(RUNS_DIR_V2.glob("*__pl_glm_47_flashx.json"))

    print(f"Found {len(json_files)} v2 files")

    successful_count = 0
    for i, json_file in enumerate(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Skip failed results
            if data.get('error') or data.get('response_text') is None:
                continue

            task_id = json_file.stem.split('__')[0]
            entry = create_glm_human_label_entry(data, task_id)
            results.append(entry)
            successful_count += 1

            if i < 5 or i % 10 == 0:  # Show progress for first 5 and every 10th
                print(f"Added successful result for {task_id}")

        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    print(f"Found {successful_count} successful GLM v2 results")
    return results

def main():
    print("Loading existing human labels...")
    existing_labels, fieldnames = load_human_labels()
    print(f"Found {len(existing_labels)} existing entries")

    print("Loading GLM v2 results...")
    glm_results = load_glm_v2_results()

    if not glm_results:
        print("No successful GLM v2 results found!")
        return

    # Combine existing with new GLM results
    all_entries = existing_labels + glm_results

    # Write combined file
    output_path = HUMAN_LABELS_DIR / "human_labels_complete_with_glm_v2.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        # Get all possible fieldnames
        all_fieldnames = set(fieldnames)
        for entry in all_entries:
            all_fieldnames.update(entry.keys())

        writer = csv.DictWriter(f, fieldnames=list(all_fieldnames))
        writer.writeheader()
        writer.writerows(all_entries)

    print(f"Wrote {len(all_entries)} entries to {output_path}")

    # Show some statistics
    glm_count = len([r for r in all_entries if r.get('run_id') == 'glm_batch_v2'])
    print(f"GLM v2 entries added: {glm_count}")

if __name__ == "__main__":
    main()