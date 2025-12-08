# Get relevant numbers from ground truth data
with open("examples-list-all.txt", "r") as f:
    lines = f.readlines()
    total_examples = 0
    safe_examples = 0
    unsafe_examples = 0
    pointer_examples = 0
    array_examples = 0
    array_or_pointer_examples = 0
    for line in lines:
        total_examples += 1
        safe = line.strip().split(" ")[2].lower()
        if safe == "true":
            safe_examples += 1
        elif safe == "false":
            unsafe_examples += 1
        split = line.strip().split(" ")
        tags = split[3].split(",") if len(split) > 3 else []
        if "array" in tags:
            array_examples += 1
        if "pointer" in tags:
            pointer_examples += 1
        if "array" in tags or "pointer" in tags:
            array_or_pointer_examples += 1

print(f"Total examples: {total_examples}, Safe: {safe_examples}, Unsafe: {unsafe_examples}, Arrays: {array_examples}, Pointers: {pointer_examples}, Arrays or Pointers: {array_or_pointer_examples}")

# Read results and aggregate them
import csv

aggregated_results = {}
repititions = 5
with open("benchmark-results.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    all_results = [row for row in reader]
    i = 0
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
        safe = block[0]['Safe']
        user_times = [float(row['UserTimeSec']) for row in block]
        system_times = [float(row['SystemTimeSec']) for row in block]
        cpu_percents = [int(row['CPUPercent']) for row in block]
        elapsed_times = [float(row['ElapsedTime']) for row in block]
        max_memories = [int(row['MaxMemoryKB']) for row in block]
        tags = block[0]['Tags']
        if block[0]['Classification'] != block[1]['Classification'] \
            or block[0]['Classification'] != block[2]['Classification'] \
            or block[0]['Classification'] != block[3]['Classification'] \
            or block[0]['Classification'] != block[4]['Classification']:
            print(f"Warning: Inconsistent classification for {example_name} in mode {mode}")
        classification = block[0]['Classification']
        ground_truth = block[0]['Ground Truth']
        num_smt_calls = [int(row['NumberOfSMTCalls']) if row['NumberOfSMTCalls'].isnumeric() else 0 for row in block]
        aggregated_results[(f"{i // repititions}: {example_name}", mode)] = {
            'Safe': safe,
            'AvgUserTimeSec': sum(user_times) / repititions,
            'AvgSystemTimeSec': sum(system_times) / repititions,
            'AvgCPUPercent': sum(cpu_percents) / repititions,
            'AvgElapsedTime': sum(elapsed_times) / repititions,
            'AvgMaxMemoryKB': sum(max_memories) / repititions,
            'AvgNumSMTCalls': sum(num_smt_calls) / repititions,
            'Classification': classification,
            'Ground Truth': ground_truth,
            'Tags': tags
        }
        i += repititions

# Calculate Classification metrics
counts = {
    "BMC": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "KInd": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "KInd (Inv)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "BMC+KInd": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "BMC+KInd (Inv)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "WPC": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (ATS)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (ATS+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (SMI)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (SMI+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (SMI+ATS)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
    "GPDR (SMI+ATS+B-Eval)": {"Proof":0, "Counterexample":0, "NoResult":0, "Crash":0, "Timeout":0, "TPsafe":0, "TNsafe":0, "FPsafe":0, "FNsafe":0, "TPunsafe":0, "TNunsafe":0, "FPunsafe":0, "FNunsafe":0},
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
    "bmc_kInd": "BMC + KInd",
    "bmc_kInd_inv": "BMC + KInd (Inv)",
    "wpc": "WPC",
    "gpdr": "GPDR",
    "gpdr_boolEval": "GPDR (B-Eval)",
    "gpdr_ats": "GPDR (ATS)",
    "gpdr_ats_boolEval": "GPDR (ATS + B-Eval)",
    "gpdr_smi": "GPDR (SMI)",
    "gpdr_smi_boolEval": "GPDR (SMI + B-Eval)",
    "gpdr_smi_ats": "GPDR (SMI + ATS)",
    "gpdr_smi_ats_boolEval": "GPDR (SMI + ATS + B-Eval)",
}

for (example_name, mode) in aggregated_results:
    if mode == "--warmup":
        continue
    if True: #aggregated_results[(example_name, mode)]['Classification'] == "":
        if aggregated_results[(example_name, mode)]['Safe'] == "Proof":
            counts[approach_mapping[mode]]["Proof"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["Counterexample"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Crash" \
            or aggregated_results[(example_name, mode)]['Safe'] == "ERROR" \
            or aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY":
            counts[approach_mapping[mode]]["Crash"] += 1
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
        elif aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["FNsafe"] += 1
            counts[approach_mapping[mode]]["FPunsafe"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Crash" \
            or aggregated_results[(example_name, mode)]['Safe'] == "NoResult" \
            or aggregated_results[(example_name, mode)]['Safe'] == "TIMEOUT" \
            or aggregated_results[(example_name, mode)]['Safe'] == "ERROR" \
            or aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY":
            counts[approach_mapping[mode]]["FNsafe"] += 1
    elif aggregated_results[(example_name, mode)]['Ground Truth'] == "False":
        if aggregated_results[(example_name, mode)]['Safe'] == "Counterexample":
            counts[approach_mapping[mode]]["TNsafe"] += 1
            counts[approach_mapping[mode]]["TPunsafe"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Proof":
            counts[approach_mapping[mode]]["FPsafe"] += 1
            counts[approach_mapping[mode]]["FNunsafe"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Crash" \
            or aggregated_results[(example_name, mode)]['Safe'] == "NoResult" \
            or aggregated_results[(example_name, mode)]['Safe'] == "TIMEOUT" \
            or aggregated_results[(example_name, mode)]['Safe'] == "ERROR" \
            or aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY":
            counts[approach_mapping[mode]]["FNunsafe"] += 1
    else:
        print(f"Warning: Unknown classification for {example_name} in mode {mode}")

# Plot -----------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
import matplot2tikz

def results_by_approach_for_metric(aggregated_results, metric):
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
        if not aggregated_results[(example_name, mode)]['Classification'].startswith("True"):
            continue
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

    results = {}
    results["bmc"] = sorted(bmc_results.values())
    results["kInd"] = sorted(kInd_results.values())
    results["kInd_inv"] = sorted(kInd_inv_results.values())
    results["bmc_kInd"] = sorted(bmc_kInd_results.values())
    results["bmc_kInd_inv"] = sorted(bmc_kInd_inv_results.values())
    results["wpc"] = sorted(wpc_results.values())

    results["gpdr"] = sorted(gpdr_results.values())
    results["gpdr_boolEval"] = sorted(gpdr_boolEval_results.values())
    results["gpdr_ats"] = sorted(gpdr_ats_results.values())
    results["gpdr_ats_boolEval"] = sorted(gpdr_ats_boolEval_results.values())
    results["gpdr_smi"] = sorted(gpdr_smi_results.values())
    results["gpdr_smi_boolEval"] = sorted(gpdr_smi_boolEval_results.values())
    results["gpdr_smi_ats"] = sorted(gpdr_smi_ats_results.values())
    results["gpdr_smi_ats_boolEval"] = sorted(gpdr_smi_ats_boolEval_results.values())
    
    return results

# Wall clock time for number of examples run ---------------------------------------------------------
color_cycle = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 14)))
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgElapsedTime")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([1, 5, 10, 50], [1, 5, 10, 50])

plt.xlabel("# of Examples")
plt.ylabel("Wall Clock Time (s)")

#plt.title("Tool Performance by Number of Examples")
#plt.legend(ncol=2, fontsize=9)
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/wall_clock_time.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/wall_clock_time.tex")

# Number of SMT Calls for number of examples run ---------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgNumSMTCalls")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([1, 5, 10, 50, 100, 500, 1000], [1, 5, 10, 50, 100, 500, 1000])

plt.xlabel("# of Examples")
plt.ylabel("Number of SMT Calls")

plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/num_smt_calls.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/num_smt_calls.tex")

# Memory usage for number of examples run ---------------------------------------------------------
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = color_cycle

results = results_by_approach_for_metric(aggregated_results, "AvgMaxMemoryKB")
for tool in results:
    plt.plot(results[tool], label=tool_labels[tool])

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([100000, 200000, 300000, 400000, 500000], [100, 200, 300, 400, 500])

plt.xlabel("# of Examples")
plt.ylabel("Max Memory Usage (MB)")

plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("../ma-ImpCompVerificationMethods/plots/max_memory_usage.png", dpi=300)
#plt.show()
plt.xlabel("\\# of Examples")
matplot2tikz.save("../ma-ImpCompVerificationMethods/plots/max_memory_usage.tex")

# Tables -----------------------------------------------------------------

# Classification table ---------------------------------------------------------
from jinja2 import Template
rows = [(f"\\footnotesize {tool}", counts[tool]['TPsafe'], counts[tool]['TPunsafe'], counts[tool]['FPsafe'], counts[tool]['FPunsafe'],
         counts[tool]['NoResult'], counts[tool]['Crash'], counts[tool]['Timeout'],
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FPsafe']) > 0 else "N/A",
         f"{(counts[tool]['TPsafe'] / (counts[tool]['TPsafe'] + counts[tool]['FPunsafe']) * 100):.1f}\\%" if (counts[tool]['TPsafe'] + counts[tool]['FPunsafe']) > 0 else "N/A",
         f"{(2 * counts[tool]['TPsafe'] / (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FPunsafe'])):.2f}" if (2 * counts[tool]['TPsafe'] + counts[tool]['FPsafe'] + counts[tool]['FPunsafe']) > 0 else "N/A"
        ) for tool in counts]


with open("table-templates/table_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

rows = [(f"\\footnotesize {tool}", counts[tool]['Proof'], counts[tool]['Counterexample'],
         counts[tool]['NoResult'], counts[tool]['Crash'], counts[tool]['Timeout']
        ) for tool in counts]

with open("table-templates/results_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/results.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

rows = [(f"\\footnotesize {tool}", counts[tool]['TPsafe'], counts[tool]['TNsafe'], counts[tool]['FPsafe'], counts[tool]['FNsafe'],
        counts[tool]['TPunsafe'], counts[tool]['TNunsafe'], counts[tool]['FPunsafe'], counts[tool]['FNunsafe'],
        0,0,0 # TODO: Rec, Prec, F1
       ) for tool in counts]

with open("table-templates/classification_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/detailed_classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))

# Big results table for Appendix ---------------------------------------------------------
# TODO: Is this necessary?


# TODO: Research more interesting plots for the results
