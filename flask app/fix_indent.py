# Script to fix indentation error in app.py
with open('app.py', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Fix indentation issue at line 3187
if len(lines) >= 3187 and '                postprocess(' in lines[3186]:
    lines[3186] = lines[3186].replace('                postprocess(', '            postprocess(')
    
# Fix indentation for the next few lines if needed
for i in range(3187, 3190):
    if i < len(lines) and lines[i].startswith('                '):
        lines[i] = '            ' + lines[i][16:]

with open('app_fixed.py', 'w', encoding='utf-8') as file:
    file.writelines(lines)

print("Fixed file written to app_fixed.py") 