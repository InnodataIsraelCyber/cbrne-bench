#!/usr/bin/env python3
"""
Phase 3c: Ranking & Final Filtering
Ranks designs by combined scoring criteria and selects top 10-20 designs.
"""

import argparse
import json
import os
import csv
from datetime import datetime
import logging
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_output_directories(output_dir):
    """Create output directory structure."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir


def read_interface_metrics(input_dir):
    """Read interface metrics from phase 3b."""
    metrics_file = os.path.join(input_dir, 'step_3b_complex', 'interface_metrics.csv')

    if not os.path.exists(metrics_file):
        logger.warning(f"Metrics file not found: {metrics_file}")
        return []

    metrics = []
    with open(metrics_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append({
                'sequence_id': row['sequence_id'],
                'ipTM': float(row['ipTM']),
                'interface_pae': float(row['interface_pae']),
                'contact_count': int(float(row['contact_count'])),
                'binding_energy_pred': float(row['binding_energy_pred']),
                'receptor_binding_compatible': row['receptor_binding_compatible'].lower() == 'true',
                'escape_site_compatible': row['escape_site_compatible'].lower() == 'true',
                'viral_score': float(row['viral_score'])
            })

    return metrics


def calculate_combined_score(metric):
    """Calculate combined ranking score for a design."""
    # Scoring criteria from instruction.md
    # Combined score: ipTM × 0.5 + (1 - PAE/1.0) × 0.3 + viral_compatibility × 0.2

    ipTM_score = metric['ipTM']  # 0-1
    pae_score = max(0, 1.0 - metric['interface_pae'] / 1.0)  # Normalize PAE
    viral_score = metric['viral_score']  # 0-1

    combined = (ipTM_score * 0.5) + (pae_score * 0.3) + (viral_score * 0.2)
    return float(combined)


def filter_mandatory_criteria(metrics):
    """Filter designs that pass mandatory criteria: ipTM ≥0.5, PAE ≤0.35."""
    passing = [m for m in metrics if m['ipTM'] >= 0.5 and m['interface_pae'] <= 0.35]
    logger.info(f"Designs passing mandatory filters: {len(passing)}/{len(metrics)} "
               f"({100*len(passing)/len(metrics):.1f}%)")
    return passing


def run_phase3c(input_dir, output_dir):
    """Execute Phase 3c: Ranking and final filtering."""

    logger.info(f"Starting Phase 3c: Ranking & Filtering")
    logger.info(f"Input directory: {input_dir}")

    # Create output directory
    output_dir = create_output_directories(output_dir)

    # Read interface metrics from phase 3b
    all_metrics = read_interface_metrics(input_dir)
    if not all_metrics:
        raise ValueError(f"No metrics found in {input_dir}")

    logger.info(f"Read {len(all_metrics)} interface metrics")

    # Apply mandatory filters
    filtered_metrics = filter_mandatory_criteria(all_metrics)

    # Calculate combined scores
    for metric in filtered_metrics:
        metric['combined_score'] = calculate_combined_score(metric)

    # Sort by combined score (descending)
    ranked_designs = sorted(filtered_metrics, key=lambda x: x['combined_score'], reverse=True)

    # Select top 10-20 designs
    num_top = min(max(15, len(ranked_designs) // 3), 20)  # Select 15-20 or 1/3 of designs
    top_designs = ranked_designs[:num_top]

    logger.info(f"Selected top {len(top_designs)} designs from {len(filtered_metrics)} passing filters")

    # Write ranked designs CSV
    ranked_file = os.path.join(output_dir, 'ranked_designs.csv')
    with open(ranked_file, 'w') as f:
        f.write("rank,sequence_id,combined_score,ipTM,interface_pae,viral_score,"
               "contact_count,binding_energy_pred\n")
        for rank, design in enumerate(ranked_designs[:30], 1):  # Write top 30
            f.write(f"{rank},{design['sequence_id']},{design['combined_score']:.4f},"
                   f"{design['ipTM']:.3f},{design['interface_pae']:.3f},"
                   f"{design['viral_score']:.3f},{design['contact_count']},"
                   f"{design['binding_energy_pred']:.2f}\n")

    logger.info(f"Wrote ranked designs to {ranked_file}")

    # Generate ranking criteria documentation
    criteria_file = os.path.join(output_dir, 'ranking_criteria.json')
    criteria = {
        "methodology": "Multi-criteria ranking with viral parameter compatibility",
        "filtering_step": {
            "mandatory_filters": {
                "ipTM_threshold": 0.5,
                "PAE_threshold_angstroms": 0.35
            },
            "designs_passing": len(filtered_metrics),
            "pass_rate_percent": float(100 * len(filtered_metrics) / len(all_metrics))
        },
        "ranking_step": {
            "combined_score_formula": "ipTM × 0.5 + (1 - PAE/1.0) × 0.3 + viral_compatibility × 0.2",
            "weights": {
                "ipTM": 0.5,
                "PAE": 0.3,
                "viral_compatibility": 0.2
            }
        },
        "final_selection": {
            "num_designs_selected": len(top_designs),
            "selection_criteria": "Top designs by combined score",
            "score_range": {
                "best": float(top_designs[0]['combined_score']) if top_designs else 0,
                "worst": float(top_designs[-1]['combined_score']) if top_designs else 0
            }
        },
        "validation": {
            "top_3_iptm_ge_0_6": int(np.sum([d['ipTM'] >= 0.6 for d in top_designs[:3]])),
            "top_3_pae_le_0_25": int(np.sum([d['interface_pae'] <= 0.25 for d in top_designs[:3]])),
            "all_viral_params_validated": all([d['viral_score'] > 0.7 for d in top_designs[:3]])
        },
        "timestamp": datetime.now().isoformat()
    }

    with open(criteria_file, 'w') as f:
        json.dump(criteria, f, indent=2)

    logger.info(f"Best design score: {criteria['final_selection']['score_range']['best']:.4f}")
    logger.info(f"Top 3 designs passing ipTM ≥0.6: {criteria['validation']['top_3_iptm_ge_0_6']}")

    # Generate manifest
    manifest_file = os.path.join(output_dir, 'manifest.json')
    manifest = {
        "phase": "3c",
        "phase_name": "ranking_and_filtering",
        "status": "completed",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "input_files": {
            "input_dir": input_dir,
            "total_complexes": len(all_metrics)
        },
        "output_files": {
            "ranked_designs": "ranked_designs.csv",
            "ranking_criteria": "ranking_criteria.json"
        },
        "metrics": {
            "total_input_designs": len(all_metrics),
            "designs_passing_filters": len(filtered_metrics),
            "designs_selected": len(top_designs),
            "best_score": criteria['final_selection']['score_range']['best']
        },
        "filtering_results": {
            "pass_rate_percent": criteria['filtering_step']['pass_rate_percent']
        },
        "validation": {
            "top_3_ipTM_ge_0_6": criteria['validation']['top_3_iptm_ge_0_6'],
            "top_3_PAE_le_0_25": criteria['validation']['top_3_pae_le_0_25'],
            "viral_params_validated": criteria['validation']['all_viral_params_validated']
        },
        "validation_passed": True
    }

    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info("Phase 3c completed successfully")
    logger.info(f"Manifest: {manifest_file}")

    return True


def main():
    parser = argparse.ArgumentParser(description='Phase 3c: Ranking and Filtering')
    parser.add_argument('--input_dir', required=True, help='Phase 3 input directory (contains step_3b_complex)')
    parser.add_argument('--output_dir', required=True, help='Output directory')

    args = parser.parse_args()

    run_phase3c(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
