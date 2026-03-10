"""Clean Architecture validation script."""
import os
import re
from pathlib import Path


def check_domain_layer():
    """Check domain layer for forbidden imports."""
    violations = []
    domain_files = []
    
    for dirpath, _, filenames in os.walk('app/modules'):
        if '\\domain\\' in dirpath or dirpath.endswith('\\domain'):
            for fn in filenames:
                if fn.endswith('.py'):
                    fp = os.path.join(dirpath, fn)
                    domain_files.append(fp)
                    with open(fp, 'r', encoding='utf-8') as f:
                        content = f.read()
                    forbidden = ['fastapi', 'sqlalchemy', 'pydantic']
                    for fb in forbidden:
                        if re.search(rf'import {fb}|from {fb}', content):
                            violations.append(f'{fp}: {fb}')
    
    return len(domain_files), violations

def check_module_structure():
    """Check that all modules have correct structure."""
    required_dirs = ['domain', 'application', 'infrastructure', 'api']
    modules = []
    missing = []
    
    modules_path = Path('app/modules')
    for item in modules_path.iterdir():
        if item.is_dir() and item.name not in ['shared', '__pycache__']:
            modules.append(item.name)
            for req in required_dirs:
                if not (item / req).exists():
                    missing.append(f'{item.name}/{req}')
    
    return modules, missing

if __name__ == '__main__':
    print('=' * 60)
    print('CLEAN ARCHITECTURE VALIDATION')
    print('=' * 60)
    
    # Check domain layer
    count, violations = check_domain_layer()
    print(f'\n1. Domain Layer Check ({count} files)')
    if violations:
        print('   FAIL - VIOLATIONS:')
        for v in violations:
            print(f'      {v}')
    else:
        print('   PASS - No forbidden imports (fastapi, sqlalchemy, pydantic)')
    
    # Check module structure
    modules, missing = check_module_structure()
    print(f'\n2. Module Structure Check ({len(modules)} modules)')
    print(f'   Modules: {", ".join(modules)}')
    if missing:
        print('   FAIL - MISSING:')
        for m in missing:
            print(f'      {m}')
    else:
        print('   PASS - All modules have domain/application/infrastructure/api')
    
    # Summary
    print('\n' + '=' * 60)
    if not violations and not missing:
        print('ALL CHECKS PASSED')
    else:
        print('SOME CHECKS FAILED')
    print('=' * 60)
