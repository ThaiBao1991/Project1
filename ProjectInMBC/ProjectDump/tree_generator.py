import os

def generate_directory_tree(project_path, exclude_dirs):
    tree_lines = []
    project_name = os.path.basename(project_path.rstrip(os.sep))
    tree_lines.append(f"{project_name}/")
    
    def add_directory_content(current_path, prefix=""):
        try:
            items = sorted(os.listdir(current_path))
            dirs = [item for item in items if os.path.isdir(os.path.join(current_path, item))]
            files = [item for item in items if os.path.isfile(os.path.join(current_path, item))]
            
            # Hiển thị thư mục
            for i, dirname in enumerate(dirs):
                is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                
                # Kiểm tra xem có phải thư mục thư viện không
                if dirname.lower() in exclude_dirs:
                    tree_lines.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dirname}/")
                    continue  # Không duyệt vào bên trong thư mục thư viện
                else:
                    tree_lines.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dirname}/")
                    next_prefix = prefix + ("    " if is_last_dir else "│   ")
                    add_directory_content(os.path.join(current_path, dirname), next_prefix)
            
            # Hiển thị files
            for i, filename in enumerate(files):
                is_last = i == len(files) - 1
                tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{filename}")
                
        except PermissionError:
            tree_lines.append(f"{prefix}├── [Permission Denied]")
    
    add_directory_content(project_path)
    return "\n".join(tree_lines)