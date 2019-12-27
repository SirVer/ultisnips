# Some constants for better reading
BS = "\x7f"
ESC = "\x1b"
ARR_L = "\x1bOD"
ARR_R = "\x1bOC"
ARR_U = "\x1bOA"
ARR_D = "\x1bOB"

# multi-key sequences generating a single key press
SEQUENCES = [ARR_L, ARR_R, ARR_U, ARR_D]

# Defined Constants
JF = "?"  # Jump forwards
JB = "+"  # Jump backwards
LS = "@"  # List snippets
EX = "\t"  # EXPAND
EA = "#"  # Expand anonymous

COMPL_KW = chr(24) + chr(14)
COMPL_ACCEPT = chr(25)
