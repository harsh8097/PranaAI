import os
import shutil

def build_static():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    public_dir = os.path.join(base_dir, "public")
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(os.path.join(public_dir, "static"), exist_ok=True)

    # Read template index.html
    template_path = os.path.join(base_dir, "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace Flask url_for calls with static relative links
    html_static = html.replace("{{ url_for('static', filename='styles.css') }}", "static/styles.css")
    html_static = html_static.replace("{{ url_for('static', filename='script.js') }}", "static/script.js")

    # Write public/index.html
    with open(os.path.join(public_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_static)

    # Write root index.html as fallback for root Netlify deploys
    with open(os.path.join(base_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_static)

    # Copy styles and scripts to public/static and public/
    static_src = os.path.join(base_dir, "static")
    for fname in ["styles.css", "script.js"]:
        src = os.path.join(static_src, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(public_dir, "static", fname))
            shutil.copy2(src, os.path.join(public_dir, fname))

    print(f"Static build complete! Output generated in {public_dir} and {base_dir}/index.html")

if __name__ == "__main__":
    build_static()
