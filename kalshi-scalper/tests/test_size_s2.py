import sys
sys.path.insert(0, "src")
from scalper import size_s2 as T

assert T.next_size("FLAT9", 9, True) == 9 and T.next_size("HALF", 4, False) == 4
assert T.next_size("STEP_DOWN", 9, True) == 8 and T.next_size("STEP_DOWN", 2, True) == 2 and T.next_size("STEP_DOWN", 3, False) == 9
assert T.next_size("STEP_UP", 3, True) == 4 and T.next_size("STEP_UP", 9, True) == 9 and T.next_size("STEP_UP", 7, False) == 3
print("ok")
