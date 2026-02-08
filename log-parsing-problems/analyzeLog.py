
# You are given a multiline string containing application logs, where each line is in the format:
# "<timestamp>, <level>, <event_name>, user_id=<id>".

# Example:

# text
# 2025-10-30 09:15:12, INFO, user_login, user_id=123
# 2025-10-30 09:16:03, ERROR, payment_failed, user_id=456
# 2025-10-30 09:18:55, INFO, user_logout, user_id=123
# 2025-10-30 09:22:10, WARN, retry_payment, user_id=456
# 2025-10-30 09:30:11, INFO, user_login, user_id=999
# Write a function that:

# Parses the logs.

# Returns a dictionary with:

# log_counts: a mapping from log level (INFO, ERROR, WARN, etc.) to the number of occurrences.

# most_frequent_event: the event name that appears most frequently (e.g., user_login).

# For the input above, the function should return:

# python
# {
#   "log_counts": {"INFO": 3, "ERROR": 1, "WARN": 1},
#   "most_frequent_event": "user_login"
# }

from collections import defaultdict

def analyzeLog(input_data: str) -> dict:
    lines = input_data.strip().splitlines()
    log_counts = defaultdict(int)
    event_counts = defaultdict(int)
    most_frequent_event = ""

    for line in lines:
        if not line:
            continue
        parts = [p.strip() for p in line.split(',')]
        _, log_level, event = parts[0], parts[1], parts[2]
        log_counts[log_level] += 1
        event_counts[event] += 1

        most_frequent_event = max(event_counts, key=event_counts.get)

    return {"log_counts": dict(log_counts), "most_frequent_event": most_frequent_event}

def new_func(log_counts):
    return dict(log_counts)

if __name__ == '__main__':
    input_data = """
    2025-10-30 09:15:12, INFO, user_login, user_id=123
    2025-10-30 09:16:03, ERROR, payment_failed, user_id=456
    2025-10-30 09:18:55, INFO, user_logout, user_id=123
    2025-10-30 09:22:10, WARN, retry_payment, user_id=456
    2025-10-30 09:30:11, INFO, user_login, user_id=999
    """

    print(analyzeLog(input_data))