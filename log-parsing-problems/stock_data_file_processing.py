#  Stock Data File Processing - Daily Range Calculation
# Problem: You have a CSV file (stock_data.csv) containing daily stock price information. The columns are: Date, Ticker, Open, High, Low, Close, Volume.

# Example stock_data.csv:

# Date,Ticker,Open,High,Low,Close,Volume
# 2025-04-18,AAPL,170.50,172.80,170.10,172.50,55000000
# 2025-04-18,GOOG,140.10,141.50,139.80,141.20,25000000
# 2025-04-21,AAPL,172.60,173.50,171.90,173.00,48000000
# 2025-04-21,GOOG,141.30,142.00,140.50,140.80,22000000
# 2025-04-22,AAPL,173.10,175.00,172.80,174.90,61000000
# 2025-04-22,GOOG,140.90,141.20,139.50,139.90,28000000
# Task: Write a Python script that reads this file and performs the following for a specific stock ticker (e.g., AAPL):

# Calculate the daily price range (High - Low) for each day the ticker appears.

# Find the date with the largest price range for that ticker.

# Calculate the average trading volume for that ticker over the period present in the file.

# Output: Print the date with the largest range and the calculated average volume for the specified ticker.

# Example Output (for AAPL):

# Ticker: AAPL
# Date with largest price range: 2025-04-18 (Range: $2.70)
# Average daily volume: 54666666.67

import csv, os
from collections import defaultdict

def stock_daily_processing(path: str, ticker: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    daily_price_range_per_date = defaultdict(int)
    
    with open(path, newline="") as fd:
        reader = csv.DictReader(fd)
        count = 0
        vol = 0
        for row in reader:
            tick = row['Ticker']
            if tick.lower() == ticker.lower():
                date = row['Date']
                high = float(row['High'])
                low = float(row['Low'])
                range = high-low
                daily_price_range_per_date[date] = range
                # Calculate avg trading vol
                vol += float(row['Volume'])
                count += 1

    max_key = max(daily_price_range_per_date, key=daily_price_range_per_date.get)
    print(f"Ticker: {ticker}")
    print(f"Date with largest price range: {max_key} (Range: ${daily_price_range_per_date[max_key]:.2f})")
    if count: print(f"Average daily volume: {vol/count:.2f}")
                

stock_daily_processing("./stock_data_file_processing_file.csv", 'AAPL')
