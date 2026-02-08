# Top N IPs by Request Count
# Goal: Return top N IPs from a large Nginx access log file.

# def top_n_ips(file_path: str, n: int) -> List[str]:
#     """
#     Return the top `n` IP addresses that appear most frequently in the file.
#     """
#     pass
# Input Format (CLF):

# 123.45.67.89 - - [10/Oct/2023:13:55:36 +0000] "GET /api/user HTTP/1.1" 200 532
# Output:

# ['123.45.67.89', '98.76.54.32']
import re
from collections import defaultdict
from operator import itemgetter

def top_n_ips(path: str) -> None:
    pattern = r'^(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})'
    count_ip = defaultdict(int)
    res = []
    with open(path) as fd:
        for line in fd:
            match = re.search(pattern, line)
            if match:
                ip = match.group(1)
                count_ip[ip] += 1
    
    count_ip = dict(sorted(count_ip.items(), key=itemgetter(1), reverse=True))

    count = 0
    for k,v in count_ip.items():
        count += 1
        res.extend([k])
        if count > 2:
            break

    print(res)

top_n_ips("./nginx-log-file-analysis-file.log")