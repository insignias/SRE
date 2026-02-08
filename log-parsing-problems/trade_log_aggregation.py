# Trade Log Aggregation
# Problem: You are provided with a trade log file (tradelog.csv) in CSV (Comma-Separated Values) format.

# The columns are: date, process, host, log, bytes.

# The exchange name (e.g., 'cme', 'lse') is part of the process name string.

# Sample tradelog.csv file content:

# Also test your code for this unordered column i.e modify the code to parse different column order eg. (date, process, host, log,bytes) => (process, date, log, bytes, host) as well

# date,process,host,log,bytes
# 20140206,cme_trader_2,ny-host-01,0345-cme_trader_2.log.gz,1500
# 20140206,lse_orderrouter_1,ln-host-a,1120-lse_orderrouter_1.log.gz,800
# 20140206,cme_trader_2,ny-host-01,0346-cme_trader_2.log.gz,500
# 20140207,cme_feedhandler_1,ny-host-02,0900-cme_feedhandler_1.log.gz,2500
# 20140207,lse_orderrouter_1,ln-host-b,1305-lse_orderrouter_1.log.gz,1200
# 20140207,cme_trader_1,ny-host-03,1015-cme_trader_1.log.gz,1800
# 20140207,lse_feedhandler_1,ln-host-a,1400-lse_feedhandler_1.log.gz,100
# Task: Write a Python script to process this log file and calculate:

# The total number of bytes processed per day, order by date ascending

# The total number of bytes processed per exchange, per day, order by date ascending

# Output: Print the results clearly. A nested dictionary or formatted print statements are acceptable.

# Example Output Structure (based on the sample data above):

# Daily Totals:
# 20140206: 2800 bytes
# 20140207: 5600 bytes

# Exchange Daily Totals:
# 20140206, cme, 2000 bytes
# 20140206, lse, 800 bytes
# 20140207, cme, 4300 bytes
# 20140207, lse, 1300 bytes

import csv, os
from collections import defaultdict

def trade_log_aggregation(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found error: {path}")
    
    daily_totals = defaultdict(int)
    exchange_daily_totals = defaultdict(lambda: defaultdict(int))
    
    with open(path, newline="") as fd:
        reader = csv.DictReader(fd)  # Use DictReader for flexible column order
        for row in reader:
            date = row['date']
            process = row['process']
            bytes_val = int(row['bytes'])
            
            daily_totals[date] += bytes_val
            exchange = process.split('_')[0]
            exchange_daily_totals[date][exchange] += bytes_val
    
    # Sort by date (key), not by value
    daily_totals = dict(sorted(daily_totals.items()))
    exchange_daily_totals = dict(sorted(exchange_daily_totals.items()))
    return {"daily_totals": daily_totals, "exchange_daily_totals": exchange_daily_totals}

cwd = os.getcwd()
file_path = os.path.join(cwd, "trade_log_aggregation_file.csv")
result = trade_log_aggregation(file_path)
daily_totals = result["daily_totals"]
exchange_daily_totals = result["exchange_daily_totals"]
print("Daily Totals:")
for k, v in daily_totals.items():
    print(f"{k}: {v} bytes")

print()
print("Exchange Daily Totals:")
for k, v in exchange_daily_totals.items():
    for exchange, val in v.items():
        print(f"{k}, {exchange}, {val} bytes")