import csv
import json
import os
import shutil
from pathlib import Path

def count_successful_results():
    """Count successful GLM results from all directories."""
    base_dir = Path("data/tessa_psa/runs")
    success_counts = {}
    file_details = []

    # Search all GLM batch directories
    for batch_dir in base_dir.glob("*glm_batch*"):
        if not batch_dir.is_dir():
            continue

        print(f"\nChecking directory: {batch_dir.name}")

        # Find all GLM JSON files
        json_files = list(batch_dir.glob("*__pl_glm_47*.json"))

        regular_count = 0
        flashx_count = 0
        successful_files = []

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if successful
                if data.get('error') is None and data.get('response_text') is not None:
                    task_id = json_file.stem.split('__')[0]
                    model_type = "regular" if "pl_glm_47" in json_file.name and "flashx" not in json_file.name else "flashx"

                    successful_files.append({
                        'file': json_file.name,
                        'task_id': task_id,
                        'model': model_type,
                        'latency': data.get('latency_sec', 0),
                        'response_length': len(data.get('response_text', ''))
                    })

                    if model_type == "regular":
                        regular_count += 1
                    else:
                        flashx_count += 1

            except Exception as e:
                print(f"Error reading {json_file}: {e}")

        success_counts[batch_dir.name] = {
            'regular': regular_count,
            'flashx': flashx_count,
            'total': regular_count + flashx_count
        }

        print(f"  Regular: {regular_count}")
        print(f"  Flashx: {flashx_count}")
        print(f"  Total: {regular_count + flashx_count}")

        file_details.extend(successful_files)

    # Overall summary
    total_regular = sum(d['regular'] for d in success_counts.values())
    total_flashx = sum(d['flashx'] for d in success_counts.values())
    total_all = total_regular + total_flashx

    print(f"\n=== SUMMARY ===")
    print(f"Total regular glm-4.7: {total_regular}")
    print(f"Total flashx glm-4.7-flashx: {total_flashx}")
    print(f"Total GLM results: {total_all}")
    print(f"DS target: 600")
    print(f"Needed: {max(0, 600 - total_all)} more")
    print(f"Ratio (regular/flashx): {total_regular}/{total_flashx}")

    return file_details, success_counts

def create_final_csv():
    """Create a final CSV with all successful GLM results."""
    file_details, success_counts = count_successful_results()

    # Load task bank for task details
    task_info = {}
    with open("data/tessa_psa/task_bank.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_info[row['task_id']] = row

    # Prepare entries
    entries = []
    for detail in file_details:
        task_id = detail['task_id']
        task_data = task_info.get(task_id, {})

        entry = {
            'task_id': task_id,
            'policy_id': 'pl_glm_47' if detail['model'] == 'regular' else 'pl_glm_47_flashx',
            'run_id': 'glm_final',
            'annotator_id': f'glm_{detail["model"]}_auto',
            'quality_score': '',
            'correctness_score': '',
            'completeness_score': '',
            'risk_score': '',
            'hallucination_flag': '',
            'human_time_base_min': '',
            'human_time_ai_min': '',
            'review_effort_min': '',
            'notes': f'GLM {detail["model"]} response. Latency: {detail["latency"]:.2f}s. Response length: {detail["response_length"]} chars.'
        }

        # Add task details
        entry['sector'] = task_data.get('sector', '')
        entry['task_source'] = task_data.get('task_source', '')
        entry['task_text'] = task_data.get('task_text', '')
        entry['risk_class'] = task_data.get('risk_class', '')
        entry['difficulty_label'] = task_data.get('difficulty_label', '')

        entries.append(entry)

    # Write final CSV
    output_path = "human_label _res/glm_results_final.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if entries:
            fieldnames = entries[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)

    print(f"\nFinal CSV written: {output_path}")
    print(f"Total entries: {len(entries)}")

    return entries

if __name__ == "__main__":
    create_final_csv()