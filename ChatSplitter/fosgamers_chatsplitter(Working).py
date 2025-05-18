import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
from datetime import datetime
import re

class FoSGamersChatSplitter:
    def __init__(self, root):
        self.root = root
        self.root.title("FoSGamers ChatSplitter")
        self.root.geometry("600x450")
        self.root.configure(bg="#f0f0f0")  # Light gray background for contrast
        
        # Variables
        self.json_file_path = tk.StringVar()
        self.output_dir_path = tk.StringVar()
        self.user_name = tk.StringVar(value="FoSGamers")
        self.size_limit_mb = tk.DoubleVar(value=25.0)
        self.output_dir = None

        # Button references for color control
        self.json_button = None
        self.output_button = None
        self.process_button = None

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # JSON File Selection
        tk.Label(self.root, text="Select ChatGPT JSON File:", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)
        tk.Entry(self.root, textvariable=self.json_file_path, width=50).pack()
        self.json_button = tk.Button(self.root, text="Browse", command=self.browse_json_file, 
                                   bg="#4CAF50", fg="white", font=("Arial", 10), width=10)
        self.json_button.pack(pady=5)

        # Output Directory Selection
        tk.Label(self.root, text="Select Output Folder:", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)
        tk.Entry(self.root, textvariable=self.output_dir_path, width=50).pack()
        self.output_button = tk.Button(self.root, text="Browse", command=self.browse_output_dir, 
                                     bg="#4CAF50", fg="white", font=("Arial", 10), width=10)
        self.output_button.pack(pady=5)

        # User Name
        tk.Label(self.root, text="Your Name (for output files):", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)
        tk.Entry(self.root, textvariable=self.user_name).pack()

        # File Size Limit
        tk.Label(self.root, text="Max File Size (MB):", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)
        tk.Entry(self.root, textvariable=self.size_limit_mb).pack()

        # Process Button
        self.process_button = tk.Button(self.root, text="Split Chats", command=self.process_chats, 
                                      bg="#4CAF50", fg="white", font=("Arial", 12), width=12)
        self.process_button.pack(pady=20)

    def browse_json_file(self):
        self.json_button.configure(bg="#FF0000")  # Turn red when clicked
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.json_file_path.set(file_path)
            self.json_button.configure(bg="#4CAF50")  # Back to green when done

    def browse_output_dir(self):
        self.output_button.configure(bg="#FF0000")  # Turn red when clicked
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_path.set(dir_path)
            self.output_button.configure(bg="#4CAF50")  # Back to green when done

    def safe_parse_timestamp(self, timestamp, context=""):
        """Safely parse a timestamp (string or float), return formatted string or 'Unknown'."""
        if timestamp is None:
            print(f"Debug: Invalid timestamp in {context}: None (type: <class 'NoneType'>)")
            return "Unknown"
        if isinstance(timestamp, (int, float)):
            try:
                return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                print(f"Debug: Failed to parse timestamp in {context}: {timestamp} (Error: {e})")
                return "Unknown"
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                print(f"Debug: Failed to parse timestamp in {context}: {timestamp} (Error: {e})")
                return "Unknown"
        print(f"Debug: Invalid timestamp in {context}: {timestamp} (type: {type(timestamp)})")
        return "Unknown"

    def sanitize_filename(self, filename):
        """Replace invalid filename characters with underscores."""
        sanitized = re.sub(r'[\/:*?"<>|]', '_', filename)
        sanitized = sanitized.replace(' ', '_').strip('_')
        return sanitized or "NoTitle"

    def extract_content(self, content, convo_id, node_id):
        """Extract text from content.parts, handling non-string cases."""
        if not content or 'parts' not in content:
            return None
        parts = content.get('parts', [])
        content_type = content.get('content_type', 'text')
        
        extracted = []
        for part in parts:
            if isinstance(part, str):
                extracted.append(part)
            elif isinstance(part, dict):
                print(f"Debug: Non-string part in convo {convo_id}, node {node_id}: {part} (content_type: {content_type})")
                for key in ['text', 'code', 'output']:
                    if key in part and isinstance(part[key], str):
                        extracted.append(part[key])
            else:
                print(f"Debug: Skipping unexpected part type in convo {convo_id}, node {node_id}: {part} (type: {type(part)})")
        
        return "\n".join(extracted) if extracted else None

    def process_chats(self):
        self.process_button.configure(bg="#FF0000")  # Turn red when clicked
        json_file = self.json_file_path.get()
        output_dir = self.output_dir_path.get()
        user_name = self.user_name.get().strip() or "FoSGamers"
        size_limit_mb = self.size_limit_mb.get()

        if not json_file or not os.path.exists(json_file):
            messagebox.showerror("Error", "Yo, pick a valid JSON file!")
            self.process_button.configure(bg="#4CAF50")
            return
        if not output_dir:
            messagebox.showerror("Error", "Yo, pick an output folder!")
            self.process_button.configure(bg="#4CAF50")
            return
        if size_limit_mb <= 0:
            messagebox.showerror("Error", "File size limit gotta be positive, fam.")
            self.process_button.configure(bg="#4CAF50")
            return

        try:
            # Create output directory
            self.output_dir = os.path.join(output_dir, "FoSGamers_ChatSplits")
            os.makedirs(self.output_dir, exist_ok=True)

            # Load JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list and dict JSON structures
            if isinstance(data, list):
                conversations = data
            elif isinstance(data, dict):
                conversations = data.get('conversations', [])
            else:
                raise ValueError("JSON root must be a list or dictionary")

            # Process conversations
            combined_content = []
            for convo in conversations:
                convo_id = convo.get('id', 'unknown')
                title = self.sanitize_filename(convo.get('title', 'NoTitle'))
                print(f"Debug: Sanitized title for convo {convo_id}: {title}")
                create_time = self.safe_parse_timestamp(convo.get('create_time'), f"conversation {convo_id}")
                
                # Extract messages
                messages = []
                for node_id, node in convo.get('mapping', {}).items():
                    message = node.get('message')
                    if message and message.get('content'):
                        author = message.get('author', {}).get('role', 'unknown')
                        sender = "ChatGPT" if author == "assistant" else user_name
                        timestamp = self.safe_parse_timestamp(message.get('create_time'), f"message in {convo_id}")
                        content = self.extract_content(message['content'], convo_id, node_id)
                        if content:
                            messages.append((timestamp, sender, content))

                # Sort messages by timestamp
                messages.sort(key=lambda x: x[0] if x[0] != "Unknown" else "0")

                # Write individual conversation file
                convo_filename = os.path.join(self.output_dir, f"fosgamers_chat_{convo_id}_{title}.txt")
                convo_content = [f"Chat: {title}\nStarted: {create_time}\n"]
                for timestamp, sender, content in messages:
                    convo_content.append(f"[{timestamp}] {sender}:\n{content}\n")
                
                with open(convo_filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(convo_content))
                
                # Add to combined content
                combined_content.extend(convo_content + ["\n" + "="*50 + "\n"])

            # Write combined file and split if necessary
            combined_filename = os.path.join(self.output_dir, "fosgamers_all_chats.txt")
            combined_text = "\n".join(combined_content)
            
            # Check file size and split
            size_limit_bytes = size_limit_mb * 1024 * 1024
            combined_size = len(combined_text.encode('utf-8'))
            
            if combined_size <= size_limit_bytes:
                with open(combined_filename, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
            else:
                # Split into parts
                lines = combined_text.splitlines()
                part_size = size_limit_bytes
                current_part = []
                current_size = 0
                part_number = 1

                for line in lines:
                    line_size = len(line.encode('utf-8')) + 1
                    if current_size + line_size > part_size and current_part:
                        part_filename = os.path.join(self.output_dir, f"fosgamers_all_chats_part_{part_number}.txt")
                        with open(part_filename, 'w', encoding='utf-8') as f:
                            f.write("\n".join(current_part))
                        part_number += 1
                        current_part = []
                        current_size = 0
                    current_part.append(line)
                    current_size += line_size

                # Write final part
                if current_part:
                    part_filename = os.path.join(self.output_dir, f"fosgamers_all_chats_part_{part_number}.txt")
                    with open(part_filename, 'w', encoding='utf-8') as f:
                        f.write("\n".join(current_part))

            # Success message
            messagebox.showinfo("Done!", f"Chats split and saved in {self.output_dir}. Keep gaming, FoSGamers!")
            self.process_button.configure(bg="#4CAF50")  # Back to green

        except Exception as e:
            messagebox.showerror("Whoops!", f"Something broke: {str(e)}")
            self.process_button.configure(bg="#4CAF50")  # Back to green on error

if __name__ == "__main__":
    root = tk.Tk()
    app = FoSGamersChatSplitter(root)
    root.mainloop()