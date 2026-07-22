import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import PyPDF2
from datetime import datetime

class PDFPasswordProtector:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Password Tool - Protect & Unprotect PDFs")
        self.root.geometry("750x700")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Khởi tạo biến trước
        self.show_password_single = tk.BooleanVar(value=False)
        self.show_password_folder = tk.BooleanVar(value=False)
        self.show_password_unprotect_single = tk.BooleanVar(value=False)
        self.show_password_unprotect_folder = tk.BooleanVar(value=False)
        
        # Main container
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.single_file_tab = ttk.Frame(self.notebook)
        self.folder_tab = ttk.Frame(self.notebook)
        self.unprotect_single_tab = ttk.Frame(self.notebook)
        self.unprotect_folder_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.single_file_tab, text="🔒 Protect Single File")
        self.notebook.add(self.folder_tab, text="🔒 Protect Folder")
        self.notebook.add(self.unprotect_single_tab, text="🔓 Unprotect Single File")
        self.notebook.add(self.unprotect_folder_tab, text="🔓 Unprotect Folder")
        
        # Setup tabs
        self.setup_single_file_tab()
        self.setup_folder_tab()
        self.setup_unprotect_single_tab()
        self.setup_unprotect_folder_tab()
        
        # Log area
        self.setup_log_area()
        
    def setup_single_file_tab(self):
        # File selection
        ttk.Label(self.single_file_tab, text="Select PDF File:").grid(row=0, column=0, sticky='w', pady=5)
        self.single_file_path = tk.StringVar()
        ttk.Entry(self.single_file_tab, textvariable=self.single_file_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.single_file_tab, text="Browse", command=self.browse_single_file).grid(row=0, column=2)
        
        # Output directory
        ttk.Label(self.single_file_tab, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.single_output_path = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(self.single_file_tab, textvariable=self.single_output_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.single_file_tab, text="Browse", command=self.browse_single_output).grid(row=1, column=2)
        
        # Password
        ttk.Label(self.single_file_tab, text="Password to Set:").grid(row=2, column=0, sticky='w', pady=5)
        self.single_password = tk.StringVar()
        self.single_password_entry = ttk.Entry(self.single_file_tab, textvariable=self.single_password, width=50, show="*")
        self.single_password_entry.grid(row=2, column=1, padx=5)
        
        # Show password checkbox
        ttk.Checkbutton(self.single_file_tab, text="Show Password", 
                       variable=self.show_password_single,
                       command=lambda: self.toggle_password_visibility(self.single_password_entry, self.show_password_single)).grid(row=3, column=1, sticky='w')
        
        # New filename
        ttk.Label(self.single_file_tab, text="New Filename:").grid(row=4, column=0, sticky='w', pady=5)
        self.single_new_filename = tk.StringVar()
        ttk.Entry(self.single_file_tab, textvariable=self.single_new_filename, width=50).grid(row=4, column=1, padx=5)
        ttk.Label(self.single_file_tab, text="(Leave empty to keep original name)").grid(row=5, column=1, sticky='w')
        
        # Start button
        self.single_start_btn = ttk.Button(self.single_file_tab, text="Start Protecting", command=self.start_single_file)
        self.single_start_btn.grid(row=6, column=1, pady=20)
        
        # Progress bar
        self.single_progress = ttk.Progressbar(self.single_file_tab, length=400, mode='determinate')
        self.single_progress.grid(row=7, column=1, pady=10)
        
    def setup_folder_tab(self):
        # Folder selection
        ttk.Label(self.folder_tab, text="Select Folder:").grid(row=0, column=0, sticky='w', pady=5)
        self.folder_path = tk.StringVar()
        ttk.Entry(self.folder_tab, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.folder_tab, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        
        # Output directory
        ttk.Label(self.folder_tab, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.folder_output_path = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(self.folder_tab, textvariable=self.folder_output_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.folder_tab, text="Browse", command=self.browse_folder_output).grid(row=1, column=2)
        
        # Password
        ttk.Label(self.folder_tab, text="Password to Set:").grid(row=2, column=0, sticky='w', pady=5)
        self.folder_password = tk.StringVar()
        self.folder_password_entry = ttk.Entry(self.folder_tab, textvariable=self.folder_password, width=50, show="*")
        self.folder_password_entry.grid(row=2, column=1, padx=5)
        
        # Show password checkbox
        ttk.Checkbutton(self.folder_tab, text="Show Password", 
                       variable=self.show_password_folder,
                       command=lambda: self.toggle_password_visibility(self.folder_password_entry, self.show_password_folder)).grid(row=3, column=1, sticky='w')
        
        # Start button
        self.folder_start_btn = ttk.Button(self.folder_tab, text="Start Protecting", command=self.start_folder)
        self.folder_start_btn.grid(row=4, column=1, pady=20)
        
        # Progress bar
        self.folder_progress = ttk.Progressbar(self.folder_tab, length=400, mode='determinate')
        self.folder_progress.grid(row=5, column=1, pady=10)
        
    def setup_unprotect_single_tab(self):
        # File selection
        ttk.Label(self.unprotect_single_tab, text="Select Password Protected PDF:").grid(row=0, column=0, sticky='w', pady=5)
        self.unprotect_single_file_path = tk.StringVar()
        ttk.Entry(self.unprotect_single_tab, textvariable=self.unprotect_single_file_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.unprotect_single_tab, text="Browse", command=self.browse_unprotect_single_file).grid(row=0, column=2)
        
        # Output directory
        ttk.Label(self.unprotect_single_tab, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.unprotect_single_output_path = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(self.unprotect_single_tab, textvariable=self.unprotect_single_output_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.unprotect_single_tab, text="Browse", command=self.browse_unprotect_single_output).grid(row=1, column=2)
        
        # Password
        ttk.Label(self.unprotect_single_tab, text="PDF Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.unprotect_single_password = tk.StringVar()
        self.unprotect_single_password_entry = ttk.Entry(self.unprotect_single_tab, textvariable=self.unprotect_single_password, width=50, show="*")
        self.unprotect_single_password_entry.grid(row=2, column=1, padx=5)
        
        # Show password checkbox
        ttk.Checkbutton(self.unprotect_single_tab, text="Show Password", 
                       variable=self.show_password_unprotect_single,
                       command=lambda: self.toggle_password_visibility(self.unprotect_single_password_entry, self.show_password_unprotect_single)).grid(row=3, column=1, sticky='w')
        
        # New filename
        ttk.Label(self.unprotect_single_tab, text="New Filename:").grid(row=4, column=0, sticky='w', pady=5)
        self.unprotect_single_new_filename = tk.StringVar()
        ttk.Entry(self.unprotect_single_tab, textvariable=self.unprotect_single_new_filename, width=50).grid(row=4, column=1, padx=5)
        ttk.Label(self.unprotect_single_tab, text="(Leave empty to keep original name)").grid(row=5, column=1, sticky='w')
        
        # Start button
        self.unprotect_single_start_btn = ttk.Button(self.unprotect_single_tab, text="Start Unprotecting", command=self.start_unprotect_single)
        self.unprotect_single_start_btn.grid(row=6, column=1, pady=20)
        
        # Progress bar
        self.unprotect_single_progress = ttk.Progressbar(self.unprotect_single_tab, length=400, mode='determinate')
        self.unprotect_single_progress.grid(row=7, column=1, pady=10)
        
    def setup_unprotect_folder_tab(self):
        # Folder selection
        ttk.Label(self.unprotect_folder_tab, text="Select Folder with Protected PDFs:").grid(row=0, column=0, sticky='w', pady=5)
        self.unprotect_folder_path = tk.StringVar()
        ttk.Entry(self.unprotect_folder_tab, textvariable=self.unprotect_folder_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.unprotect_folder_tab, text="Browse", command=self.browse_unprotect_folder).grid(row=0, column=2)
        
        # Output directory
        ttk.Label(self.unprotect_folder_tab, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.unprotect_folder_output_path = tk.StringVar(value=os.path.expanduser("~"))
        ttk.Entry(self.unprotect_folder_tab, textvariable=self.unprotect_folder_output_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self.unprotect_folder_tab, text="Browse", command=self.browse_unprotect_folder_output).grid(row=1, column=2)
        
        # Password
        ttk.Label(self.unprotect_folder_tab, text="PDF Password (for all files):").grid(row=2, column=0, sticky='w', pady=5)
        self.unprotect_folder_password = tk.StringVar()
        self.unprotect_folder_password_entry = ttk.Entry(self.unprotect_folder_tab, textvariable=self.unprotect_folder_password, width=50, show="*")
        self.unprotect_folder_password_entry.grid(row=2, column=1, padx=5)
        
        # Show password checkbox
        ttk.Checkbutton(self.unprotect_folder_tab, text="Show Password", 
                       variable=self.show_password_unprotect_folder,
                       command=lambda: self.toggle_password_visibility(self.unprotect_folder_password_entry, self.show_password_unprotect_folder)).grid(row=3, column=1, sticky='w')
        
        # Note about password
        ttk.Label(self.unprotect_folder_tab, text="Note: All PDFs in folder must use the same password", 
                 foreground='red').grid(row=4, column=1, sticky='w', pady=5)
        
        # Start button
        self.unprotect_folder_start_btn = ttk.Button(self.unprotect_folder_tab, text="Start Unprotecting", command=self.start_unprotect_folder)
        self.unprotect_folder_start_btn.grid(row=5, column=1, pady=20)
        
        # Progress bar
        self.unprotect_folder_progress = ttk.Progressbar(self.unprotect_folder_tab, length=400, mode='determinate')
        self.unprotect_folder_progress.grid(row=6, column=1, pady=10)
        
    def setup_log_area(self):
        # Log area frame
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        ttk.Label(log_frame, text="Log:").pack(anchor='w')
        
        # Log text with scrollbar
        self.log_text = tk.Text(log_frame, height=10, wrap='word')
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
        
    def toggle_password_visibility(self, entry_widget, show_var):
        if show_var.get():
            entry_widget.config(show="")
        else:
            entry_widget.config(show="*")
    
    # Browse functions for Protect tabs
    def browse_single_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            self.single_file_path.set(filename)
            # Set default new filename
            default_name = os.path.basename(filename)
            self.single_new_filename.set(default_name.replace('.pdf', '_protected.pdf'))
            
    def browse_single_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.single_output_path.set(folder)
            
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            
    def browse_folder_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_output_path.set(folder)
    
    # Browse functions for Unprotect tabs
    def browse_unprotect_single_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            self.unprotect_single_file_path.set(filename)
            # Set default new filename
            default_name = os.path.basename(filename)
            self.unprotect_single_new_filename.set(default_name.replace('.pdf', '_unprotected.pdf'))
            
    def browse_unprotect_single_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.unprotect_single_output_path.set(folder)
            
    def browse_unprotect_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.unprotect_folder_path.set(folder)
            
    def browse_unprotect_folder_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.unprotect_folder_output_path.set(folder)
            
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.root.update()
        
    def clear_log(self):
        self.log_text.delete(1.0, 'end')
        
    def protect_pdf(self, input_path, output_path, password):
        try:
            with open(input_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Copy all pages
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Add password
                pdf_writer.encrypt(password)
                
                # Save to output
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                    
            return True, "Success"
        except Exception as e:
            return False, str(e)
    
    def unprotect_pdf(self, input_path, output_path, password):
        try:
            with open(input_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    # Try to decrypt with provided password
                    if pdf_reader.decrypt(password):
                        pdf_writer = PyPDF2.PdfWriter()
                        
                        # Copy all pages
                        for page_num in range(len(pdf_reader.pages)):
                            pdf_writer.add_page(pdf_reader.pages[page_num])
                        
                        # Save without password
                        with open(output_path, 'wb') as output_file:
                            pdf_writer.write(output_file)
                        
                        return True, "Success"
                    else:
                        return False, "Incorrect password"
                else:
                    # File is not encrypted, just copy it
                    shutil.copy2(input_path, output_path)
                    return True, "File was not encrypted, copied as is"
                    
        except Exception as e:
            return False, str(e)
    
    # Protect Single File
    def start_single_file(self):
        if not self.single_file_path.get():
            messagebox.showerror("Error", "Please select a PDF file")
            return
            
        if not self.single_password.get():
            messagebox.showerror("Error", "Please enter a password")
            return
            
        # Disable start button
        self.single_start_btn.config(state='disabled')
        
        # Start in new thread
        thread = threading.Thread(target=self.process_single_file)
        thread.daemon = True
        thread.start()
        
    def process_single_file(self):
        try:
            input_path = self.single_file_path.get()
            output_folder = self.single_output_path.get()
            password = self.single_password.get()
            
            # Determine output filename
            if self.single_new_filename.get():
                output_filename = self.single_new_filename.get()
                if not output_filename.endswith('.pdf'):
                    output_filename += '.pdf'
            else:
                output_filename = os.path.basename(input_path)
                
            output_path = os.path.join(output_folder, output_filename)
            
            self.log_message(f"🔒 Starting to protect: {os.path.basename(input_path)}")
            self.single_progress['value'] = 30
            self.root.update()
            
            # Protect PDF
            success, message = self.protect_pdf(input_path, output_path, password)
            
            if success:
                self.single_progress['value'] = 100
                self.log_message(f"✅ Success! Protected PDF saved to: {output_path}")
                self.log_message(f"🔑 Password used: {password}")
                messagebox.showinfo("Success", f"PDF protected successfully!\nSaved to: {output_path}")
            else:
                self.single_progress['value'] = 0
                self.log_message(f"❌ Error: {message}")
                messagebox.showerror("Error", f"Failed to protect PDF: {message}")
                
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
        finally:
            self.single_start_btn.config(state='normal')
    
    # Protect Folder
    def start_folder(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder")
            return
            
        if not self.folder_password.get():
            messagebox.showerror("Error", "Please enter a password")
            return
            
        # Disable start button
        self.folder_start_btn.config(state='disabled')
        
        # Start in new thread
        thread = threading.Thread(target=self.process_folder)
        thread.daemon = True
        thread.start()
        
    def process_folder(self):
        try:
            source_folder = self.folder_path.get()
            dest_folder = self.folder_output_path.get()
            password = self.folder_password.get()
            
            self.log_message(f"📁 Starting to process folder: {source_folder}")
            
            # Count total files for progress
            total_files = sum([len(files) for r, d, files in os.walk(source_folder)])
            processed = 0
            pdf_count = 0
            other_count = 0
            error_count = 0
            
            # Walk through directory
            for root, dirs, files in os.walk(source_folder):
                # Create corresponding destination directory
                relative_path = os.path.relpath(root, source_folder)
                if relative_path == '.':
                    dest_dir = dest_folder
                else:
                    dest_dir = os.path.join(dest_folder, relative_path)
                
                os.makedirs(dest_dir, exist_ok=True)
                
                for file in files:
                    source_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    
                    # Update progress
                    processed += 1
                    progress = (processed / total_files) * 100
                    self.folder_progress['value'] = progress
                    self.root.update()
                    
                    # Process PDF files
                    if file.lower().endswith('.pdf'):
                        pdf_count += 1
                        self.log_message(f"📄 Processing PDF: {file}")
                        
                        # Create protected PDF
                        success, message = self.protect_pdf(source_file, dest_file, password)
                        
                        if success:
                            self.log_message(f"  ✅ Protected: {file}")
                        else:
                            error_count += 1
                            self.log_message(f"  ❌ Failed to protect {file}: {message}")
                    else:
                        # Copy non-PDF files
                        other_count += 1
                        try:
                            shutil.copy2(source_file, dest_file)
                            self.log_message(f"📋 Copied: {file}")
                        except Exception as e:
                            error_count += 1
                            self.log_message(f"  ❌ Failed to copy {file}: {str(e)}")
            
            self.folder_progress['value'] = 100
            self.log_message("=" * 50)
            self.log_message("📊 PROTECT SUMMARY:")
            self.log_message(f"   ✅ PDF files protected: {pdf_count}")
            self.log_message(f"   📋 Other files copied: {other_count}")
            self.log_message(f"   ❌ Errors: {error_count}")
            self.log_message(f"   📁 Output folder: {dest_folder}")
            self.log_message("=" * 50)
            
            messagebox.showinfo("Completed", f"Folder processing completed!\n\nSummary:\n- PDF files protected: {pdf_count}\n- Other files copied: {other_count}\n- Errors: {error_count}")
            
        except Exception as e:
            self.log_message(f"❌ Error processing folder: {str(e)}")
            messagebox.showerror("Error", f"Error processing folder: {str(e)}")
        finally:
            self.folder_start_btn.config(state='normal')
    
    # Unprotect Single File
    def start_unprotect_single(self):
        if not self.unprotect_single_file_path.get():
            messagebox.showerror("Error", "Please select a PDF file")
            return
            
        if not self.unprotect_single_password.get():
            messagebox.showerror("Error", "Please enter the PDF password")
            return
            
        # Disable start button
        self.unprotect_single_start_btn.config(state='disabled')
        
        # Start in new thread
        thread = threading.Thread(target=self.process_unprotect_single)
        thread.daemon = True
        thread.start()
        
    def process_unprotect_single(self):
        try:
            input_path = self.unprotect_single_file_path.get()
            output_folder = self.unprotect_single_output_path.get()
            password = self.unprotect_single_password.get()
            
            # Determine output filename
            if self.unprotect_single_new_filename.get():
                output_filename = self.unprotect_single_new_filename.get()
                if not output_filename.endswith('.pdf'):
                    output_filename += '.pdf'
            else:
                output_filename = os.path.basename(input_path)
                
            output_path = os.path.join(output_folder, output_filename)
            
            self.log_message(f"🔓 Starting to unprotect: {os.path.basename(input_path)}")
            self.unprotect_single_progress['value'] = 30
            self.root.update()
            
            # Unprotect PDF
            success, message = self.unprotect_pdf(input_path, output_path, password)
            
            if success:
                self.unprotect_single_progress['value'] = 100
                self.log_message(f"✅ Success! Unprotected PDF saved to: {output_path}")
                messagebox.showinfo("Success", f"PDF unprotected successfully!\nSaved to: {output_path}")
            else:
                self.unprotect_single_progress['value'] = 0
                self.log_message(f"❌ Error: {message}")
                messagebox.showerror("Error", f"Failed to unprotect PDF: {message}")
                
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
        finally:
            self.unprotect_single_start_btn.config(state='normal')
    
    # Unprotect Folder
    def start_unprotect_folder(self):
        if not self.unprotect_folder_path.get():
            messagebox.showerror("Error", "Please select a folder")
            return
            
        if not self.unprotect_folder_password.get():
            messagebox.showerror("Error", "Please enter the PDF password")
            return
            
        # Disable start button
        self.unprotect_folder_start_btn.config(state='disabled')
        
        # Start in new thread
        thread = threading.Thread(target=self.process_unprotect_folder)
        thread.daemon = True
        thread.start()
        
    def process_unprotect_folder(self):
        try:
            source_folder = self.unprotect_folder_path.get()
            dest_folder = self.unprotect_folder_output_path.get()
            password = self.unprotect_folder_password.get()
            
            self.log_message(f"📁 Starting to process folder for unprotect: {source_folder}")
            
            # Count total files for progress
            total_files = sum([len(files) for r, d, files in os.walk(source_folder)])
            processed = 0
            pdf_count = 0
            other_count = 0
            error_count = 0
            
            # Walk through directory
            for root, dirs, files in os.walk(source_folder):
                # Create corresponding destination directory
                relative_path = os.path.relpath(root, source_folder)
                if relative_path == '.':
                    dest_dir = dest_folder
                else:
                    dest_dir = os.path.join(dest_folder, relative_path)
                
                os.makedirs(dest_dir, exist_ok=True)
                
                for file in files:
                    source_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    
                    # Update progress
                    processed += 1
                    progress = (processed / total_files) * 100
                    self.unprotect_folder_progress['value'] = progress
                    self.root.update()
                    
                    # Process PDF files
                    if file.lower().endswith('.pdf'):
                        pdf_count += 1
                        self.log_message(f"📄 Processing PDF: {file}")
                        
                        # Unprotect PDF
                        success, message = self.unprotect_pdf(source_file, dest_file, password)
                        
                        if success:
                            self.log_message(f"  ✅ Unprotected: {file}")
                        else:
                            error_count += 1
                            self.log_message(f"  ❌ Failed to unprotect {file}: {message}")
                    else:
                        # Copy non-PDF files
                        other_count += 1
                        try:
                            shutil.copy2(source_file, dest_file)
                            self.log_message(f"📋 Copied: {file}")
                        except Exception as e:
                            error_count += 1
                            self.log_message(f"  ❌ Failed to copy {file}: {str(e)}")
            
            self.unprotect_folder_progress['value'] = 100
            self.log_message("=" * 50)
            self.log_message("📊 UNPROTECT SUMMARY:")
            self.log_message(f"   ✅ PDF files unprotected: {pdf_count}")
            self.log_message(f"   📋 Other files copied: {other_count}")
            self.log_message(f"   ❌ Errors: {error_count}")
            self.log_message(f"   📁 Output folder: {dest_folder}")
            self.log_message("=" * 50)
            
            messagebox.showinfo("Completed", f"Folder processing completed!\n\nSummary:\n- PDF files unprotected: {pdf_count}\n- Other files copied: {other_count}\n- Errors: {error_count}")
            
        except Exception as e:
            self.log_message(f"❌ Error processing folder: {str(e)}")
            messagebox.showerror("Error", f"Error processing folder: {str(e)}")
        finally:
            self.unprotect_folder_start_btn.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFPasswordProtector(root)
    root.mainloop()