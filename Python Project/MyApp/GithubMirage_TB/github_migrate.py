import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import datetime


class GitHubMigratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repository Migrator")
        self.root.geometry("900x650")
        self.root.configure(bg="#2b2b2b")

        self.current_directory = tk.StringVar(value=os.getcwd())
        self.current_remote_var = tk.StringVar()
        self.new_remote_var = tk.StringVar()

        self.setup_ui()
        self.detect_current_git()

    # ================= UI =================

    def setup_ui(self):
        main = tk.Frame(self.root, bg="#2b2b2b")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main, text="Working Directory",
                 bg="#2b2b2b", fg="#ffa726",
                 font=("Arial", 12, "bold")).pack(anchor="w")

        dir_frame = tk.Frame(main, bg="#2b2b2b")
        dir_frame.pack(fill="x", pady=5)

        tk.Entry(dir_frame, textvariable=self.current_directory,
                 bg="#3c3c3c", fg="white",
                 insertbackground="white").pack(side="left", fill="x", expand=True)

        tk.Button(dir_frame, text="Browse",
                  command=self.browse_directory).pack(side="right")

        tk.Label(main, text="Current Remote",
                 bg="#2b2b2b", fg="#61dafb",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 0))

        tk.Entry(main, textvariable=self.current_remote_var,
                 state="readonly",
                 bg="#3c3c3c", fg="#cccccc").pack(fill="x")

        tk.Label(main, text="New Remote URL",
                 bg="#2b2b2b", fg="#4CAF50",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 0))

        tk.Entry(main, textvariable=self.new_remote_var,
                 bg="#3c3c3c", fg="white",
                 insertbackground="white").pack(fill="x")

        tk.Button(main, text="START MIGRATION",
                  bg="#4CAF50", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.start_migration).pack(pady=15)

        self.console = scrolledtext.ScrolledText(
            main, bg="#1e1e1e", fg="#cccccc", height=15)
        self.console.pack(fill="both", expand=True)

        self.status = tk.Label(self.root, text="Ready",
                               bg="#1e1e1e", fg="#61dafb",
                               anchor="w")
        self.status.pack(fill="x")

    # ================= Helper =================

    def log(self, msg):
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.root.update()

    def update_status(self, msg):
        self.status.config(text=msg)
        self.root.update()

    def browse_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_directory.set(folder)
            self.detect_current_git()

    # ================= Git Detection =================

    def detect_current_git(self):
        repo = self.current_directory.get()
        git_dir = os.path.join(repo, ".git")

        if not os.path.exists(git_dir):
            self.current_remote_var.set("No Git repository found")
            return

        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            cwd=repo
        )

        if result.stdout:
            first_line = result.stdout.split("\n")[0]
            parts = first_line.split()
            if len(parts) > 1:
                self.current_remote_var.set(parts[1])
        else:
            self.current_remote_var.set("No remote configured")

    # ================= Core Logic =================

    def run_git(self, command):
        repo = self.current_directory.get()
        self.log("$ " + " ".join(command))

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=repo
        )

        if result.stdout:
            self.log(result.stdout.strip())

        if result.stderr:
            self.log(result.stderr.strip())

        return result.returncode == 0

    def migrate(self):
        repo = self.current_directory.get()
        new_url = self.new_remote_var.get().strip()

        if not os.path.exists(os.path.join(repo, ".git")):
            messagebox.showerror("Error", "No Git repository found.")
            return

        if not new_url.startswith("http") and not new_url.startswith("git@"):
            messagebox.showerror("Error", "Invalid Git URL.")
            return

        self.console.delete(1.0, tk.END)
        self.log("=" * 50)
        self.log("GIT MIGRATION STARTED")
        self.log("Time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.log("New URL: " + new_url)
        self.log("=" * 50)

        # Kiểm tra remote
        result = subprocess.run(
            ["git", "remote"],
            capture_output=True,
            text=True,
            cwd=repo
        )

        remotes = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if "origin" in remotes:
            self.log("Changing origin URL...")
            success = self.run_git(["git", "remote", "set-url", "origin", new_url])
        else:
            if remotes:
                self.log("Removing existing remote...")
                self.run_git(["git", "remote", "remove", remotes[0]])

            self.log("Adding new origin...")
            success = self.run_git(["git", "remote", "add", "origin", new_url])

        if not success:
            self.update_status("Migration failed")
            return

        self.log("Pushing to new remote...")
        self.run_git(["git", "push", "-u", "origin", "--all"])

        self.current_remote_var.set(new_url)

        self.log("Migration completed successfully!")
        self.update_status("Migration completed successfully")

        messagebox.showinfo("Success", "Git remote changed successfully!")

    # ================= Thread =================

    def start_migration(self):
        thread = threading.Thread(target=self.migrate)
        thread.daemon = True
        thread.start()


# ================= MAIN =================

def main():
    try:
        subprocess.run(["git", "--version"], check=True)
    except:
        print("Git not installed.")
        sys.exit(1)

    root = tk.Tk()
    app = GitHubMigratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()