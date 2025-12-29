from dataclasses import dataclass

from matplotlib.lines import Line2D
@dataclass
class Example:
    path: str
    name: str
    expected_safety: bool
    tags: list[str] = None
    loc: int = None
# Path configurations
path_to_whilestar = "../whilestar"
wvm_gradle = f"{path_to_whilestar}/gradlew"
mode = "-k"
path_to_examples = f"{path_to_whilestar}/examples"
example = f"{path_to_examples}/array/ex1.w"

# Get LOCs per example
with open(f"examples-list-all.txt", "r") as file:
    locs_per_example = {}
    for line in file:
        line = line.strip()
        split = line.split(" ")
        with open(f"{path_to_examples}/{split[0]}", "r") as example_file:
            locs_per_example[f"{split[1]}-{split[2].lower() == "true"}"] = len(example_file.readlines())

# Get examples with if:
# with open(f"examples-list-all.txt", "r") as file:
#     for line in file:
#         line = line.strip()
#         split = line.split(" ")
#         with open(f"{path_to_examples}/{split[0]}", "r") as example_file:
#             lines = example_file.readlines()
#             for l in lines:
#                 if "if" in l:
#                     print(f"Example {split[1]} has an if statement.")
#                     break

# Get relevant numbers from ground truth data
tags_per_example = {}
with open("examples-list-all.txt", "r") as f:
    lines = f.readlines()
    total_examples = 0
    safe_examples = 0
    unsafe_examples = 0
    pointer_examples = 0
    array_examples = 0
    array_or_pointer_examples = 0
    loop_examples = 0
    if_examples = 0
    for line in lines:
        total_examples += 1
        safe = line.strip().split(" ")[2].lower()
        if safe == "true":
            safe_examples += 1
        elif safe == "false":
            unsafe_examples += 1
        split = line.strip().split(" ")
        tags = split[3].split(",") if len(split) > 3 else []
        tags_per_example[f"{split[1]}-{True if safe == "true" else False}"] = tags
        if "array" in tags:
            array_examples += 1
        if "pointer" in tags:
            pointer_examples += 1
        if "array" in tags or "pointer" in tags:
            array_or_pointer_examples += 1
        if "loop" in tags:
            loop_examples += 1
        if "if" in tags:
            if_examples += 1

print(f"Total examples: {total_examples}, Safe: {safe_examples}, Unsafe: {unsafe_examples}, Arrays: {array_examples}, Pointers: {pointer_examples}, Arrays or Pointers: {array_or_pointer_examples}, Loops: {loop_examples}, Ifs: {if_examples}")

# Read results and aggregate them
import csv

