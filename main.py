"""货运台账解析器 - 主入口"""
import sys
import os

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from gui import main

if __name__ == "__main__":
    main()
