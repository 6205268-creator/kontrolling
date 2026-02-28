from app.main import app

with open('routes_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'Routes: {len(app.routes)}\n')
    for r in app.routes:
        if hasattr(r, 'path'):
            f.write(f'  {r.path}\n')

print('Done! Check routes_output.txt')