aggregated_results = {}
repititions = 5
with open("benchmark-results.csv", "r") as csvfile, open("benchmark-results-new-tags.csv", "w", newline='') as outfile:
    reader = csv.DictReader(csvfile)
    all_results = [row for row in reader]
    i = 0
    writer = csv.DictWriter(outfile, fieldnames=all_results[0].keys())
    writer.writeheader()
    while i < len(all_results):
        block = all_results[i:i+repititions]
        example_name = block[0]['Example']
        mode = block[0]['Mode']
        if block[0]['Safe'] != block[1]['Safe'] \
            or block[0]['Safe'] != block[2]['Safe'] \
            or block[0]['Safe'] != block[3]['Safe'] \
            or block[0]['Safe'] != block[4]['Safe']:
            print(f"Warning: Inconsistent results for {example_name} in mode {mode}")
            if block[0]['Safe'] != "OUTOFMEMORY" and block[0]['Safe'] != "TIMEOUT":
                exit(1)
            if block[0]['Safe'] != "OUTOFMEMORY" \
                and (block[1]['Safe'] == "OUTOFMEMORY" or block[2]['Safe'] == "OUTOFMEMORY" \
                  or block[3]['Safe'] == "OUTOFMEMORY" or block[4]['Safe'] == "OUTOFMEMORY"):
                block[0]['Safe'] = "OUTOFMEMORY"
                print(f"Info: Setting result for {example_name} in mode {mode} to OUTOFMEMORY because one of the runs resulted in OOM.")
        safe = block[0]['Safe']
        user_times = [float(row['UserTimeSec']) for row in block]
        system_times = [float(row['SystemTimeSec']) for row in block]
        cpu_percents = [int(row['CPUPercent']) for row in block]
        elapsed_times = [float(row['ElapsedTime']) for row in block]
        max_memories = [int(row['MaxMemoryKB']) for row in block]
        tags = block[0]['Tags']
        tags = tags_per_example.get(example_name, [])
        block[0]['Tags'] = " ".join(tags)
        block[1]['Tags'] = " ".join(tags)
        block[2]['Tags'] = " ".join(tags)
        block[3]['Tags'] = " ".join(tags)
        block[4]['Tags'] = " ".join(tags)
        if block[0]['Classification'] != block[1]['Classification'] \
            or block[0]['Classification'] != block[2]['Classification'] \
            or block[0]['Classification'] != block[3]['Classification'] \
            or block[0]['Classification'] != block[4]['Classification']:
            print(f"Warning: Inconsistent classification for {example_name} in mode {mode}")
        classification = block[0]['Classification']
        ground_truth = block[0]['Ground Truth']
        num_smt_calls = [int(row['NumberOfSMTCalls']) if row['NumberOfSMTCalls'].isnumeric() else 0 for row in block]
        aggregated_results[(example_name, mode)] = {
            'Safe': safe,
            'AvgUserTimeSec': sum(user_times) / repititions,
            'AvgSystemTimeSec': sum(system_times) / repititions,
            'AvgCPUPercent': sum(cpu_percents) / repititions,
            'AvgElapsedTime': sum(elapsed_times) / repititions,
            'StdElapsedTime': () if repititions < 2 else (sum((x - (sum(elapsed_times) / repititions)) ** 2 for x in elapsed_times) / (repititions - 1)) ** 0.5,
            'AvgMaxMemoryKB': sum(max_memories) / repititions,
            'StdMaxMemoryKB': () if repititions < 2 else (sum((x - (sum(max_memories) / repititions)) ** 2 for x in max_memories) / (repititions - 1)) ** 0.5,
            'AvgNumSMTCalls': sum(num_smt_calls) / repititions,
            'Classification': classification,
            'Ground Truth': ground_truth,
            'Tags': " ".join(tags)
        }
        i += repititions
    # Write results with changed tags to new file:
        
        for row in block:
            writer.writerow(row)

with open("aggregated-results.csv", "w", newline='') as csvfile:
    fieldnames = ['Example', 'Mode', 'Safe', 'AvgUserTimeSec', 'AvgSystemTimeSec', 'AvgCPUPercent', 'AvgElapsedTime', 'StdElapsedTime', 'AvgMaxMemoryKB', 'StdMaxMemoryKB', 'AvgNumSMTCalls', 'Classification', 'Ground Truth', 'Tags']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for (example_name, mode) in aggregated_results:
        row = {'Example': example_name, 'Mode': mode}
        row.update(aggregated_results[(example_name, mode)])
        writer.writerow(row)

