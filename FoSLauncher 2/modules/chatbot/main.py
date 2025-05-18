# File: modules/chatbot/main.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time

# Placeholder for backend AI communication (simulate response)
def simulate_ai_response(prompt):
    time.sleep(1)
    return f"[Simulated AI]: You said '{prompt}'"


class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FoSGamers Chatbot+")

        # Configure main frame
        self.mainframe = ttk.Frame(root, padding="10")
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(self.mainframe, wrap=tk.WORD, width=70, height=20, state='disabled')
        self.chat_display.grid(column=0, row=0, columnspan=2, padx=5, pady=5)

        # User input
        self.user_input = tk.StringVar()
        self.input_entry = ttk.Entry(self.mainframe, width=60, textvariable=self.user_input)
        self.input_entry.grid(column=0, row=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.input_entry.bind('<Return>', self.send_prompt)

        # Send button
        self.send_button = ttk.Button(self.mainframe, text="Send", command=self.send_prompt)
        self.send_button.grid(column=1, row=1, padx=5, pady=5)

        # Configure weight
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=1)

    def send_prompt(self, event=None):
        prompt = self.user_input.get().strip()
        if prompt:
            self.append_message("You", prompt)
            self.user_input.set("")
            threading.Thread(target=self.get_ai_response, args=(prompt,), daemon=True).start()

    def append_message(self, sender, message):
        self.chat_display['state'] = 'normal'
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display['state'] = 'disabled'
        self.chat_display.see(tk.END)

    def get_ai_response(self, prompt):
        response = simulate_ai_response(prompt)  # Replace with actual backend call
        self.append_message("Chatbot+", response)


def main():
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
