import os
import ast
import sys

def get_imports(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception:
            return set()
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Handle relative imports gracefully
                if node.level > 0:
                    continue
                imports.add(node.module.split('.')[0])
    return imports

def main():
    root_dirs = ["edith", "tests", "scripts"]
    all_imports = set()
    for d in root_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith(".py"):
                    imports = get_imports(os.path.join(root, f))
                    all_imports.update(imports)
    
    # Filter standard library
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()
    external_imports = all_imports - stdlib
    print("External Imports:")
    for imp in sorted(external_imports):
        if imp not in ["edith"]: # ignore internal package
            print(imp)

if __name__ == "__main__":
    main()
