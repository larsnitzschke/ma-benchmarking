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
        aggregated_results[(f"{i // repititions}: {example_name}", mode)] = {
            'Safe': safe,
            'AvgUserTimeSec': sum(user_times) / repititions,
            'AvgSystemTimeSec': sum(system_times) / repititions,
            'AvgCPUPercent': sum(cpu_percents) / repititions,
            'AvgElapsedTime': sum(elapsed_times) / repititions,
            'AvgMaxMemoryKB': sum(max_memories) / repititions,
            'Classification': classification,
            'Tags': tags
        }
        i += repititions

# Calculate Classification metrics
counts = {
    "BMC": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "Kind": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "BMC+Kind": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "Hoare": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (ATS)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (ATS + B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI + B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI + ATS)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},
    "GPDR (SMI + ATS + B-Eval)": {"TP":0, "TN":0, "FP":0, "FN":0, "NoResult":0, "Crash":0, "Timeout":0},       
}
approach_mapping = {
    "-b": "BMC",
    "-k": "Kind",
    "-bk": "BMC+Kind",
    "-p": "Hoare",
    "-g": "GPDR",
    "-gB": "GPDR (B-Eval)",
    "-g --gpdr-ats": "GPDR (ATS)",
    "-gB --gpdr-ats": "GPDR (ATS + B-Eval)",
    "-g --gpdr-smi": "GPDR (SMI)",
    "-gB --gpdr-smi": "GPDR (SMI + B-Eval)",
    "-g --gpdr-smi --gpdr-ats": "GPDR (SMI + ATS)",
    "-gB --gpdr-smi --gpdr-ats": "GPDR (SMI + ATS + B-Eval)",       
}
classification_labels = {
    "True Positive": "TP",
    "True Negative": "TN",
    "False Positive": "FP",
    "False Negative": "FN",
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
            print(f"Warning: Unknown classification for {example_name} in mode {mode}")
    elif aggregated_results[(example_name, mode)]['Classification'] in classification_labels:
        label = classification_labels[aggregated_results[(example_name, mode)]['Classification']]
        counts[approach_mapping[mode]][label] += 1
    else:
        print(f"Warning: Unknown classification for {example_name} in mode {mode}")

print(counts)
exit(0)


# Plot -----------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np


# Wall clock time for number of examples run
plt.figure(figsize=(8, 6))
plt.rcParams['axes.prop_cycle'] = plt.cycler(color = plt.cm.nipy_spectral(np.linspace(1, 0, 12)))

bmc_results = {}
kind_results = {}
bmc_kind_results = {}
hoare_results = {}
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
        bmc_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-k":
        kind_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == '-p':
        hoare_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-bk":
        bmc_kind_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-g":
        gpdr_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-gB":
        gpdr_boolEval_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-g --gpdr-ats":
        gpdr_ats_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-gB --gpdr-ats":
        gpdr_ats_boolEval_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-g --gpdr-smi":
        gpdr_smi_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-gB --gpdr-smi":
        gpdr_smi_boolEval_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-g --gpdr-smi --gpdr-ats":
        gpdr_smi_ats_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']
    if mode == "-gB --gpdr-smi --gpdr-ats":
        gpdr_smi_ats_boolEval_results[example_name] = aggregated_results[(example_name, mode)]['AvgUserTimeSec']


# for (example_name, mode) in aggregated_results:
#     if aggregated_results[(example_name, mode)]['Classification'].startswith("True"):
#         continue
#     if mode == "-k":
#         print("UNSAFE:", example_name, aggregated_results[(example_name, mode)]['AvgUserTimeSec'])

bmc = sorted(bmc_results.values())
kind = sorted(kind_results.values())
bmc_kind = sorted(bmc_kind_results.values())
hoare = sorted(hoare_results.values())

gpdr = sorted(gpdr_results.values())
gpdr_boolEval = sorted(gpdr_boolEval_results.values())
gpdr_ats = sorted(gpdr_ats_results.values())
gpdr_ats_boolEval = sorted(gpdr_ats_boolEval_results.values())
gpdr_smi = sorted(gpdr_smi_results.values())
gpdr_smi_boolEval = sorted(gpdr_smi_boolEval_results.values())
gpdr_smi_ats = sorted(gpdr_smi_ats_results.values())
gpdr_smi_ats_boolEval = sorted(gpdr_smi_ats_boolEval_results.values())

plt.plot(bmc, label="BMC")
plt.plot(kind, label="Kind")
plt.plot(bmc_kind, label="BMC + Kind")
plt.plot(hoare, label="Hoare")
plt.plot(gpdr, label="GPDR")
plt.plot(gpdr_boolEval, label="GPDR (B-Eval)")
plt.plot(gpdr_ats, label="GPDR (ATS)")
plt.plot(gpdr_ats_boolEval, label="GPDR (ATS + B-Eval)")
plt.plot(gpdr_smi, label="GPDR (SMI)")
plt.plot(gpdr_smi_boolEval, label="GPDR (SMI + B-Eval)")
plt.plot(gpdr_smi_ats, label="GPDR (SMI + ATS)")
plt.plot(gpdr_smi_ats_boolEval, label="GPDR (SMI + ATS + B-Eval)")


# Formatting -----------------------------------------------------------------

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([1, 5, 10, 50], [1, 5, 10, 50])

plt.xlabel("\# of Examples")
plt.ylabel("Wall Clock Time (s)")

#plt.title("Tool Performance by Number of Examples")
#plt.legend(ncol=2, fontsize=9)
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, ncol=4, fontsize=9)

plt.tight_layout()
plt.savefig("plots/wall_clock_time.png", dpi=300)
#plt.show()


# Relevant numbers:
# Total examples = 115
# How many examples are (ground truth) safe/unsafe? -> Can be solved by Hoare / BMC?
# How many examples do use arrays / pointers

# Build examples that show why (how and when) GPDR with SMI / ATS / Boolean Evaluation works / does not work. 

# Plots
# UserTime for number of examples run
# NumSMTCalls for number of examples run (?)
# MaxMemory for number of examples run

# Tables
# Classification (TP, TN, FP, FN) for each tool + Precision, Recall, F1-score + Timeouts / Neither
# Appendix: All results in a big table

import matplot2tikz
matplot2tikz.save("plots/wall_clock_time.tex")



# Tables:

from jinja2 import Template
rows = [("BMC", 1,1,1,1,1,1,1,1,1,1)]


with open("tables/table_template.tex") as f:
    template = Template(f.read())
    print(template.render(rows=rows))
