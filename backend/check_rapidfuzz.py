import sys
try:
    import rapidfuzz
    print("rapidfuzz_ok:" + rapidfuzz.__version__)
except ImportError:
    print("rapidfuzz_missing")
