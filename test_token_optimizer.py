"""Comprehensive validation of token optimization integration."""
import sys, json

sys.path.insert(0, r'C:\Users\stefa\Desktop\GitHub publish\models\ai_engine\unified_layer')
sys.path.insert(0, r'C:\Users\stefa\Desktop\GitHub publish\models\ai_engine')

from token_optimizer import get_token_optimizer, CompressionPipeline, ShellCompressor, TokenBudget, ResponseCache

results = {}

# 1. Compression Pipeline
cp = CompressionPipeline()
results['compressors'] = cp.available
assert len(results['compressors']) >= 2
text = '**Markdown** *content* with extra whitespace. ' * 50
cr = cp.compress(text)
results['compression_saved'] = cr['saved']
results['compression_method'] = cr['method']
print(f'  Compression pipeline: {cr["method"]} saved {cr["saved"]} tokens')

# 2. Shell Compressor
sc = ShellCompressor()
sh = 'Line A\n' * 200
sr = sc.compress(sh)
results['shell_sqz'] = sc._sqz_available
results['shell_saved'] = sr['saved']
assert sr['saved'] > 0
print(f'  Shell compressor: sqz={sc._sqz_available} saved {sr["saved"]}')

# 3. Cache (second call same content)
sr2 = sc.compress(sh)
results['cache_hit'] = sr2['method'] == 'cache_hit'
assert sr2['method'] == 'cache_hit'
print(f'  Cache: hit={sr2["method"]=="cache_hit"}')

# 4. Token Budget
tb = TokenBudget('test')
bt = tb.track(1000, 'gemini-2.5-flash')
results['budget_enabled'] = tb.enabled
results['budget_within'] = bt['within_budget']
assert bt['within_budget']
print(f'  Budget: enabled={tb.enabled} spent={bt["spent"]}')

# 5. Response Cache
rc = ResponseCache()
rc.put('key1', 'value1')
cv = rc.get('key1')
results['cache_works'] = cv == 'value1'
assert cv == 'value1'
print(f'  ResponseCache: works')

# 6. Backward-compatible API
opt = get_token_optimizer('test')
et = opt.estimate_tokens('hello world')
results['estimate_tokens'] = et > 0
assert et > 0
cb = opt.check_budget('hello world')
results['check_budget'] = cb['within_budget']
opt.log_usage('test', 100)
results['log_usage'] = True
print(f'  Backward API: estimate={et}, budget={cb["within_budget"]}')

# 7. optimize_context
ctx = opt.optimize_context([
    {'content': 'A'*500, 'score': 0.9},
    {'content': 'B'*500, 'score': 0.5}
], max_tokens=100)
results['optimize_context'] = len(ctx) > 0
print(f'  optimize_context: {len(ctx)} items')

# 8. compact_history
hist = opt.compact_history(
    [{'role': 'system', 'content': 'You are...'}] +
    [{'role': 'user', 'content': f'This is message number {i} with some extra content for token counting purposes. ' * 5} for i in range(20)],
    target_tokens=200
)
results['compact_history'] = len(hist) < 15
print(f'  compact_history: {len(hist)} messages (original 21)')

# 9. optimize_messages
msgs = [
    {'role': 'system', 'content': 'You are helpful. ' * 100},
    {'role': 'user', 'content': 'Hello. ' * 50}
]
opt_msgs = opt.optimize_messages(msgs)
results['optimize_messages'] = len(opt_msgs) == 2
print(f'  optimize_messages: {len(opt_msgs)} messages')

# 10. get_report
rpt = opt.get_report()
results['report_keys'] = list(rpt.keys())
assert 'agent' in rpt
print(f'  Report: {len(rpt["compressors"])} compressors, budget={rpt["budget"]["enabled"]}')

# 11. cmd_control integration check
with open(r'C:\Users\stefa\Desktop\GitHub publish\models\Mark-XXXV\actions\cmd_control.py', encoding='utf-8', errors='ignore') as f:
    src = f.read()
results['jarvis_cmd_patched'] = 'compress_shell' in src
assert 'compress_shell' in src
print(f'  JARVIS cmd_control: patched with compress_shell')

with open(r'C:\Users\stefa\Desktop\GitHub publish\models\ai_engine\plugins\cmd_control.py', encoding='utf-8', errors='ignore') as f:
    src2 = f.read()
results['engine_cmd_patched'] = 'compress_shell' in src2
assert 'compress_shell' in src2
print(f'  AI Engine cmd_control: patched with compress_shell')

# 12. UnifiedLayer loads token_optimizer
with open(r'C:\Users\stefa\Desktop\GitHub publish\models\ai_engine\unified_layer\__init__.py', encoding='utf-8', errors='ignore') as f:
    src3 = f.read()
results['unified_layer_loads'] = 'token_optimizer' in src3
print(f'  UnifiedLayer loads token_optimizer: {"token_optimizer" in src3}')

# 13. sqz binary exists
import os
results['sqz_binary'] = os.path.exists(r'C:\Users\stefa\Desktop\GitHub publish\models\ai_engine\lais-bin\sqz.exe')
print(f'  sqz binary: {results["sqz_binary"]}')

# Summary
passed = sum(1 for v in results.values() if isinstance(v, bool) and v)
failed = sum(1 for v in results.values() if isinstance(v, bool) and not v)
print(f'\n=== RESULTS: {passed} passed, {failed} failed, {len(results)} total ===')
for k, v in results.items():
    s = 'PASS' if (isinstance(v, bool) and v) or (not isinstance(v, bool) and v) else 'FAIL'
    print(f'  [{s}] {k}: {v}')
