import os, gc, subprocess
import csv, re
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Example:
    path: str
    name: str
    expected_safety: bool
    tags: list[str] = None

def classification(result: str, expected_safety: bool) -> str:
    if result == "Proof" and expected_safety:
        return "True Positive"
    elif result == "Counterexample" and not expected_safety:
        return "False Positive"
    elif result == "Proof" and not expected_safety:
        return "False Positive"
    elif result == "Counterexample" and expected_safety:
        return "False Negative"
    else:
        return ""

def extract_metrics(stdout, stderr) -> dict:
    num_smt_calls = None
    match = re.search(r"# NumberOfSMTCalls:\s*(\d+)", stdout)
    if match:
        num_smt_calls = match.group(1)
    verification_result = None
    match = re.search(r"# Safe:\s*(\w+)", stdout)
    if match:
        verification_result = match.group(1)
    else:
        match = re.search(r"OutOfMemoryError", stderr)
        if match:
            verification_result = "OUTOFMEMORY"

    user_time = re.search(r"User time \(seconds\):\s*([\d.]+)", stderr)
    system_time = re.search(r"System time \(seconds\):\s*([\d.]+)", stderr)
    cpu_percent = re.search(r"Percent of CPU this job got:\s*(\d+)%", stderr)
    elapsed = re.search(r"Elapsed \(wall clock\) time.*:\s*([\d:.]+)", stderr)
    max_rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", stderr)

    return {
        "num_smt_calls": num_smt_calls,
        "verification_result": verification_result,
        "user_time_sec": float(user_time.group(1)) if user_time else None,
        "system_time_sec": float(system_time.group(1)) if system_time else None,
        "cpu_percent": int(cpu_percent.group(1)) if cpu_percent else None,
        "elapsed_time": elapsed.group(1) if elapsed else None,
        "max_memory_kb": int(max_rss.group(1)) if max_rss else None,
    }

# Path configurations
path_to_whilestar = "../whilestar"
wvm_gradle = f"{path_to_whilestar}/gradlew"
mode = "-k"
path_to_examples = f"{path_to_whilestar}/examples"
example = f"{path_to_examples}/array/ex1.w"

# Total benchmarking time
benchmarking_start_time = datetime.now()

# Load examples
with open(f"{path_to_examples}/examples-list.txt", "r") as file:
    examples = []
    for line in file:
        line = line.strip()
        split = line.split(" ")
        tags = split[3].split(",") if len(split) > 3 else []
        examples.append(Example(f"{path_to_examples}/{split[0]}", split[1], bool(split[2]), tags))

# Benchmarking: Warm-up, BMC, k-induction, BMC+k-ind, WPC-Proof, GPDR, GPDR with boolean evaluation, GPDR with ArrayTransitionSystems, GPDR with SubModelInterpolation
modes = ["--warmup", "-b", "-k", "-bk", "-p", "-g", "-gB", "-g --gpdr-smi", "-gB --gpdr-smi", "-g --gpdr-ats", "-gB --gpdr-ats", "-g --gpdr-smi --gpdr-ats", "-gB --gpdr-smi --gpdr-ats"]
limit_examples = None  # Set to an integer to limit number of examples for testing
repititions = 5  # Number of repititions per example per mode
timeout = 30 # Timeout in seconds per run

# Prepare output CSV file
csv_filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
with open(csv_filename, "a", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Example", "Mode", "Run Number", "Safe", "NumberOfSMTCalls",
                     "UserTimeSec", "SystemTimeSec", "CPUPercent",
                     "ElapsedTime", "MaxMemoryKB", "Classification", "Tags"])

# Main Loop
keyboard_interrupt = False
for example in examples[:limit_examples]:
    if keyboard_interrupt:
        break
    for mode in modes:
        if keyboard_interrupt:
            break
        for run_number in range(repititions):
            gc.collect()
            print(f"Running benchmark for example: {example.name} with mode: {mode}")
            try:
                benchmarking_process = subprocess.Popen(["/usr/bin/time", "-v", "timeout", str(timeout), "java", "-jar", "build/libs/wvm-fatJar-verification-benchmarking.jar", *mode.split(" "), example.path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True,
                                    cwd=path_to_whilestar,
                                    preexec_fn=subprocess.os.setsid)
                stdout, stderr = benchmarking_process.communicate()
            except KeyboardInterrupt:
                print("Benchmarking interrupted by user.")
                os.killpg(benchmarking_process.pid, subprocess.signal.SIGKILL)
                keyboard_interrupt = True
                break

            metrics = extract_metrics(stdout, stderr)
            if benchmarking_process.returncode == 124:  # Timeout return code 124
                print(f"Timeout expired for example: {example.name} with mode: {mode}")
                metrics["verification_result"] = "TIMEOUT"

            result_line = [example.name, mode, run_number,
                            metrics["verification_result"], metrics["num_smt_calls"],
                            metrics["user_time_sec"], metrics["system_time_sec"],
                            metrics["cpu_percent"], metrics["elapsed_time"],
                            metrics["max_memory_kb"],
                            classification(metrics["verification_result"], example.expected_safety),
                            " ".join(example.tags)]
            with open(csv_filename, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(result_line)

print("Benchmarking complete. Results saved to", csv_filename)

total_benchmarking_time = datetime.now() - benchmarking_start_time
print(f"Total benchmarking time: {(total_benchmarking_time.total_seconds() / 60):.2f} minutes")