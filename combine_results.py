import csv

gpdr_results = {}
with open("benchmark_results-gpdr-ats-rerun-12-26.csv", "r") as csvgpdrfile:
    reader = csv.DictReader(csvgpdrfile)
    for row in reader:
        key = (row["Example"], row["Mode"], row["Run Number"])
        gpdr_results[key] = row

with open("benchmark-results.csv", "r") as csvfile, open("benchmark-results-merged.csv", "w", newline="") as mergedfile:
    reader = csv.DictReader(csvfile)
    results = []
    for row in reader:
        key = (row["Example"], row["Mode"], row["Run Number"])
        if key in gpdr_results:
            results.append(gpdr_results[key])
        else:
            results.append(row)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(mergedfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)