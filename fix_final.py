import re
with open('README.md', encoding='utf-8') as f:
    d = f.read()
# Fix badges: for each star URL, add correct label based on project name
replacements = {
    'neohiro/ExploitProtection?style=flat)': 'neohiro/ExploitProtection?style=flat&label=%E2%AD%90%20ExploitProtection)',
    'neohiro/dnscrypt-proxy-gui?style=flat)': 'neohiro/dnscrypt-proxy-gui?style=flat&label=%E2%AD%90%20dnscrypt%20proxy%20GUI)',
    'neohiro/Cripple-NetStrip?style=flat)': 'neohiro/Cripple-NetStrip?style=flat&label=%E2%AD%90%20Cripple%20NetStrip)',
    'neohiro/auto-resume?style=flat)': 'neohiro/auto-resume?style=flat&label=%E2%AD%90%20auto-resume)',
    'neohiro/meteo-ics?style=flat)': 'neohiro/meteo-ics?style=flat&label=%E2%AD%90%20meteo-ics)',
    'neohiro/HoneyScan?style=flat)': 'neohiro/HoneyScan?style=flat&label=%E2%AD%90%20HoneyScan)',
    'neohiro/DNSLookup?style=flat)': 'neohiro/DNSLookup?style=flat&label=%E2%AD%90%20DNSLookup)',
    'neohiro/lora-multiboot?style=flat)': 'neohiro/lora-multiboot?style=flat&label=%E2%AD%90%20lora-multiboot)',
    'neohiro/windows?style=flat)': 'neohiro/windows?style=flat&label=%E2%AD%90%20windows)',
    'neohiro/linux?style=flat)': 'neohiro/linux?style=flat&label=%E2%AD%90%20linux)',
}
for old, new in replacements.items():
    d = d.replace(old, new)
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(d)
print('Fixed badges.')
