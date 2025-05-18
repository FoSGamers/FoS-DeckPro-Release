import os

# Define the filenames in the correct order
parts = [
    "install_fosbot_part1.py",
    "install_fosbot_part2.py",
    "install_fosbot_part3.py",
    "install_fosbot_part4.py",
    "install_fosbot_part5.py"
]

# Output file
output_filename = "install_fosbot.py"

# Combine the parts
with open(output_filename, "w") as outfile:
    for part in parts:
        if not os.path.exists(part):
            print(f"[ERROR] Missing file: {part}")
            continue
        with open(part, "r") as infile:
            outfile.write(infile.read())
            outfile.write("\n")  # Ensure separation between files

print(f"✅ Combined into {output_filename}")
