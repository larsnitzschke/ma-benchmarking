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

# Plot -----------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np


# Wall clock time for number of examples run
plt.figure(figsize=(10, 6))
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
plt.plot(gpdr_boolEval, label="GPDR (Boolean Evaluation)")
plt.plot(gpdr_ats, label="GPDR (Array Transition Systems)")
plt.plot(gpdr_ats_boolEval, label="GPDR (ATS + B-Eval)")
plt.plot(gpdr_smi, label="GPDR (SMI)")
plt.plot(gpdr_smi_boolEval, label="GPDR (SMI + B-Eval)")
plt.plot(gpdr_smi_ats, label="GPDR (SMI + ATS)")
plt.plot(gpdr_smi_ats_boolEval, label="GPDR (SMI + ATS + B-Eval)")


# Formatting -----------------------------------------------------------------

plt.yscale("log")
plt.grid(True, which="major", linestyle="--", alpha=0.5)
plt.yticks([1, 5, 10, 50], [1, 5, 10, 50])

plt.xlabel("# of Examples")
plt.ylabel("Wall Clock Time (s)")

#plt.title("Tool Performance by Number of Examples")
plt.legend(ncol=2, fontsize=9)

plt.tight_layout()
plt.show()


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

import tikzplotlib
tikzplotlib.save("benchmark_plots.tex")