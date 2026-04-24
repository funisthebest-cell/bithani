import os
import re

BASE = "https://bithani.com"

def get_canonical(filepath):
    rel = filepath.replace("\\", "/")
    rel = rel.lstrip("./")
    if rel == "index.html":
        return BASE + "/"
    elif rel == "blog/index.html":
        return BASE + "/blog/"
    else:
        return BASE + "/" + rel

def add_canonical(filepath, url):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if 'rel="canonical"' in content:
        return "skip"

    canonical_tag = f'  <link rel="canonical" href="{url}" />'

    if 'name="robots"' in content:
        content = re.sub(
            r'(<meta name="robots"[^>]*>)',
            r'\1\n' + canonical_tag,
            content
        )
    else:
        content = content.replace("</head>", canonical_tag + "\n</head>", 1)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return "done"

targets = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in [".git", ".claude", "node_modules"]]
    for f in files:
        if f.endswith(".html"):
            path = os.path.join(root, f)
            path = path.replace(".\\", "").replace("./", "")
            targets.append(path)

done = skip = 0
for fp in sorted(targets):
    url = get_canonical(fp)
    result = add_canonical(fp, url)
    if result == "done":
        done += 1
        print(f"OK  {fp}")
    else:
        skip += 1

print(f"\ndone={done} skip={skip}")
