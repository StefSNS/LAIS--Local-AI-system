import ast, shutil
def view(p): return open(p,'r',encoding='utf-8').read()
def propose_edit(p,code):
    s=p+".staging"; open(s,'w',encoding='utf-8').write(code)
    try: ast.parse(code); shutil.copy2(s,p); return "Applied - hot swapped"
    except SyntaxError as e: return f"Error {e} - staging saved"
