# File Metadata Analysis (Inspired by "Dinosaur Problem" Concept)
# Concept: This question involves processing structured data, categorizing items, and performing aggregations, similar to how one might analyze a large dataset with various attributes (like the conceptual "dinosaur problem" often attributed to Meta interviews which involves handling large datasets/filtering/grouping).

# Problem: You are given a file (files.txt) where each line represents a file entry with its path, size in bytes, and last modified timestamp (Unix epoch). The format is comma-separated: filepath,size,modified_timestamp.

# Example files.txt:

# /var/log/app.log,10240,1678886400
# /home/user/data.csv,51200,1678886460
# /etc/config.xml,1024,1678800000
# /var/log/kernel.log,20480,1678890000
# /home/user/report.pdf,204800,1678886520
# /home/user/archive.zip,1024000,1678790000
# /var/log/sys.log,15360,1678890060
# Task: Write a Python script that reads this file and calculates the total size of files for each file extension type (e.g., .log, .csv, .xml, .pdf, .zip). Ignore files with no extension.

# Output: Print the total size for each extension found. The output should be clear, like:

# log: 46080 bytes
# csv: 51200 bytes
# xml: 1024 bytes
# pdf: 204800 bytes
# zip: 1024000 bytes

import os

def file_analysis(filePath: str) -> dict:
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"File not found: {filePath}")
    
    res = {}
    
    with open(filePath, 'r') as fd:
        for line in fd:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            path, size = parts[0], int(parts[1])
            if '.' in path:
                ext = path.split('.')[-1]
                res[ext] = res.get(ext, 0) + size
    return res

if __name__ == '__main__':
    res = file_analysis('./filemetadataAnalysis_file.txt')
    for k, v in res.items():
        print(f"{k}: {v} bytes")
