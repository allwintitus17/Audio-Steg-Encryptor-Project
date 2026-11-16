"""Entry point for the Audio Cryptography & Steganography Desktop Application."""

import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import AudioStegoApp

def main():
    app = AudioStegoApp()
    app.mainloop()

if __name__ == "__main__":
    main()
