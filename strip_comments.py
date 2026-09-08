import re
import os

files_to_clean = [
    "python/sheepdog/change_source.py",
    "python/sheepdog/audit.py",
    "python/sheepdog/maintenance.py",
    "python/sheepdog/intelligence.py",
    "python/sheepdog/knowledge.py",
    "python/sheepdog/github/trust_pr.py",
    "python/sheepdog/github/provisioning.py",
    "tests/test_knowledge.py",
    "tests/test_doctor.py",
    "tests/test_credential_scoping.py",
    "tests/test_git_trailers.py",
    "tests/test_workspace_activation.py"
]

for f in files_to_clean:
    with open(f, 'r') as fh:
        lines = fh.readlines()
    
    new_lines = []
    for line in lines:
        if line.lstrip().startswith('#') and not line.lstrip().startswith('# Copyright') and not line.lstrip().startswith('# SPDX-License-Identifier'):
            continue # drop pure comment lines (except license)
        if '#' in line and not line.lstrip().startswith('#'):
            # It's an inline comment. We need to be careful not to break `#` inside strings.
            # A simple hack: just split by `  # ` (with leading spaces) to catch most typical inline comments.
            if '  #' in line:
                line = line.split('  #')[0].rstrip() + '\n'
        new_lines.append(line)
        
    with open(f, 'w') as fh:
        fh.writelines(new_lines)
print("Comments stripped.")
