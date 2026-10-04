#!/usr/bin/env python3
"""Per-protein replicate consistency within each group."""

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path


def consistency(values):
    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    if mean_value <= 0:
        return None
    variance = sum((v - mean_value) ** 2 for v in values) / (len(values) - 1)
    cv = math.sqrt(variance) / mean_value
    return 1.0 / (1.0 + cv)


def main():
    parser = argparse.ArgumentParser(description="Per-protein replicate reproducibility score")
    parser.add_argument("--abundance_long_file", required=True)
    parser.add_argument("--samples_file", required=True)
    parser.add_argument("--output_folder", required=True)
    args = parser.parse_args()

    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # @step: Loading samples and abundance data
    group_by_sample = {}
    with open(args.samples_file) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            group_by_sample[row["sample"]] = row["group"]

    values_by_protein = defaultdict(lambda: defaultdict(list))
    gene_by_protein = {}
    with open(args.abundance_long_file) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            group = group_by_sample.get(row["sample"])
            if group is None:
                continue
            values_by_protein[row["protein"]][group].append(float(row["value"]))
            gene_by_protein[row["protein"]] = row["gene"]

    # @step: Scoring replicate consistency per protein
    rows = []
    for protein, by_group in values_by_protein.items():
        ip_consistency = consistency(by_group.get("ip", []))
        wcl_consistency = consistency(by_group.get("wcl", []))
        group_scores = [s for s in (ip_consistency, wcl_consistency) if s is not None]
        if not group_scores:
            continue
        value = sum(group_scores) / len(group_scores)
        rows.append({
            "protein": protein,
            "gene": gene_by_protein[protein],
            "reproducibility": value,
            "ip_consistency": ip_consistency if ip_consistency is not None else "",
            "wcl_consistency": wcl_consistency if wcl_consistency is not None else "",
        })

    with open(output_folder / "reproducibility.tsv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["protein", "gene", "reproducibility", "ip_consistency", "wcl_consistency"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} reproducibility scores", file=sys.stderr)

    # @step: Reproducibility scoring complete
    print("Reproducibility scoring complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
