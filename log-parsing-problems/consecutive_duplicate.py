# Mimic uniq -c in Python
# Goal: Return the count of consecutive duplicate lines.

# def uniq_count(file_path: str) -> List[str]:
#     """
#     Return a list of lines with their consecutive occurrence counts,
#     similar to the Unix `uniq -c` command.
#     """
#     pass
# Input (file content):

# apple
# apple
# banana
# banana
# banana
# apple
# Output:

# ['2 apple', '3 banana', '1 apple']

from collections import defaultdict

def uniq_count(file_path: str) -> list[str]:
    count = defaultdict(int)
    res = []
    prev = ''
    with open(file_path) as fd:
        for line in fd:
            line = line.strip()
            if line:
                if (line != prev and line in count):
                    res.extend([f"{v} {k}" for k, v in count.items()])
                    count = defaultdict(int)
                count[line] += 1
                prev = line
  
    res.extend([f"{v} {k}" for k, v in count.items()])
    return res

print(uniq_count("./consecutive_duplicate_file.txt"))