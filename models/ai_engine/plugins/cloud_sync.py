import shutil, json
def sync():
    t=json.load(open("config.json"))["sync_folder"]; shutil.copytree(".",t,dirs_exist_ok=True,ignore=shutil.ignore_patterns("models","__pycache__")); return f"Synced to {t}"
