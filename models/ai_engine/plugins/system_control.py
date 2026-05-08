import subprocess, os, winreg
def launch(app): 
    try: os.startfile(app); return "launched"
    except Exception as e: return subprocess.Popen(app,shell=True).pid
def list_apps():
    apps=[]; 
    for h in [winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER]:
        try: k=winreg.OpenKey(h,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        except Exception as e: continue
        for i in range(winreg.QueryInfoKey(k)[0]):
            try: apps.append(winreg.EnumKey(k,i))
            except Exception as e: pass
    return apps[:50]
