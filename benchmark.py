import re
import subprocess
from dataclasses import dataclass
import csv
from datetime import datetime

path_to_whilestar = "../whilestar"
wvm_gradle = f"{path_to_whilestar}/gradlew"
mode = "-k"
path_to_examples = f"{path_to_whilestar}/examples"
example = f"{path_to_examples}/array/ex1.w"

file = open(f"{path_to_examples}/examples-list.txt", "r")
print(file.readlines())
file.close()

@dataclass
class Example:
    path: str
    name: str
    success: bool
    tags: list[str] = None

examples = []
for line in open(f"{path_to_examples}/examples-list.txt", "r"):
    line = line.strip()
    split = line.split(" ")
    tags = split[3].split(",") if len(split) > 3 else []
    examples.append(Example(f"{path_to_examples}/{split[0]}", split[1], bool(split[2]), tags))
print(examples)

# Benchmarking: Warm-up, BMC; k-induction, WPC-Proof, GPDR, GPDR with boolean evaluation
modes = ["--warmup", "-b", "-k", "-p", "-g", "-gB"]
limit_examples = None  # Set to an integer to limit number of examples for testing

results = []
for mode in modes:
    for example in examples[:limit_examples]:
        print(f"Running benchmark for example: {example.name} with mode: {mode}")
        try:
            result = subprocess.run(["/usr/bin/time", "-v", wvm_gradle, "run", f"--args={mode} {example.path}"],
                                capture_output=True, text=True,
                                cwd=path_to_whilestar,
                                timeout=10)
        except subprocess.TimeoutExpired as e:
            print(f"Timeout expired for example: {example.name} with mode: {mode}")
            results.append([example.name, mode, "TIMEOUT", None, None, None, None, None, None, " ".join(example.tags)])
            continue

        num_smt_calls = None
        match = re.search(r"# NumberOfSMTCalls:\s*(\d+)", result.stdout)
        if match:
            num_smt_calls = match.group(1)
        safe = None
        match = re.search(r"# Safe:\s*(\w+)", result.stdout)
        if match:
            safe = match.group(1)

        user_time = re.search(r"User time \(seconds\):\s*([\d.]+)", result.stderr)
        system_time = re.search(r"System time \(seconds\):\s*([\d.]+)", result.stderr)
        cpu_percent = re.search(r"Percent of CPU this job got:\s*(\d+)%", result.stderr)
        elapsed = re.search(r"Elapsed \(wall clock\) time.*:\s*([\d:.]+)", result.stderr)
        max_rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", result.stderr)

        metrics = {
            "user_time_sec": float(user_time.group(1)) if user_time else None,
            "system_time_sec": float(system_time.group(1)) if system_time else None,
            "cpu_percent": int(cpu_percent.group(1)) if cpu_percent else None,
            "elapsed_time": elapsed.group(1) if elapsed else None,
            "max_memory_kb": int(max_rss.group(1)) if max_rss else None,
        }
        print(f"Metrics: {metrics}")

        results.append([example.name, mode, safe, num_smt_calls,
                        metrics["user_time_sec"], metrics["system_time_sec"],
                        metrics["cpu_percent"], metrics["elapsed_time"],
                        metrics["max_memory_kb"],
                        " ".join(example.tags)])

with open(f"benchmark_results_{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Example", "Mode", "Safe", "NumberOfSMTCalls",
                     "UserTimeSec", "SystemTimeSec", "CPUPercent",
                     "ElapsedTime", "MaxMemoryKB", "Tags"])
    writer.writerows(results)

print("Benchmarking complete. Results saved to benchmark_results.csv")