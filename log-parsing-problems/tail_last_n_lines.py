# For given Large input file, return the last n lines of a large file without reading the entire file into memory.
# tail -n functionality

# def tail_n_lines(file_path: str, n: int) -> List[str]:
#     """
#     Return the last `n` lines from a very large file without loading the entire file into memory.
#     """
#     pass
# Input:

# logfile.txt with millions of lines
# Output:

# ["line n-9", "line n-8", ..., "line n"]
from collections import deque

def tail_n_lines(file_path: str, n: int) -> list[str]:
    with open(file_path, "r") as fd:
        return list(deque(fd, maxlen=n))
    
res = tail_n_lines("./filemetadataAnalysis_file.txt", 3)
for line in res:
    print(line, end="")