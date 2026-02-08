# Nginx Log File Analysis
# Problem: You are given a sample Nginx access log file (access.log). The format is the standard combined log format.

# Example access.log:

# 192.168.1.101 - - [21/Apr/2025:10:05:15 +0100] "GET /index.html HTTP/1.1" 200 512 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# 192.168.1.102 - - [21/Apr/2025:10:05:20 +0100] "GET /styles/main.css HTTP/1.1" 200 1024 "http://example.com/index.html" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
# 192.168.1.101 - - [21/Apr/2025:10:05:21 +0100] "GET /images/logo.png HTTP/1.1" 200 2048 "http://example.com/index.html" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# 192.168.1.103 - - [21/Apr/2025:10:06:05 +0100] "GET /products/item1 HTTP/1.1" 200 1800 "-" "Chrome/110.0.0.0"
# 192.168.1.104 - - [21/Apr/2025:10:06:30 +0100] "GET /nonexistentpage HTTP/1.1" 404 150 "-" "Firefox/109.0"
# 192.168.1.101 - - [21/Apr/2025:10:07:00 +0100] "POST /api/submit HTTP/1.1" 201 50 "http://example.com/form.html" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# 192.168.1.102 - - [21/Apr/2025:10:07:15 +0100] "GET /index.html HTTP/1.1" 304 0 "-" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
# Task: Write a Python script to parse this log file and determine:

# The count of each HTTP status code (e.g., 200, 404, 304, 201).

# The top 3 most requested resource paths (the part between the HTTP method and the HTTP version, e.g., /index.html, /styles/main.css). Ignore query parameters if present.

# Output: Print the status code counts and the top 3 requested paths with their counts.

# Example Output:

# Status Code Counts:
# 200: 3
# 404: 1
# 201: 1
# 304: 1

# Top 3 Requested Paths:
# /index.html: 2
# /styles/main.css: 1
# /images/logo.png: 1
import os
from collections import defaultdict, Counter
import re
from operator import itemgetter

def nginx_log_file_analysis(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    count_status = defaultdict(int)
    requested_resource_path = defaultdict(int)
    pattern = r'"[A-Z]+\s+(\S+)\s+HTTP/[\d.]+" (\d{3})'
    # pattern = r'"[A-Z]+\s+(\S+)\s+HTTP/[\d.]+" (\d{3})'

    with open(path) as fd:
        for line in fd:
            if line:
                match = re.search(pattern, line)
                path = match.group(1)
                status = match.group(2)
                count_status[status] += 1
                requested_resource_path[path] += 1
    
    requested_resource_path = dict(sorted(requested_resource_path.items(), key=itemgetter(1), reverse=True))

    print("Status Code Counts:")
    for k, v in count_status.items():
        print(f"{k}: {v}")
    
    print("\nTop 3 Requested Paths:")
    count = 0
    for k, v in requested_resource_path.items():
        count += 1
        print(f"{k} {v}")
        if count == 3:
            break

nginx_log_file_analysis("./nginx-log-file-analysis-file.log")