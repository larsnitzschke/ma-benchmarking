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
    results = [row for row in reader]
    i = 0
    while i < len(results):
        block = results[i:i+repititions]
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
            'Tags': tags
        }
        i += repititions

# Calculate Classification metrics
counts = {
    "BMC": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "KInd": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "BMC+KInd": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "WPC": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (ATS)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (ATS+B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI+B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI+ATS)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI+ATS+B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},       
}
approach_mapping = {
    "-b": "BMC",
    "-k": "KInd",
    "-bk": "BMC+KInd",
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
for (example_name, mode) in aggregated_results:
    if mode == "--warmup":
        continue
    if aggregated_results[(example_name, mode)]['Classification'] == "":
        if aggregated_results[(example_name, mode)]['Safe'] == "OUTOFMEMORY" \
            or aggregated_results[(example_name, mode)]['Safe'] == "TIMEOUT":
            counts[approach_mapping[mode]]["Timeout"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "Crash":
            counts[approach_mapping[mode]]["Crash"] += 1
        elif aggregated_results[(example_name, mode)]['Safe'] == "NoResult":
            counts[approach_mapping[mode]]["NoResult"] += 1
        else:
            # print(f"Warning: Unknown classification for {example_name} in mode {mode}. Interpret as Crash.")
            counts[approach_mapping[mode]]["Crash"] += 1
    elif aggregated_results[(example_name, mode)]['Classification'] in classification_labels:
        label = classification_labels[aggregated_results[(example_name, mode)]['Classification']]
        counts[approach_mapping[mode]][label] += 1
        #if mode == "-p" and label == "FP":
        #    print(f"WPC False Positive: {example_name}")
    else:
        print(f"Warning: Unknown classification for {example_name} in mode {mode}")

print(counts)

# Plot -----------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
import matplot2tikz

def results_by_approach_for_metric(aggregated_results, metric):
    bmc_results = {}
    kInd_results = {}
    bmc_kInd_results = {}
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
        if mode == '-p':
            wpc_results[example_name] = aggregated_results[(example_name, mode)][metric]
        if mode == "-bk":
            bmc_kInd_results[example_name] = aggregated_results[(example_name, mode)][metric]
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
    results["bmc_kInd"] = sorted(bmc_kInd_results.values())
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
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 12)))

results = results_by_approach_for_metric(aggregated_results, "AvgElapsedTime")
plt.plot(results["bmc"], label="BMC")
plt.plot(results["kInd"], label="KInd")
plt.plot(results["bmc_kInd"], label="BMC + KInd")
plt.plot(results["wpc"], label="WPC")
plt.plot(results["gpdr"], label="GPDR")
plt.plot(results["gpdr_boolEval"], label="GPDR (B-Eval)")
plt.plot(results["gpdr_ats"], label="GPDR (ATS)")
plt.plot(results["gpdr_ats_boolEval"], label="GPDR (ATS + B-Eval)")
plt.plot(results["gpdr_smi"], label="GPDR (SMI)")
plt.plot(results["gpdr_smi_boolEval"], label="GPDR (SMI + B-Eval)")
plt.plot(results["gpdr_smi_ats"], label="GPDR (SMI + ATS)")
plt.plot(results["gpdr_smi_ats_boolEval"], label="GPDR (SMI + ATS + B-Eval)")

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
plt.rcParams['axes.prop_cycle'] = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 12)))

results = results_by_approach_for_metric(aggregated_results, "AvgNumSMTCalls")
plt.plot(results["bmc"], label="BMC")
plt.plot(results["kInd"], label="KInd")
plt.plot(results["bmc_kInd"], label="BMC + KInd")
plt.plot(results["wpc"], label="WPC")
plt.plot(results["gpdr"], label="GPDR")
plt.plot(results["gpdr_boolEval"], label="GPDR (B-Eval)")
plt.plot(results["gpdr_ats"], label="GPDR (ATS)")
plt.plot(results["gpdr_ats_boolEval"], label="GPDR (ATS + B-Eval)")
plt.plot(results["gpdr_smi"], label="GPDR (SMI)")
plt.plot(results["gpdr_smi_boolEval"], label="GPDR (SMI + B-Eval)")
plt.plot(results["gpdr_smi_ats"], label="GPDR (SMI + ATS)")
plt.plot(results["gpdr_smi_ats_boolEval"], label="GPDR (SMI + ATS + B-Eval)")

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
plt.rcParams['axes.prop_cycle'] = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 12)))

results = results_by_approach_for_metric(aggregated_results, "AvgMaxMemoryKB")
plt.plot(results["bmc"], label="BMC")
plt.plot(results["kInd"], label="KInd")
plt.plot(results["bmc_kInd"], label="BMC + KInd")
plt.plot(results["wpc"], label="WPC")
plt.plot(results["gpdr"], label="GPDR")
plt.plot(results["gpdr_boolEval"], label="GPDR (B-Eval)")
plt.plot(results["gpdr_ats"], label="GPDR (ATS)")
plt.plot(results["gpdr_ats_boolEval"], label="GPDR (ATS + B-Eval)")
plt.plot(results["gpdr_smi"], label="GPDR (SMI)")
plt.plot(results["gpdr_smi_boolEval"], label="GPDR (SMI + B-Eval)")
plt.plot(results["gpdr_smi_ats"], label="GPDR (SMI + ATS)")
plt.plot(results["gpdr_smi_ats_boolEval"], label="GPDR (SMI + ATS + B-Eval)")

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
rows = [(f"\\footnotesize {tool}", counts[tool]['TP'], counts[tool]['TN'], counts[tool]['FP'], counts[tool]['FN'],
         counts[tool]['NoResult'], counts[tool]['Crash'], counts[tool]['Timeout'],
         f"{(counts[tool]['TP'] / (counts[tool]['TP'] + counts[tool]['FP']) * 100):.1f}\\%" if (counts[tool]['TP'] + counts[tool]['FP']) > 0 else "N/A",
         f"{(counts[tool]['TP'] / (counts[tool]['TP'] + counts[tool]['FN']) * 100):.1f}\\%" if (counts[tool]['TP'] + counts[tool]['FN']) > 0 else "N/A",
         f"{(2 * counts[tool]['TP'] / (2 * counts[tool]['TP'] + counts[tool]['FP'] + counts[tool]['FN'])):.2f}" if (2 * counts[tool]['TP'] + counts[tool]['FP'] + counts[tool]['FN']) > 0 else "N/A"
        ) for tool in counts]


with open("table-templates/table_template.tex") as f, open("../ma-ImpCompVerificationMethods/tables/classifications.tex", "w") as out:
    template = Template(f.read())
    out.write(template.render(rows=rows))


# Big results table for Appendix ---------------------------------------------------------
# TODO: Is this necessary?


# TODO: Research more interesting plots for the results
