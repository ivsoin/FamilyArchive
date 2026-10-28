import os

def export_project():
    output_filename = 'project_snapshot.txt'
    
    # 1. Collect all files to read
    files_to_read = []
    
    # - Python files in the root directory
    for f in sorted(os.listdir('.')):
        if os.path.isfile(f) and f.endswith('.py'):
            files_to_read.append(f)
            
    # - HTML files inside templates/
    templates_dir = 'templates'
    if os.path.exists(templates_dir):
        for root, dirs, files in os.walk(templates_dir):
            dirs.sort()
            for file in sorted(files):
                if file.endswith('.html'):
                    rel_path = os.path.join(root, file)
                    rel_path = rel_path.replace('\\', '/')
                    files_to_read.append(rel_path)
                    
    # - CSS and JS files inside static/
    static_dir = 'static'
    if os.path.exists(static_dir):
        for root, dirs, files in os.walk(static_dir):
            dirs.sort()
            for file in sorted(files):
                if file.endswith('.css') or file.endswith('.js'):
                    rel_path = os.path.join(root, file)
                    rel_path = rel_path.replace('\\', '/')
                    files_to_read.append(rel_path)
                    
    # 2. Write to project_snapshot.txt
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for filepath in files_to_read:
            # Skip reading project_snapshot.txt itself if it somehow got in
            if os.path.basename(filepath) == output_filename:
                continue
                
            ext = os.path.splitext(filepath)[1].lstrip('.')
            
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                continue
                
            outfile.write(f"### Файл: `{filepath}`\n")
            outfile.write(f"```{ext}\n")
            outfile.write(content)
            if not content.endswith('\n'):
                outfile.write('\n')
            outfile.write("```\n\n")
            
    print(f"Done! Project snapshot successfully saved to: {output_filename}")

if __name__ == '__main__':
    export_project()