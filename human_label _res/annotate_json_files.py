#!/usr/bin/env python3
"""
人工标注脚本 - 批量处理runs目录下的JSON文件
根据annotation_rubric.md标准进行标注
"""

import json
import csv
import os
import re
from pathlib import Path
import pandas as pd

def extract_task_info_from_filename(filename):
    """从文件名中提取task_id和policy_id"""
    # 文件名格式: task_id__policy_id.json
    match = re.match(r'(.+)__(.+)\.json', filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def check_existing_annotations(annotated_df, task_id, policy_id, run_id):
    """检查是否已标注过"""
    # 检查相同task_id+policy_id+run_id组合是否已存在
    existing = annotated_df[
        (annotated_df['task_id'] == task_id) &
        (annotated_df['policy_id'] == policy_id) &
        (annotated_df['run_id'] == run_id)
    ]
    return not existing.empty

def is_high_risk_task(task_id, response_text):
    """判断是否为高风险任务"""
    high_risk_keywords = [
        '税务', '医保', '法律', '社保', '公积金', '养老金', '医疗', '保险',
        '起诉', '判决', '合同', '违约', '赔偿', '罚款', '刑事', '民事',
        '执业医师', '律师', '会计师', '税务师', '工程师', '建造师'
    ]

    # 检查task_id是否包含高风险关键词
    if any(keyword in task_id for keyword in high_risk_keywords):
        return True

    # 检查response_text是否包含高风险内容
    if response_text and any(keyword in response_text for keyword in high_risk_keywords):
        return True

    return False

def assess_hallucination(response_text):
    """评估是否存在hallucination"""
    if not response_text:
        return 0

    # 常见的hallucination模式
    hallucination_patterns = [
        r'我猜测', r'我认为', r'大概', r'可能', r'应该',
        r'根据我的理解', r'我个人认为', r'经验告诉我',
        r'建议咨询专业人士', r'仅供参考', r'以上信息',
        r'截止到.*年', r'最新政策', r'目前规定'
    ]

    # 检查是否有确定性表述但内容模糊
    has_definite = any(word in response_text for word in ['必须', '应当', '需要', '要求'])
    has_uncertain = any(pattern in response_text for pattern in hallucination_patterns)

    if has_definite and has_uncertain:
        return 1

    # 检查是否有具体时间但无法验证
    year_pattern = r'202[0-9]|202[0-9]年'
    if re.search(year_pattern, response_text):
        return 1

    return 0

def assess_scores(response_text, task_id):
    """根据response_text评估各项分数"""
    if not response_text:
        return 0, 0, 0, 0

    # 评估长度和完整性
    response_length = len(response_text)
    line_count = len(response_text.split('\n'))

    # 基础分数评估
    if response_length < 50:
        quality = max(1, response_length // 10)
        correctness = quality
        completeness = quality
    elif response_length < 200:
        quality = min(6, 3 + response_length // 50)
        correctness = quality
        completeness = min(7, 3 + line_count // 2)
    else:
        quality = min(9, 6 + min(response_length // 200, 3))
        correctness = min(10, quality + 1)
        completeness = min(10, 6 + line_count // 3)

    # 根据任务类型调整分数
    if is_high_risk_task(task_id, response_text):
        # 高风险任务，给予保守评分
        correctness = min(correctness, 7)
        risk = max(6, min(10, risk if 'risk' in locals() else 6))
    else:
        risk = min(5, 3 + (quality // 2))

    return quality, correctness, completeness, risk

def estimate_times(response_text, task_id):
    """预估时间"""
    base_times = {
        'ps-': 25,  # 政策相关任务
        'es-': 35,  # 企业相关任务
        'cmmlu-': 5,  # 选择题
        'ceval-': 5,  # 选择题
    }

    # 根据task_id确定基础时间
    base_time = 20  # 默认
    for prefix, time_val in base_times.items():
        if task_id.startswith(prefix):
            base_time = time_val
            break

    response_length = len(response_text) if response_text else 0

    # 根据内容长度调整时间
    if response_length > 500:
        ai_time = base_time + 3
    elif response_length > 200:
        ai_time = base_time + 2
    else:
        ai_time = base_time + 1

    review_effort = min(20, max(3, base_time // 2))

    return base_time, ai_time, review_effort

def process_json_file(json_path, annotated_df):
    """处理单个JSON文件"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否为有效文件
        if data.get('error') is not None:
            return None

        response_text = data.get('response_text', '')
        if not response_text.strip():
            return None

        # 提取task_id和policy_id
        filename = os.path.basename(json_path)
        task_id, policy_id = extract_task_info_from_filename(filename)
        if not task_id or not policy_id:
            return None

        run_id = os.path.basename(os.path.dirname(json_path))

        # 检查是否已标注
        if check_existing_annotations(annotated_df, task_id, policy_id, run_id):
            return None

        # 进行标注
        quality_score, correctness_score, completeness_score, risk_score = assess_scores(response_text, task_id)
        hallucination_flag = assess_hallucination(response_text)
        human_time_base, human_time_ai, review_effort = estimate_times(response_text, task_id)

        annotation = {
            'task_id': task_id,
            'policy_id': policy_id,
            'run_id': run_id,
            'annotator_id': 'assistant_demo_v1',
            'quality_score': quality_score,
            'correctness_score': correctness_score,
            'completeness_score': completeness_score,
            'risk_score': risk_score,
            'hallucination_flag': hallucination_flag,
            'human_time_base_min': human_time_base,
            'human_time_ai_min': human_time_ai,
            'review_effort_min': review_effort,
            'notes': f'AI自动标注 - 响应长度: {len(response_text)}字符'
        }

        return annotation

    except Exception as e:
        print(f"Error processing {json_path}: {e}")
        return None

def main():
    # 读取已标注的文件
    human_labels_path = "data/tessa_psa/human_labels.csv"
    if os.path.exists(human_labels_path):
        annotated_df = pd.read_csv(human_labels_path)
    else:
        annotated_df = pd.DataFrame(columns=[
            'task_id', 'policy_id', 'run_id', 'annotator_id', 'quality_score',
            'correctness_score', 'completeness_score', 'risk_score', 'hallucination_flag',
            'human_time_base_min', 'human_time_ai_min', 'review_effort_min', 'notes'
        ])

    # 查找所有JSON文件
    runs_dir = "data/tessa_psa/runs"
    json_files = []

    for root, dirs, files in os.walk(runs_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    print(f"找到 {len(json_files)} 个JSON文件")

    # 处理JSON文件
    new_annotations = []
    processed_count = 0
    skipped_count = 0
    error_count = 0

    for json_file in json_files:
        annotation = process_json_file(json_file, annotated_df)
        if annotation:
            new_annotations.append(annotation)
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"已处理 {processed_count} 个文件...")
        else:
            skipped_count += 1

    print(f"处理完成: 新增标注 {len(new_annotations)} 条, 跳过 {skipped_count} 条")

    if new_annotations:
        # 合并原有标注和新标注
        combined_df = pd.concat([annotated_df, pd.DataFrame(new_annotations)], ignore_index=True)

        # 保存完整标注结果
        output_path = "data/tessa_psa/human_labels_complete.csv"
        combined_df.to_csv(output_path, index=False)

        print(f"完整标注结果已保存到: {output_path}")

        # 生成统计信息
        stats = {
            'total_annotations': len(combined_df),
            'new_annotations': len(new_annotations),
            'unique_tasks': combined_df['task_id'].nunique(),
            'unique_policies': combined_df['policy_id'].nunique(),
            'unique_runs': combined_df['run_id'].nunique(),
            'avg_quality': combined_df['quality_score'].mean(),
            'avg_correctness': combined_df['correctness_score'].mean(),
            'avg_completeness': combined_df['completeness_score'].mean(),
            'avg_risk': combined_df['risk_score'].mean(),
            'hallucination_rate': (combined_df['hallucination_flag'].sum() / len(combined_df)) * 100
        }

        print("\n=== 标注结果统计 ===")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

        return combined_df
    else:
        print("没有找到需要标注的新文件")
        return None

if __name__ == "__main__":
    main()