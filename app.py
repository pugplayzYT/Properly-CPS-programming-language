import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as ttk


# CPS Interpreter Logic
class CPSInterpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}

    def reset(self):
        self.variables.clear()
        self.functions.clear()

    def run_code(self, code):
        self.reset()
        lines = [line.strip() for line in code.strip().split("\n") if line.strip()]  # Remove empty lines
        output = []
        execution_started = False
        function_name = None
        function_body = []

        for i, line in enumerate(lines):
            if line.startswith("if!app.run ^^true^^::do"):
                execution_started = True
                break  # Stop processing functions and variables

            # Ignore empty lines
            if not line:
                continue

            # Parsing variable declarations
            if line.startswith("app.add ^^") and ":: value%" in line:
                parts = line.split(":: value%^^")
                if len(parts) != 2 or not parts[0].startswith("app.add ^^") or not parts[1].endswith("^^"):
                    return f"Syntax Error: Invalid variable declaration '{line}'"

                var_name = parts[0][len("app.add ^^"):-2].strip()
                var_value = parts[1][:-2].strip()
                self.variables[var_name] = var_value
                continue

            # Parsing function declarations
            if line.startswith("app.get::^^") and line.endswith("^^"):
                function_name = line[len("app.get::^^"):-2].strip()
                function_body = []
                continue

            if function_name:
                if line == "!":
                    self.functions[function_name] = function_body  # Store function
                    function_name = None
                else:
                    function_body.append(line)
                continue

            return f"Syntax Error: Invalid declaration '{line}'"

        if not execution_started:
            return "Syntax Error: Expected 'if!app.run ^^true^^::do' before execution."

        # Execute CPS code
        for line in lines[i + 1:-1]:  # Exclude '!' from execution
            line = line.strip()

            if line.startswith("Console.line^^") and line.endswith("^^"):
                text = line[len("Console.line^^"):-2].strip()
                output.append(self.variables.get(text, text))
                continue

            if line.startswith("app.getthe^^") and line.endswith("^^"):
                function_name = line[len("app.getthe^^"):-2].strip()
                if function_name in self.functions:
                    for func_line in self.functions[function_name]:
                        if func_line.startswith("Console.line^^") and func_line.endswith("^^"):
                            text = func_line[len("Console.line^^"):-2].strip()
                            output.append(self.variables.get(text, text))
                        else:
                            return f"Syntax Error: Invalid statement '{func_line}' in function '{function_name}'"
                else:
                    return f"Syntax Error: Function '{function_name}' not found."
                continue

            return f"Syntax Error: Invalid statement '{line}'"

        return "\n".join(output)


# CPS Commands and Autocomplete Setup
CPS_COMMANDS = [
    "if!app.run ^^true^^::do",
    "Console.line^^text in here^^",
    "app.add ^^variable_name^^:: value%^^value here^^",
    "app.get::^^function_name^^",
    "app.getthe^^function_name^^",
    "!"
]


class CPSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPS Interpreter")
        self.root.geometry("700x500")
        self.root.configure(bg="#282C34")

        # Style
        self.style = ttk.Style()
        self.style.theme_use("darkly")

        # Input area
        self.text_area = scrolledtext.ScrolledText(
            root, font=("JetBrains Mono", 12), wrap=tk.WORD, height=12,
            bg="#1E1E1E", fg="white", insertbackground="white", borderwidth=2
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text_area.bind("<KeyRelease>", self.show_autocomplete)
        self.text_area.bind("<Tab>", self.confirm_autocomplete)

        # Autocomplete dropdown
        self.autocomplete_listbox = tk.Listbox(
            root, font=("JetBrains Mono", 12), bg="#333", fg="white",
            selectbackground="#555", height=4
        )
        self.autocomplete_listbox.bind("<ButtonRelease-1>", self.insert_autocomplete)

        # Run button
        self.run_button = ttk.Button(root, text="▶ Run Code", bootstyle="success", command=self.run_cps_code)
        self.run_button.pack(pady=5)

        # Output area
        self.output_area = tk.Text(
            root, font=("JetBrains Mono", 12), height=6, bg="#1E1E1E", fg="lime", wrap=tk.WORD,
            borderwidth=2, state=tk.DISABLED
        )
        self.output_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Interpreter instance
        self.interpreter = CPSInterpreter()

    def show_autocomplete(self, event):
        """ Show autocomplete dropdown dynamically as user types. """
        cursor_position = self.text_area.index(tk.INSERT)
        text_before_cursor = self.text_area.get("1.0", cursor_position).strip().split()[-1]

        # Match commands containing the current input (even partial)
        matches = [cmd for cmd in CPS_COMMANDS if text_before_cursor in cmd]

        if matches:
            self.autocomplete_listbox.delete(0, tk.END)
            for match in matches:
                self.autocomplete_listbox.insert(tk.END, match)

            # Position autocomplete near the cursor
            x, y, _, _ = self.text_area.bbox("insert")
            self.autocomplete_listbox.place(x=x + 20, y=y + 80)
        else:
            self.autocomplete_listbox.place_forget()

    def insert_autocomplete(self, event=None):
        """ Insert selected autocomplete command into text area. """
        if self.autocomplete_listbox.size() == 0:
            return

        selected = self.autocomplete_listbox.get(tk.ACTIVE)
        cursor_position = self.text_area.index(tk.INSERT)
        current_text = self.text_area.get("1.0", cursor_position)
        words = current_text.split()
        last_word = words[-1] if words else ""

        updated_text = current_text[: -len(last_word)] + selected if last_word else selected
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", updated_text)

        self.autocomplete_listbox.place_forget()

    def confirm_autocomplete(self, event):
        """ Confirm the first autocomplete option with Tab key. """
        self.insert_autocomplete()
        return "break"

    def run_cps_code(self):
        """ Run the CPS code and display output/errors. """
        code = self.text_area.get("1.0", tk.END).strip()
        self.output_area.config(state=tk.NORMAL)
        self.output_area.delete("1.0", tk.END)

        output = self.interpreter.run_code(code)

        if "Syntax Error" in output:
            messagebox.showerror("Syntax Error", output)
        else:
            self.output_area.insert(tk.END, output)

        self.output_area.config(state=tk.DISABLED)


# Run GUI
if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = CPSGUI(root)
    root.mainloop()
