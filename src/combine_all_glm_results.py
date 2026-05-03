import csv
import json
import os
from pathlib import Path
import glob

def load_human_labels():
    """Load existing human labels."""
    file_path = "human_label _res/human_labels_complete_with_glm_v2.csv"
    if not os.path.exists(file_path):
        file_path = "human_label _res/human_labels_complete_with_glm.csv"
    if not os.path.exists(file_path):
        file_path = "human_label _res/human_labels_complete.csv"

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

def create_glm_human_label_entry(data, task_id, run_id):
    """Create a human label entry from GLM data."""
    # Read task info from task_bank.csv to fill in missing fields
    task_info = {}
    with open("data/tessa_psa/task_bank.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['task_id'] == task_id:
                task_info = row
                break

    # Determine model version
    model_type = "glm-4.7-flashx" if "flashx" in run_id else "glm-4.7"

    # Create entry matching the CSV format
    entry = {
        'task_id': task_id,
        'policy_id': 'pl_glm_47_flashx' if "flashx" in run_id else 'pl_glm_47',
        'run_id': run_id,
        'annotator_id': f'glm_{model_type.replace(".", "_")}_auto',
        'quality_score': '',  # Need manual review
        'correctness_score': '',  # Need manual review
        'completeness_score': '',  # Need manual review
        'risk_score': '',  # Need manual review
        'hallucination_flag': '',  # Need manual review
        'human_time_base_min': '',  # Fill from task_info if available
        'human_time_ai_min': '',  # Could estimate based on response length
        'review_effort_min': '',  # Estimate based on complexity
        'notes': f'GLM {model_type} auto-generated response. Latency: {data.get("latency_sec", 0):.2f}s. Response length: {len(data.get("response_text", ""))} chars. Run: {run_id}'
    }

    # Fill in task info if available
    if task_info:
        entry['sector'] = task_info.get('sector', '')
        entry['task_source'] = task_info.get('task_source', '')
        entry['task_text'] = task_info.get('task_text', '')
        entry['risk_class'] = task_info.get('risk_class', '')
        entry['difficulty_label'] = task_info.get('difficulty_label', '')

    return entry

def load_all_glm_results():
    """Load all successful GLM results from all runs."""
    results = []

    # Find all GLM batch directories
    batch_dirs = [
        "data/tessa_psa/runs/glm_batch",
        "data/tessa_psa/runs/glm_batch_v2",
        "data/tessa_psa/runs/glm_batch_v3",
        "data/tessa_psa/runs/glm_batch_v4"
    ]

    total_found = 0
    total_successful = 0

    for batch_dir in batch_dirs:
        batch_path = Path(batch_dir)
        if not batch_path.exists():
            print(f"Directory not found: {batch_dir}")
            continue

        # Find all JSON files
        json_files = list(batch_path.glob("*__pl_glm_47*.json"))
        print(f"\nFound {len(json_files)} files in {batch_dir}")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                total_found += 1

                # Skip failed results
                if data.get('error') or data.get('response_text') is None:
                    continue

                # Extract task_id and run_id from filename
                task_id = json_file.stem.split('__')[0]
                run_id = json_file.stem.split('__')[1].replace('pl_glm_47_', '')

                entry = create_glm_human_label_entry(data, task_id, f"glm_batch_{run_id}")
                results.append(entry)
                total_successful += 1

            except Exception as e:
                print(f"Error processing {json_file}: {e}")

    print(f"\nSummary:")
    print(f"Total JSON files found: {total_found}")
    print(f"Total successful GLM results: {total_successful}")

    return results

def main():
    print("Loading existing human labels...")
    existing_labels, fieldnames = load_human_labels()
    print(f"Found {len(existing_labels)} existing entries")

    print("Loading all GLM results...")
    glm_results = load_all_glm_results()

    if not glm_results:
        print("No successful GLM results found!")
        return

    # Count results by model type
    flashx_count = len([r for r in glm_results if 'flashx' in r.get('policy_id', '')])
    regular_count = len([r for r in glm_results if r.get('policy_id') == 'pl_glm_47'])

    print(f"\nGLM results by model:")
    print(f"glm-4.7 (regular): {regular_count}")
    print(f"glm-4.7-flashx: {flashx_count}")
    print(f"Total GLM results: {len(glm_results)}")

    # Combine existing with new GLM results
    all_entries = existing_labels + glm_results

    # Write combined file
    output_path = "human_label _res/human_labels_complete_all_glm.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        # Get all possible fieldnames
        all_fieldnames = set(fieldnames)
        for entry in all_entries:
            all_fieldnames.update(entry.keys())

        writer = csv.DictWriter(f, fieldnames=list(all_fieldnames))
        writer.writeheader()
        writer.writerows(all_entries)

    print(f"\nFinal result:")
    print(f"Wrote {len(all_entries)} total entries to {output_path}")

    # Show final statistics
    total_glm = len([r for r in all_entries if 'glm_batch' in r.get('run_id', '')])
    print(f"Total GLM entries in final file: {total_glm}")

if __name__ == "__main__":
    main()