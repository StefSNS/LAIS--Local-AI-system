with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Print lines around 264 to see the problem
for i, line in enumerate(lines[258:275], start=259):
    print(f"{i}: {repr(line)}")
