import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from datetime import datetime
import re
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class FoSGamersChatSplitter:
    def __init__(self):
        logger.info("Initializing FoSGamersChatSplitter")
        self.root = None
        self.json_file_path = None
        self.image_dir_path = None
        self.output_dir = None
        self.user_name = None
        self.size_limit_mb = 5

    def start(self):
        """Start the chat splitter GUI"""
        logger.info("Starting chat splitter GUI")
        self.root = tk.Tk()
        self.root.title("FoSGamers Chat Splitter")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create widgets
        self.create_widgets(main_frame)
        
        # Start the main loop
        self.root.mainloop()

    def stop(self):
        """Stop the chat splitter GUI"""
        logger.info("Stopping chat splitter GUI")
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

    def create_widgets(self, parent):
        # JSON File Selection
        json_frame = tk.Frame(parent, bg="#333333")
        json_frame.pack(pady=10)
        tk.Label(json_frame, text="Select ChatGPT JSON File:", font=("Arial", 14, "bold"), 
                 bg="#333333", fg="#FFFFFF").pack()
        self.json_file_path = tk.StringVar()
        tk.Entry(json_frame, textvariable=self.json_file_path, width=50, font=("Arial", 12)).pack(pady=5)
        self.json_button = ttk.Button(json_frame, text="Browse", command=self.browse_json_file, 
                                     style="Green.TButton")
        self.json_button.pack(pady=5)

        # Output Directory Selection
        output_frame = tk.Frame(parent, bg="#333333")
        output_frame.pack(pady=10)
        tk.Label(output_frame, text="Select Output Folder:", font=("Arial", 14, "bold"), 
                 bg="#333333", fg="#FFFFFF").pack()
        self.output_dir_path = tk.StringVar()
        tk.Entry(output_frame, textvariable=self.output_dir_path, width=50, font=("Arial", 12)).pack(pady=5)
        self.output_button = ttk.Button(output_frame, text="Browse", command=self.browse_output_dir, 
                                       style="Green.TButton")
        self.output_button.pack(pady=5)

        # Image Directory Selection
        image_frame = tk.Frame(parent, bg="#333333")
        image_frame.pack(pady=10)
        tk.Label(image_frame, text="Select Image Folder:", font=("Arial", 14, "bold"), 
                 bg="#333333", fg="#FFFFFF").pack()
        self.image_dir_path = tk.StringVar()
        tk.Entry(image_frame, textvariable=self.image_dir_path, width=50, font=("Arial", 12)).pack(pady=5)
        self.image_button = ttk.Button(image_frame, text="Browse", command=self.browse_image_dir, 
                                      style="Green.TButton")
        self.image_button.pack(pady=5)

        # User Name
        name_frame = tk.Frame(parent, bg="#333333")
        name_frame.pack(pady=10)
        tk.Label(name_frame, text="Your Name (for output files):", font=("Arial", 14, "bold"), 
                 bg="#333333", fg="#FFFFFF").pack()
        self.user_name = tk.StringVar(value="FoSGamers")
        tk.Entry(name_frame, textvariable=self.user_name, font=("Arial", 12)).pack(pady=5)

        # File Size Limit
        size_frame = tk.Frame(parent, bg="#333333")
        size_frame.pack(pady=10)
        tk.Label(size_frame, text="Max File Size (MB):", font=("Arial", 14, "bold"), 
                 bg="#333333", fg="#FFFFFF").pack()
        self.size_limit_mb = tk.DoubleVar(value=25.0)
        tk.Entry(size_frame, textvariable=self.size_limit_mb, font=("Arial", 12)).pack(pady=5)

        # Process Button
        process_frame = tk.Frame(parent, bg="#333333")
        process_frame.pack(pady=20)
        self.process_button = ttk.Button(process_frame, text="Split Chats", command=self.process_chats, 
                                        style="Green.TButton")
        self.process_button.pack()

    def browse_json_file(self):
        self.json_button.configure(style="Red.TButton")
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.json_file_path.set(file_path)
            self.json_button.configure(style="Green.TButton")

    def browse_output_dir(self):
        self.output_button.configure(style="Red.TButton")
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_path.set(dir_path)
            self.output_button.configure(style="Green.TButton")

    def browse_image_dir(self):
        self.image_button.configure(style="Red.TButton")
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.image_dir_path.set(dir_path)
            self.image_button.configure(style="Green.TButton")

    def safe_parse_timestamp(self, timestamp, context=""):
        """Safely parse a timestamp (string or float), return formatted string or 'Unknown'."""
        if timestamp is None:
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

    def find_image_file(self, asset_pointer):
        """Find local image file matching asset_pointer ID in the image folder."""
        image_dir = self.image_dir_path.get()
        if not image_dir or not asset_pointer:
            return None
        file_id = asset_pointer.replace("file-service://", "")
        for ext in ['.png', '.jpg', '.jpeg', '.gif']:
            file_path = os.path.join(image_dir, f"{file_id}{ext}")
            if os.path.exists(file_path):
                return file_path
        return None

    def extract_content(self, content, convo_id, node_id):
        """Extract text and image references from content.parts."""
        if not content or 'parts' not in content:
            return None
        parts = content.get('parts', [])
        content_type = content.get('content_type', 'text')
        
        extracted = []
        for part in parts:
            if isinstance(part, str):
                extracted.append(part)
            elif isinstance(part, dict):
                if part.get('content_type') == 'image_asset_pointer':
                    asset_pointer = part.get('asset_pointer')
                    image_path = self.find_image_file(asset_pointer)
                    if image_path:
                        extracted.append(f"[Image: {image_path}]")
                    else:
                        extracted.append(f"[Image: {asset_pointer} (not found)]")
                else:
                    print(f"Debug: Non-string part in convo {convo_id}, node {node_id}: {part} (content_type: {content_type})")
                    for key in ['text', 'code', 'output']:
                        if key in part and isinstance(part[key], str):
                            extracted.append(part[key])
            else:
                print(f"Debug: Skipping unexpected part type in convo {convo_id}, node {node_id}: {part} (type: {type(part)})")
        
        return "\n".join(extracted) if extracted else None

    def process_chats(self):
        self.process_button.configure(style="Red.TButton")
        json_file = self.json_file_path.get()
        output_dir = self.output_dir_path.get()
        user_name = self.user_name.get().strip() or "FoSGamers"
        size_limit_mb = self.size_limit_mb.get()

        if not json_file or not os.path.exists(json_file):
            messagebox.showerror("Error", "Yo, pick a valid JSON file!")
            self.process_button.configure(style="Green.TButton")
            return
        if not output_dir:
            messagebox.showerror("Error", "Yo, pick an output folder!")
            self.process_button.configure(style="Green.TButton")
            return
        if size_limit_mb <= 0:
            messagebox.showerror("Error", "File size limit gotta be positive, fam.")
            self.process_button.configure(style="Green.TButton")
            return

        try:
            self.output_dir = os.path.join(output_dir, "FoSGamers_ChatSplits")
            os.makedirs(self.output_dir, exist_ok=True)

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                conversations = data
            elif isinstance(data, dict):
                conversations = data.get('conversations', [])
            else:
                raise ValueError("JSON root must be a list or dictionary")

            combined_content = []
            for convo in conversations:
                convo_id = convo.get('id', 'unknown')
                title = self.sanitize_filename(convo.get('title', 'NoTitle'))
                print(f"Debug: Sanitized title for convo {convo_id}: {title}")
                create_time = self.safe_parse_timestamp(convo.get('create_time'), f"conversation {convo_id}")
                
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

                messages.sort(key=lambda x: x[0] if x[0] != "Unknown" else "0")

                convo_filename = os.path.join(self.output_dir, f"{title}.txt")
                convo_content = [f"Chat: {title}\nStarted: {create_time}\n"]
                for timestamp, sender, content in messages:
                    convo_content.append(f"[{timestamp}] {sender}:\n{content}\n")
                
                with open(convo_filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(convo_content))
                
                combined_content.extend(convo_content + ["\n" + "="*50 + "\n"])

            combined_filename = os.path.join(self.output_dir, "fosgamers_all_chats.txt")
            combined_text = "\n".join(combined_content)
            
            size_limit_bytes = size_limit_mb * 1024 * 1024
            combined_size = len(combined_text.encode('utf-8'))
            
            if combined_size <= size_limit_bytes:
                with open(combined_filename, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
            else:
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

                if current_part:
                    part_filename = os.path.join(self.output_dir, f"fosgamers_all_chats_part_{part_number}.txt")
                    with open(part_filename, 'w', encoding='utf-8') as f:
                        f.write("\n".join(current_part))

            messagebox.showinfo("Done!", f"Chats split and saved in {self.output_dir}. Keep gaming, FoSGamers!")
            self.process_button.configure(style="Green.TButton")

        except Exception as e:
            messagebox.showerror("Whoops!", f"Something broke: {str(e)}")
            self.process_button.configure(style="Green.TButton")

def main():
    """Main function to start the chatsplitter module"""
    # Create and run the chat splitter
    app = FoSGamersChatSplitter()
    app.start()

if __name__ == "__main__":
    main()