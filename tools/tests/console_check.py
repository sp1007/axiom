import sys
import ctypes
import subprocess
import time
import os

kernel32 = ctypes.windll.kernel32

def main():
    if len(sys.argv) < 3:
        print("Usage: console_check.py <exe> <expected_text>")
        sys.exit(1)

    exe = sys.argv[1]
    expected_text = sys.argv[2]

    # Free existing console and allocate a new one to be sure
    kernel32.FreeConsole()
    time.sleep(0.1)
    if not kernel32.AllocConsole():
        err = ctypes.GetLastError()
        print(f"SKIP: Could not allocate console, err={err}")
        sys.exit(0)
    
    try:
        # Get console screen buffer
        h_out = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
        if h_out == -1 or h_out == 0:
            print("SKIP: GetStdHandle failed")
            sys.exit(0)
        
        # Save current code page
        orig_cp = kernel32.GetConsoleOutputCP()

        # Run process
        # Popen without CREATE_NEW_CONSOLE inherits our console
        proc = subprocess.Popen([exe], stdout=None, stderr=None)
        proc.wait()

        # Check code page is restored
        new_cp = kernel32.GetConsoleOutputCP()
        if new_cp != orig_cp:
            print(f"FAIL: Code page not restored (was {orig_cp}, now {new_cp})")
            sys.exit(1)

        # Read screen buffer
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        buf = ctypes.create_unicode_buffer(1024)
        chars_read = ctypes.c_uint32()
        coord = COORD(0, 0)

        res = kernel32.ReadConsoleOutputCharacterW(h_out, buf, 1024, coord, ctypes.byref(chars_read))
        if not res:
            err = ctypes.GetLastError()
            print(f"FAIL: ReadConsoleOutputCharacterW failed with err={err}")
            sys.exit(1)

        screen_text = buf.value[:chars_read.value]
        
        # Check if expected text is in screen_text
        if expected_text not in screen_text:
            print(f"FAIL: Expected '{expected_text}' not found in console output:")
            print(repr(screen_text))
            sys.exit(1)

        print("PASS")
    finally:
        kernel32.FreeConsole()

if __name__ == "__main__":
    main()
