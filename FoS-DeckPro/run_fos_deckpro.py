import sys
import os

# Ensure the FoS_DeckPro package is on the path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'FoS_DeckPro')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from FoS_DeckPro import main
    if hasattr(main, 'main'):
        main.main()
    else:
        # Fallback: run as script
        exec(open(os.path.join(src_path, 'main.py')).read())
except ImportError as e:
    missing = str(e).split('No module named ')[-1].replace("'", "")
    print(f"\n[ERROR] Missing dependency: {missing}\n")
    print("To fix: Run 'pip install -r FoS-DeckPro/requirements.txt' from your project root.")
    sys.exit(1) 