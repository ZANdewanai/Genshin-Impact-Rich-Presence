import ast
files = [
    'core/sensors/base.py',
    'core/sensors/char_sensor.py',
    'core/sensors/location_sensor.py',
    'core/sensors/menu_sensor.py',
    'core/domain_handler.py',
    'core/shared_config.py',
]
for path in files:
    print('==== ', path)
    src = open(path).read()
    t = ast.parse(src)
    used = set()
    for node in ast.walk(t):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    for node in t.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                name = (a.asname or a.name.split('.')[0])
                print('  %-12s %s' % (name, 'USED' if name in used else 'UNUSED'))