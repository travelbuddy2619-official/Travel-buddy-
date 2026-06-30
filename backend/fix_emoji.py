import re

with open('app/agents/orchestrator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    try:
        line.encode('cp1252')
        fixed_lines.append(line)
    except UnicodeEncodeError:
        # Line has emoji or non-cp1252 chars — convert to logger.debug with ASCII only
        ascii_line = line.encode('ascii', errors='ignore').decode('ascii')
        # If it was a print(...) statement, convert to logger.debug
        stripped = ascii_line.strip()
        if stripped.startswith('print('):
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + 'logger.debug(' + stripped[6:] + '\n'
            fixed_lines.append(new_line)
        else:
            fixed_lines.append(ascii_line)

with open('app/agents/orchestrator.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('Done - fixed', sum(1 for l in lines if not l.encode('utf-8').decode('ascii', errors='ignore') == l.encode('utf-8').decode('utf-8')), 'problematic lines')
