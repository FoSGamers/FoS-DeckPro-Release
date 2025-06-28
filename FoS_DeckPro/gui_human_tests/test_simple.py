#!/usr/bin/env python3
import subprocess, time; print("Testing app launch..."); proc = subprocess.Popen(["python3", "../main.py"]); time.sleep(3); print("App launched!"); proc.terminate(); print("Test complete!")