# Calculate Classification metrics
counts = {
    "BMC": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "KInd": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "KInd (Inv)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "BMC+KInd": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "BMC+KInd (Inv)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "WPC": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (ATS)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (ATS+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (SMI)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (SMI+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (SMI+ATS)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
    "GPDR (SMI+ATS+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "OOM":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0, "TSec":0, "TInsec":0, "TInsecSOAP":0, "FSec":0, "FInsec":0, "FInsecSOAP":0},
}
approach_mapping = {
    "-b": "BMC",
    "-k": "KInd",
    "-k --kInd-inv": "KInd (Inv)",
    "-bk": "BMC+KInd",
    "-bk --kInd-inv": "BMC+KInd (Inv)",
    "-p": "WPC",
    "-g": "GPDR",
    "-gB": "GPDR (B-Eval)",
    "-g --gpdr-ats": "GPDR (ATS)",
    "-gB --gpdr-ats": "GPDR (ATS+B-Eval)",
    "-g --gpdr-smi": "GPDR (SMI)",
    "-gB --gpdr-smi": "GPDR (SMI+B-Eval)",
    "-g --gpdr-smi --gpdr-ats": "GPDR (SMI+ATS)",
    "-gB --gpdr-smi --gpdr-ats": "GPDR (SMI+ATS+B-Eval)",       
}
classification_labels = {
    "True Positive": "TP",
    'True\xa0Positive': "TP",
    "True Negative": "TN",
    'True\xa0Negative': "TN",
    "False Positive": "FP",
    'False\xa0Positive': "FP",
    "False Negative": "FN",
    'False\xa0Negative': "FN",
}
tool_labels = {
    "bmc": "BMC",
    "kInd": "KInd",
    "kInd_inv": "KInd (Inv)",
    "bmc_kInd": "BMC+KInd",
    "bmc_kInd_inv": "BMC+KInd (Inv)",
    "wpc": "WPC",
    "gpdr": "GPDR",
    "gpdr_boolEval": "GPDR (B-Eval)",
    "gpdr_ats": "GPDR (ATS)",
    "gpdr_ats_boolEval": "GPDR (ATS+B-Eval)",
    "gpdr_smi": "GPDR (SMI)",
    "gpdr_smi_boolEval": "GPDR (SMI+B-Eval)",
    "gpdr_smi_ats": "GPDR (SMI+ATS)",
    "gpdr_smi_ats_boolEval": "GPDR (SMI+ATS+B-Eval)",
}
a = b = 0
for (ex1, m1) in aggregated_results:
    if m1 != "-gB":
        continue
    for (ex2, m2) in aggregated_results:
        if m2 != "-gB --gpdr-smi":
            continue
        if ex1 == ex2:
            if aggregated_results[(ex1, m1)]['Safe'] != aggregated_results[(ex2, m2)]['Safe']:
                pass
                #print(f"Warning: Different results for {ex1} in modes {m1} and {m2}: {aggregated_results[(ex1, m1)]['Safe']} vs. {aggregated_results[(ex2, m2)]['Safe']}")
            if (aggregated_results[(ex1, m1)]['Safe'] == "Proof" and aggregated_results[(ex2, m2)]['Safe'] == "Proof") or ( \
                aggregated_results[(ex1, m1)]['Safe'] == "Counterexample" and aggregated_results[(ex2, m2)]['Safe'] == "Counterexample" \
            ):
                #print("Proof for both.")
                if aggregated_results[(ex1, m1)]['AvgElapsedTime'] > aggregated_results[(ex2, m2)]['AvgElapsedTime']:
                    #print(f"without SMI slower: {aggregated_results[(ex1, m1)]['AvgElapsedTime']}s vs. {aggregated_results[(ex2, m2)]['AvgElapsedTime']}s")
                    a += 1
                else:
                    b += 1
print(f"SMI faster in {a} cases, without SMI faster in {b} cases.")

for (ex, m) in aggregated_results:
    if m == "-k":
        if aggregated_results[(ex, m)]['Safe'] == "NoResult":
            print(f"Warning: NoResult for {ex} in mode {m} --> TODO: Why?")
    #if aggregated_results[(ex, m)]['Safe'] == "OUTOFMEMORY":
    #    print(f"Warning: OOM for {ex} in mode {m} --> Max memory: {aggregated_results[(ex, m)]['AvgMaxMemoryKB'] / 1000} MB")
    #if aggregated_results[(ex, m)]['Safe'] == "TIMEOUT":
    #    if m in ["-b", "-k", "-bk", "-k --kInd-inv", "-bk --kInd-inv"]:
    #        print(f"Warning: TIMEOUT for {ex} in mode {m} --> Elapsed time: {aggregated_results[(ex, m)]['AvgElapsedTime']} seconds")
    if m == "-g":
        if aggregated_results[(ex, m)]['Safe'] == "Proof" or aggregated_results[(ex, m)]['Safe'] == "Counterexample":
            print(f"--Warning: Result {aggregated_results[(ex, m)]['Safe']} for {ex} in mode {m} --> TODO: Why?")
for (example_name, mode) in aggregated_results:
    if mode == "--warmup":
        continue
    if True: #aggregated_results[(example_name, mode)]['Classification'] == "":
        if aggregated_results[(example_name, mode)]['Safe'] == "Proof":
            counts[approach_mapping[mode]]["Proof"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["Counterexample"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Crash" \
            or aggregated_results[(example_name, mode)]['Safe'] == "ERROR":  # Caught by approaches vs. not caught
            counts[approach_mapping[mode]]["Crash"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY":
            counts[approach_mapping[mode]]["OOM"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "NoResult":
            counts[approach_mapping[mode]]["NoResult"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "TIMEOUT":
            counts[approach_mapping[mode]]["Timeout"] += 1
        else:
            # print(f"Warning: Unknown classification for {example_name} in mode {mode}. Interpret as Crash.")
            counts[approach_mapping[mode]]["Crash"] += 1
    if aggregated_results[(example_name, mode)]['Ground Truth'] == "True":
        if aggregated_results[(example_name, mode)]['Safe'] == "Proof":
            counts[approach_mapping[mode]]["TPsafe"] += 1
            counts[approach_mapping[mode]]["TNunsafe"] += 1
            counts[approach_mapping[mode]]["TSec"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["FNsafe"] += 1
            counts[approach_mapping[mode]]["FPunsafe"] += 1
            counts[approach_mapping[mode]]["FInsec"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] != "Proof" \
            and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample":
            counts[approach_mapping[mode]]["FNsafe"] += 1
            counts[approach_mapping[mode]]["FInsec"] += 1
            counts[approach_mapping[mode]]["FInsecSOAP"] += 1
    elif aggregated_results[(example_name, mode)]['Ground Truth'] == "False":
        if aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["TNsafe"] += 1
            counts[approach_mapping[mode]]["TPunsafe"] += 1
            counts[approach_mapping[mode]]["TInsec"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Proof":
            counts[approach_mapping[mode]]["FPsafe"] += 1
            counts[approach_mapping[mode]]["FNunsafe"] += 1
            counts[approach_mapping[mode]]["FSec"] += 1
            if mode == "-p":
                print(f"Warning: False Proof for {example_name} in mode {mode} --> TODO: Why?")
        elif aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" \
            and aggregated_results[(example_name, mode)]['Safe'] != "Proof":
            counts[approach_mapping[mode]]["FNunsafe"] += 1
            counts[approach_mapping[mode]]["TInsec"] += 1
            counts[approach_mapping[mode]]["TInsecSOAP"] += 1
    else:
        print(f"Warning: Unknown classification for {example_name} in mode {mode}")

# Plot -----------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
import matplot2tikz

def results_by_approach_for_metric(aggregated_results, metric, complexity = False):
    bmc_results = {}
    kInd_results = {}
    kInd_inv_results = {}
    bmc_kInd_results = {}
    bmc_kInd_inv_results = {}
    wpc_results = {}
    gpdr_results = {}
    gpdr_boolEval_results = {}
    gpdr_ats_results = {}
    gpdr_ats_boolEval_results = {}
    gpdr_smi_results = {}
    gpdr_smi_boolEval_results = {}
    gpdr_smi_ats_results = {}
    gpdr_smi_ats_boolEval_results = {}
    for (example_name, mode) in aggregated_results:
        #if aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY":
        #    print(f"OOM for example {example_name} in mode {mode}. Max memory: {aggregated_results[(example_name, mode)]['AvgMaxMemoryKB'] / 1000} MB")
        if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
            continue
        #if aggregated_results[(example_name, mode)]['Safe'] == "TIMEOUT": # or aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY"):
        #    continue
        if mode == "-b":
            bmc_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-k":
            kInd_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-k --kInd-inv":
            kInd_inv_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == '-p':
            wpc_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-bk":
            bmc_kInd_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-bk --kInd-inv":
            bmc_kInd_inv_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-g":
            gpdr_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-gB":
            gpdr_boolEval_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-g --gpdr-ats":
            gpdr_ats_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-gB --gpdr-ats":
            gpdr_ats_boolEval_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-g --gpdr-smi":
            gpdr_smi_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-gB --gpdr-smi":
            gpdr_smi_boolEval_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-g --gpdr-smi --gpdr-ats":
            gpdr_smi_ats_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-gB --gpdr-smi --gpdr-ats":
            gpdr_smi_ats_boolEval_results[example_name] = aggregated_results[(example_name, mode)][metric]

    print_plot_data = False
    if print_plot_data: # and metric == "AvgElapsedTime":
        results = gpdr_ats_boolEval_results
        approach = "-gB --gpdr-ats"
        data = sorted(results, key = results.get)
        for i, res in enumerate(data):
            print(f"result {i}: {results[res]:.2f} seconds/calls/kb | safe: {aggregated_results[(res, approach)]['Safe']} {res}")
    
    results = {}
    results["bmc"] = sorted(bmc_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(bmc_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["kInd"] = sorted(kInd_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(kInd_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["kInd_inv"] = sorted(kInd_inv_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(kInd_inv_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["bmc_kInd"] = sorted(bmc_kInd_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(bmc_kInd_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["bmc_kInd_inv"] = sorted(bmc_kInd_inv_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(bmc_kInd_inv_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["wpc"] = sorted(wpc_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(wpc_results.items(), key= lambda item: locs_per_example.get(item[0]))]

    results["gpdr"] = sorted(gpdr_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_boolEval"] = sorted(gpdr_boolEval_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_boolEval_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_ats"] = sorted(gpdr_ats_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_ats_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_ats_boolEval"] = sorted(gpdr_ats_boolEval_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_ats_boolEval_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_smi"] = sorted(gpdr_smi_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_smi_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_smi_boolEval"] = sorted(gpdr_smi_boolEval_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_smi_boolEval_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_smi_ats"] = sorted(gpdr_smi_ats_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_smi_ats_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    results["gpdr_smi_ats_boolEval"] = sorted(gpdr_smi_ats_boolEval_results.values()) if not complexity else [(locs_per_example[k], v) for k, v in sorted(gpdr_smi_ats_boolEval_results.items(), key= lambda item: locs_per_example.get(item[0]))]
    
    return results

# Wall clock time for number of examples run ---------------------------------------------------------
color_cycle = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 14)))
empty1 = Line2D([], [], linestyle="None", label=" ")
empty2 = Line2D([], [], linestyle="None", label=" ")
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgElapsedTime")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([0.5, 1, 5, 10, 50], [0.5, 1, 5, 10, 50])
plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])

plt.xlabel("# of Examples")
plt.ylabel("Wall Clock Time (s)")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9),

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/wall_clock_time.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/wall_clock_time.tex")

# Wall clock time for safe and unsafe examples seperately ---------------------------------------------------------
for safety in ["safe", "unsafe"]:
    plt.figure(figsize=(8, 6))
    plt.rcParams['axes.prop_cycle'] = color_cycle

    results = {}
    for tool in tool_labels:
        filtered_results = {}
        for (example_name, mode) in aggregated_results:
            if safety == "safe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "True":
                continue
            if safety == "unsafe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "False":
                continue
            if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
                continue
            if tool_labels[tool] != approach_mapping[mode]:
                continue
            filtered_results[example_name] = aggregated_results[(example_name, mode)]["AvgElapsedTime"]
        results[tool] = sorted(filtered_results.values())

    for tool in results:
        plt.plot(results[tool], label=tool_labels[tool])

    plt.yscale("log")
    plt.grid(True, which="major", linestyle="--", alpha=0.5)
    plt.yticks([0.5, 1, 5, 10, 50], [0.5, 1, 5, 10, 50])
    plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])    

    plt.xlabel("# of Examples")
    plt.ylabel("Wall Clock Time (s)")

    plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
               loc='upper center', bbox_to_anchor=(0.5, -0.15),
               fancybox=True, ncol=4, fontsize=9)

    plt.tight_layout()
    plt.savefig(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/wall_clock_time_{safety}.png", dpi=300)
    #plt.show()
    plt.xlabel("\\# of Examples")
    matplot2tikz.save(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/wall_clock_time_{safety}.tex")


# Complexity: Wall clock time per LOC --------------------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgElapsedTime", complexity=True)
for tool in results:
    plt.plot(*zip(*results[tool]), label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)

plt.yticks([1, 10, 50], [1, 10, 50])
plt.xticks([-1, 19, 39, 59], [0, 20, 40, 60])

plt.xlabel("# of LOC")
plt.ylabel("Wall Clock Time (s)")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/wall_clock_time_per_loc.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/wall_clock_time_per_loc.tex")

# Number of SMT Calls for number of examples run ---------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgNumSMTCalls")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([1, 5, 10, 50, 100, 500, 1000], [1, 5, 10, 50, 100, 500, 1000])
plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])

plt.xlabel("# of Examples")
plt.ylabel("# of SMT Calls")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/num_smt_calls.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/num_smt_calls.tex")

# Num of SMT Queries for safe and unsafe examples seperately ---------------------------------------------------------
for safety in ["safe", "unsafe"]:
    plt.figure(figsize=(8, 6))
    plt.rcParams['axes.prop_cycle'] = color_cycle

    results = {}
    for tool in tool_labels:
        filtered_results = {}
        for (example_name, mode) in aggregated_results:
            if safety == "safe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "True":
                continue
            if safety == "unsafe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "False":
                continue
            if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
                continue
            if tool_labels[tool] != approach_mapping[mode]:
                continue
            filtered_results[example_name] = aggregated_results[(example_name, mode)]["AvgNumSMTCalls"]
        results[tool] = sorted(filtered_results.values())

    for tool in results:
        plt.plot(results[tool], label=tool_labels[tool])

    plt.yscale("log")
    plt.grid(True, which="major", linestyle="--", alpha=0.5)
    plt.yticks([1, 5, 10, 50, 100, 500, 1000], [1, 5, 10, 50, 100, 500, 1000])
    plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])    

    plt.xlabel("# of Examples")
    plt.ylabel("# of SMT Calls")

    plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
               loc='upper center', bbox_to_anchor=(0.5, -0.15),
               fancybox=True, ncol=4, fontsize=9)

    plt.tight_layout()
    plt.savefig(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/num_smt_calls_{safety}.png", dpi=300)
    #plt.show()
    plt.xlabel("\\# of Examples")
    matplot2tikz.save(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/num_smt_calls_{safety}.tex")

# Memory usage for number of examples run ---------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgMaxMemoryKB")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([100000, 150000, 200000, 300000, 400000, 500000, 600000], [100, 150, 200, 300, 400, 500, 600])
plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])

plt.xlabel("# of Examples")
plt.ylabel("Max Memory Usage (MB)")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/max_memory_usage.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/max_memory_usage.tex")

# Memory usage for safe and unsafe examples seperately ---------------------------------------------------------
for safety in ["safe", "unsafe"]:
    plt.figure(figsize=(8, 6))
    plt.rcParams['axes.prop_cycle'] = color_cycle

    results = {}
    for tool in tool_labels:
        filtered_results = {}
        for (example_name, mode) in aggregated_results:
            if safety == "safe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "True":
                continue
            if safety == "unsafe" and aggregated_results[(example_name, mode)]['Ground Truth'] != "False":
                continue
            if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
                continue
            if tool_labels[tool] != approach_mapping[mode]:
                continue
            filtered_results[example_name] = aggregated_results[(example_name, mode)]["AvgMaxMemoryKB"]
        results[tool] = sorted(filtered_results.values())

    for tool in results:
        plt.plot(results[tool], label=tool_labels[tool])

    plt.yscale("log")
    plt.grid(True, which="major", linestyle="--", alpha=0.5)
    plt.yticks([100000, 150000, 200000, 300000, 400000, 500000, 600000], [100, 150, 200, 300, 400, 500, 600])
    plt.xticks([-1, 19, 39, 59, 79, 99, total_examples-1], [0, 20, 40, 60, 80, 100, total_examples])

    plt.xlabel("# of Examples")
    plt.ylabel("Max Memory Usage (MB)")

    plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
               loc='upper center', bbox_to_anchor=(0.5, -0.15),
               fancybox=True, ncol=4, fontsize=9)

    plt.tight_layout()
    plt.savefig(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/max_memory_usage_{safety}.png", dpi=300)
    #plt.show()
    plt.xlabel("\\# of Examples")
    matplot2tikz.save(f"../ma-ImpCompVerificationMethods/plots/safe-unsafe/max_memory_usage_{safety}.tex")

# Complexity: Running times of only loop programs.
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = {}
for tool in tool_labels:
    filtered_results = {}
    for (example_name, mode) in aggregated_results:
        if "loop" not in aggregated_results[(example_name, mode)]['Tags']:
            continue
        if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
            continue
        if tool_labels[tool] != approach_mapping[mode]:
            continue
        filtered_results[example_name] = aggregated_results[(example_name, mode)]["AvgElapsedTime"]
    results[tool] = sorted(filtered_results.values())

for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([0.5, 1, 5, 10, 50], [0.5, 1, 5, 10, 50])
plt.xticks([-1, 4, 9, 14, 19, 21], [0, 5, 10, 15, 20, 22])

plt.xlabel("# of Examples")
plt.ylabel("Wall Clock Time (s)")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9),

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/complexity/wall_clock_time_loops.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/complexity/wall_clock_time_loops.tex")

# Running times of only if-programs
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = {}
for tool in tool_labels:
    filtered_results = {}
    for (example_name, mode) in aggregated_results:
        if "if" not in aggregated_results[(example_name, mode)]['Tags']:
            continue
        if aggregated_results[(example_name, mode)]['Safe'] != "Proof" and aggregated_results[(example_name, mode)]['Safe'] != "Counterexample" and aggregated_results[(example_name, mode)]['Safe'] != "NoResult":
            continue
        if tool_labels[tool] != approach_mapping[mode]:
            continue
        filtered_results[example_name] = aggregated_results[(example_name, mode)]["AvgElapsedTime"]
    results[tool] = sorted(filtered_results.values())

for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([0.5, 1, 5, 10, 50], [0.5, 1, 5, 10, 50])
plt.xticks([-1, 19, 39, 59, 79, 85], [0, 20, 40, 60, 80, 86])

plt.xlabel("# of Examples")
plt.ylabel("Wall Clock Time (s)")

plt.legend(handles=plt.gca().get_legend_handles_labels()[0][:6] + [empty1, empty2] + plt.gca().get_legend_handles_labels()[0][6:],
           loc='upper center', bbox_to_anchor=(0.5, -0.15),
           fancybox=True, ncol=4, fontsize=9),

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/complexity/wall_clock_time_ifs.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/complexity/wall_clock_time_ifs.tex")

# Tables -----------------------------------------------------------------

# Classification tables --------------------------------------------------
from jinja2 import Template
# Classification: Proof = Positive, Counterexample = Negative
rows = [(f"\\footnotesize {tool}", counts[tool]['TPsafe'], counts[tool]['TPunsafe'], counts[tool]['FPsafe'], counts[tool]['FPunsafe'],
         counts[tool]['NoResult'], counts[tool]['Crash'], counts[tool]['Timeout'],
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) > 0 else "N/A",
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FPunsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FPunsafe']) > 0 else "N/A",
         f"{(2 * counts[tool]['TPsafe'] / (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FPunsafe'])):.2f}" if (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FPunsafe']) > 0 else "N/A"
        ) for tool in counts]
with open("table-templates/table_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

# Results: # of Proofs, Counterexamples, NoResults, Crashes, Timeouts
rows = [(f"\\footnotesize {tool}", counts[tool]['Proof'], counts[tool]['Counterexample'],
         counts[tool]['NoResult'], counts[tool]['Crash'], counts[tool]['Timeout'], counts[tool]['OOM']
        ) for tool in counts]
with open("table-templates/results_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/results.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

# Classification per class {Safe, Unsafe}: 
rows = [(
         # Safe: TP, TN, FP, FN, Precision, Recall, F1-Score
         f"\\tiny {tool}", counts[tool]['TPsafe'], counts[tool]['TNsafe'], counts[tool]['FPsafe'], counts[tool]['FNsafe'],
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) > 0 else "N/A",
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FNsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FNsafe']) > 0 else "N/A",
         f"{(2 * counts[tool]['TPsafe'] / (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FNsafe'])):.2f}" if (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FNsafe']) > 0 else "N/A",
         # Unsafe: TP, TN, FP, FN, Precision, Recall, F1-Score
         counts[tool]['TPunsafe'], counts[tool]['TNunsafe'], counts[tool]['FPunsafe'], counts[tool]['FNunsafe'],
         f"{(counts[tool]['TPunsafe'] / (counts[tool]['TPunsafe'] + counts[tool]['FPunsafe']) * 100):.1f}\\%" if (counts[tool]['TPunsafe'] + counts[tool]['FPunsafe']) > 0 else "N/A",
         f"{(counts[tool]['TPunsafe'] / (counts[tool]['TPunsafe'] + counts[tool]['FNunsafe']) * 100):.1f}\\%" if (counts[tool]['TPunsafe'] + counts[tool]['FNunsafe']) > 0 else "N/A",
         f"{(2 * counts[tool]['TPunsafe'] / (2 * counts[tool]['TPunsafe'] + counts[tool]['FPunsafe'] + counts[tool]['FNunsafe'])):.2f}" if (2 * counts[tool]['TPunsafe'] + counts[tool]['FPunsafe'] + counts[tool]['FNunsafe']) > 0 else "N/A",
         # Micro averaged F1-Score
         f"{(2 * (counts[tool]['TPsafe'] + counts[tool]['TPunsafe']) / (2 * (counts[tool]['TPsafe'] + counts[tool]['TPunsafe']) + counts[tool]['FPsafe'] + counts[tool]['FPunsafe'] + counts[tool]['FNsafe'] + counts[tool]['FNunsafe'])):.2f}" 
            if (2 * (counts[tool]['TPsafe'] + counts[tool]['TPunsafe']) + counts[tool]['FPsafe'] + counts[tool]['FPunsafe'] + counts[tool]['FNsafe'] + counts[tool]['FNunsafe']) > 0 else "N/A",
       ) for tool in counts]
with open("table-templates/classification_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/detailed_classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

# Classification results SOAPed (= Safely Over-Approximated)
rows_sec = [( # Tool, TP, TN, FP, FN, Precision, Recall, F1-Score
    f"\\footnotesize {tool}",
    f"{counts[tool]['TSec']}", f"{counts[tool]['TInsec']}", f"({counts[tool]['TInsecSOAP']})",
    f"{counts[tool]['FSec']}", f"{counts[tool]['FInsec']}", f"({counts[tool]['FInsecSOAP']})",
    f"{(counts[tool]['TSec'] / (counts[tool]['TSec'] + counts[tool]['FSec']) * 100):.1f}\\%" if (counts[tool]['TSec'] + counts[tool]['FSec']) > 0 else "N/A",
    f"{(counts[tool]['TSec'] / (counts[tool]['TSec'] + counts[tool]['FInsec']) * 100):.1f}\\%" if (counts[tool]['TSec'] + counts[tool]['FInsec']) > 0 else "N/A",
    f"{(2 * counts[tool]['TSec'] / (2 * counts[tool]['TSec'] + counts[tool]['FSec'] + counts[tool]['FInsec'])):.2f}" if (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FNsafe']) > 0 else "N/A"
    ) for tool in counts]
rows_insec = [( # Tool, TP, TN, FP, FN, Precision, Recall, F1-Score
    f"\\footnotesize {tool}",
    f"{counts[tool]['TSec']}", f"{counts[tool]['TInsec']}", f"({counts[tool]['TInsecSOAP']})",
    f"{counts[tool]['FSec']}", f"{counts[tool]['FInsec']}", f"({counts[tool]['FInsecSOAP']})",
    f"{(counts[tool]['TInsec'] / (counts[tool]['TInsec'] + counts[tool]['FInsec']) * 100):.1f}\\%" if (counts[tool]['TInsec'] + counts[tool]['FInsec']) > 0 else "N/A",
    f"{(counts[tool]['TInsec'] / (counts[tool]['TInsec'] + counts[tool]['FSec']) * 100):.1f}\\%" if (counts[tool]['TInsec'] + counts[tool]['FSec']) > 0 else "N/A",
    f"{(2 * counts[tool]['TInsec'] / (2 * counts[tool]['TInsec'] + counts[tool]['FSec'] + counts[tool]['FInsec'])):.2f}" if (2 * counts[tool]['TInsec'] + counts[tool]['FSec'] + counts[tool]['FInsec']) > 0 else "N/A"
    ) for tool in counts]
rows = rows_sec
with open("table-templates/soap_results_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/soap_classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

# Big results table for Appendix
# BMC
for k, v in approach_mapping.items():
    rows = [(f"{example_name}".replace("_", "\\_").replace("SvBenchmarksJava\\_", ""),
            #approach_mapping[mode], 
            aggregated_results[(example_name, mode)]['Ground Truth'],
            f"{aggregated_results[(example_name, mode)]['Safe']}".replace("-", "Crash [BM]"),
            f"{aggregated_results[(example_name, mode)]['AvgElapsedTime']:.2f}",
            f"{aggregated_results[(example_name, mode)]['StdElapsedTime']:.2f}",
            f"{aggregated_results[(example_name, mode)]['AvgNumSMTCalls']:.0f}" if aggregated_results[(example_name, mode)]['AvgNumSMTCalls'] != 0 else "",
            f"{aggregated_results[(example_name, mode)]['AvgMaxMemoryKB'] / 1000:.2f}",
            f"{aggregated_results[(example_name, mode)]['StdMaxMemoryKB'] / 1000:.2f}"
            ) for (example_name, mode) in aggregated_results if mode == k]
    with open("table-templates/aggregated_template.tex") as f, open(f"../ma-ImpCompVerificationMethods/tables/results/aggregated_results_{v}.tex", "w") as out:
        template = Template(f.read())
        out.write(template.render(rows=rows, caption=f"{v} average results"))

print("Done")
