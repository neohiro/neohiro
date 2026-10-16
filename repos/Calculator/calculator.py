import tkinter as tk
import math
import re

# A more advanced GUI calculator with scientific, memory, history functions, and a secure expression parser.

class Calculator:
    """
    A class to create and manage an advanced GUI calculator with scientific, memory, and history functions.
    It now uses a custom parser instead of eval() for security and robustness.
    """
    def __init__(self, master):
        """
        Initializes the calculator's GUI components and state.
        """
        self.master = master
        master.title("Advanced Python Calculator 🚀 - FrenzyPenguin Media")
        master.resizable(False, False)
        master.iconbitmap('calculator.ico')  # Set the window icon

        # Set a dark theme for a sleek, modern look
        self.bg_color = "#282a36"  # Dark gray
        self.fg_color = "#f8f8f2"  # Light off-white
        self.entry_bg = "#44475a"  # Lighter gray for display
        self.button_bg = "#6a6d7a" # Gray for numbers/parentheses
        self.op_button_bg = "#8be9fd" # Blue for operators
        self.eq_button_bg = "#50fa7b" # Green for equals
        self.mem_sci_button_bg = "#6272a4" # Muted purple-blue for scientific/memory
        self.active_bg = "#21222c" # Darker gray on hover/press

        master.configure(bg=self.bg_color)

        # Initialize memory variable and history list
        self.memory = 0.0
        self.history = []
        # New state variable to track if the last action was an equals sign
        self.last_was_equals = False

        # Create the main frame for the calculator and a frame for the history log
        self.main_frame = tk.Frame(master, bg=self.bg_color)
        self.main_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.history_frame = tk.Frame(master, bg=self.bg_color)
        self.history_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        # Create the display entry widget inside the main frame
        self.display = tk.Entry(self.main_frame, width=30, justify='right', font=('Arial', 20, 'bold'),
                                bg=self.entry_bg, fg=self.fg_color, bd=0, relief=tk.FLAT, insertbackground=self.fg_color)
        self.display.grid(row=0, column=0, columnspan=5, padx=5, pady=10)
        self.display.insert(0, "0")

        # Bind keyboard events to the master window
        self.master.bind("<Key>", self._key_press)

        # Create the history log listbox and scrollbar inside the history frame
        history_label = tk.Label(self.history_frame, text="History", font=('Arial', 14, 'bold'), bg=self.bg_color, fg=self.fg_color)
        history_label.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        
        self.history_listbox = tk.Listbox(self.history_frame, height=15, width=25, font=('Arial', 12),
                                          bg=self.entry_bg, fg=self.fg_color, bd=0, relief=tk.FLAT, highlightthickness=0)
        self.history_listbox.grid(row=1, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(self.history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview, troughcolor=self.bg_color, bg=self.entry_bg)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.history_listbox.config(yscrollcommand=scrollbar.set)

        # Bind right-click event to show the context menu
        self.history_listbox.bind("<Button-3>", self.show_history_menu)

        # Create the context menu for the history listbox
        self.history_menu = tk.Menu(self.master, tearoff=0)
        self.history_menu.add_command(label="Copy", command=self.copy_history_entry)
        self.history_menu.add_command(label="Copy All", command=self.copy_all_history)

        # Add a button to clear the history log, now placed in a new row below the listbox
        clear_history_button = tk.Button(self.history_frame, text="Clear History", font=('Arial', 12, 'bold'),
                                         bg=self.mem_sci_button_bg, fg=self.fg_color, activebackground=self.active_bg,
                                         relief=tk.FLAT, bd=0, command=self.clear_history_log)
        clear_history_button.grid(row=2, column=0, columnspan=2, pady=(5, 0), sticky="ew")

        # Configure row and column weights to make the listbox expand
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(1, weight=1)

        # Define the layout of all buttons, with new categories for styling
        button_layout = [
            # Row 1: Parentheses and scientific functions
            (('(', 1, 0, self.mem_sci_button_bg), (')', 1, 1, self.mem_sci_button_bg), ('sin', 1, 2, self.mem_sci_button_bg), ('cos', 1, 3, self.mem_sci_button_bg), ('tan', 1, 4, self.mem_sci_button_bg)),
            # Row 2: Clear, backspace, and memory
            (('C', 2, 0, self.op_button_bg), ('Back', 2, 1, self.op_button_bg), ('MC', 2, 2, self.mem_sci_button_bg), ('MR', 2, 3, self.mem_sci_button_bg), ('M+', 2, 4, self.mem_sci_button_bg)),
            # Row 3: 7, 8, 9, divide, M-
            (('7', 3, 0, self.button_bg), ('8', 3, 1, self.button_bg), ('9', 3, 2, self.button_bg), ('/', 3, 3, self.op_button_bg), ('M-', 3, 4, self.mem_sci_button_bg)),
            # Row 4: 4, 5, 6, multiply, sqrt
            (('4', 4, 0, self.button_bg), ('5', 4, 1, self.button_bg), ('6', 4, 2, self.button_bg), ('*', 4, 3, self.op_button_bg), ('sqrt', 4, 4, self.mem_sci_button_bg)),
            # Row 5: 1, 2, 3, subtract, power
            (('1', 5, 0, self.button_bg), ('2', 5, 1, self.button_bg), ('3', 5, 2, self.button_bg), ('-', 5, 3, self.op_button_bg), ('^', 5, 4, self.mem_sci_button_bg)),
            # Row 6: New layout with 00 and a single-width equals button
            (('0', 6, 0, self.button_bg), ('.', 6, 1, self.button_bg), ('00', 6, 2, self.button_bg), ('+', 6, 3, self.op_button_bg), ('=', 6, 4, self.eq_button_bg)),
        ]

        # Create buttons and place them in the grid inside the main frame
        for row_buttons in button_layout:
            for (text, row, col, color) in row_buttons:
                if text == 'C':
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0, command=self.clear_display)
                elif text == 'Back':
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0, command=self.backspace)
                elif text == '=':
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0, command=self.calculate)
                elif text in ['M+', 'M-', 'MR', 'MC']:
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0,
                                       command=lambda t=text: self.memory_function(t))
                elif text in ['sin', 'cos', 'tan', 'sqrt', '^', '(', ')']:
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0,
                                       command=lambda t=text: self.scientific_function(t))
                else:
                    button = tk.Button(self.main_frame, text=text, width=7, height=2, font=('Arial', 12, 'bold'),
                                       bg=color, fg=self.fg_color, activebackground=self.active_bg, relief=tk.FLAT, bd=0,
                                       command=lambda t=text: self.button_click(t))

                button.grid(row=row, column=col, padx=2, pady=2)


    def _key_press(self, event):
        """
        Handles key press events from the keyboard and maps them to button functions.
        """
        key = event.char
        if key in "0123456789.+-*/^()":
            self.button_click(key)
        elif event.keysym == "Return":
            self.calculate()
        elif event.keysym == "BackSpace":
            self.backspace()
        elif key in "cC":
            self.clear_display()

    def button_click(self, value):
        """
        Handles number and operator button clicks.
        This method is reverted to a previous, working version.
        """
        current_text = self.display.get()

        # If the last action was an equals sign and a new number is pressed, clear the display
        if self.last_was_equals and (value.isdigit() or value == '.' or value == '(' or value == '00'):
            self.display.delete(0, tk.END)
            self.last_was_equals = False
        
        # Reset the flag if an operator is pressed
        if value in "+-*/^":
            self.last_was_equals = False

        if current_text == "0" and (value.isdigit() or value == '.' or value == '00'):
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, value)
        elif current_text == "0" and value == '(':
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, value)
        elif "Error" in current_text or "Invalid input" in current_text:
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, value)
        else:
            self.display.insert(tk.END, value)
    
    def backspace(self):
        """
        Removes the last character from the display.
        """
        self.last_was_equals = False
        current_text = self.display.get()
        if len(current_text) > 1:
            self.display.delete(len(current_text) - 1, tk.END)
        else:
            self.display.delete(0, tk.END)
            self.display.insert(0, "0")

    def clear_display(self):
        """
        Clears the display and resets the 'last_was_equals' flag.
        """
        self.display.delete(0, tk.END)
        self.display.insert(0, "0")
        self.last_was_equals = False
    
    def clear_history_log(self):
        """
        Clears the history list and the history listbox.
        """
        self.history.clear()
        self.history_listbox.delete(0, tk.END)

    def show_history_menu(self, event):
        """
        Displays the context menu when the user right-clicks on the history listbox.
        """
        try:
            # Clear previous selection to ensure only the item under the cursor is selected
            self.history_listbox.selection_clear(0, tk.END)
            # Find the nearest index to the event's y-coordinate and select it
            index = self.history_listbox.nearest(event.y)
            self.history_listbox.selection_set(index)
            # Display the menu at the cursor's position
            self.history_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass
    
    def copy_history_entry(self):
        """
        Copies the selected entry from the history listbox to the clipboard.
        """
        try:
            # Get the index of the selected item
            selected_index = self.history_listbox.curselection()
            if selected_index:
                # Get the text of the selected item
                selected_text = self.history_listbox.get(selected_index[0])
                # Clear the clipboard and append the selected text
                self.master.clipboard_clear()
                self.master.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def copy_all_history(self):
        """
        Copies all entries from the history listbox to the clipboard.
        """
        # Get all items from the listbox and join them with newlines
        all_history_text = "\n".join(self.history_listbox.get(0, tk.END))
        # Clear the clipboard and append the combined text
        self.master.clipboard_clear()
        self.master.clipboard_append(all_history_text)

    def memory_function(self, func):
        """
        Handles the memory functions (M+, M-, MR, MC).
        """
        self.last_was_equals = False
        try:
            current_value = float(self.display.get())
        except (ValueError):
            self.display.delete(0, tk.END)
            self.display.insert(0, "Error")
            return
        
        if func == 'M+':
            self.memory += current_value
        elif func == 'M-':
            self.memory -= current_value
        elif func == 'MR':
            self.display.delete(0, tk.END)
            self.display.insert(0, str(self.memory))
        elif func == 'MC':
            self.memory = 0.0

    def scientific_function(self, func):
        """
        Handles scientific functions and parentheses like sin, cos, tan, sqrt, and power.
        """
        self.last_was_equals = False
        try:
            current_text = self.display.get()
            if func == 'sqrt':
                result = math.sqrt(float(current_text))
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
                self.update_history(f"sqrt({current_text}) = {result}")
            elif func == '^':
                self.display.insert(tk.END, '^')
            elif func in ['(', ')']:
                 self.display.insert(tk.END, func)
            else:
                result = getattr(math, func)(math.radians(float(current_text)))
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
                self.update_history(f"{func}({current_text}) = {result}")
        except (ValueError, ZeroDivisionError, AttributeError):
            self.display.delete(0, tk.END)
            self.display.insert(0, "Invalid input")

    def _parse_expression(self, expression):
        """
        Parses and evaluates a mathematical expression using the Shunting-yard algorithm
        and Reverse Polish Notation (RPN) logic.
        """
        # Fix: Preprocess to handle unary minus at the beginning of an expression
        expression = expression.replace(' ', '')
        if expression.startswith('-'):
            expression = '0' + expression
        
        # Tokenize the expression into numbers and operators, including parentheses
        tokens = re.findall(r"(\d+\.?\d*|[-+*/^()])", expression)
        
        # Operators and their precedence
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        
        output_queue = []
        operator_stack = []

        for token in tokens:
            if re.match(r"^\d+\.?\d*$", token):
                output_queue.append(float(token))
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                if operator_stack and operator_stack[-1] == '(':
                    operator_stack.pop() # Discard the '('
                else:
                    return "Error: Mismatched parentheses"
            elif token in '+-*/^':
                while (operator_stack and operator_stack[-1] != '(' and
                       precedence.get(operator_stack[-1], 0) >= precedence.get(token, 0)):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
        
        while operator_stack:
            if operator_stack[-1] == '(':
                return "Error: Mismatched parentheses"
            output_queue.append(operator_stack.pop())

        # Evaluate the RPN expression
        eval_stack = []
        for token in output_queue:
            if isinstance(token, float):
                eval_stack.append(token)
            else:
                try:
                    operand2 = eval_stack.pop()
                    operand1 = eval_stack.pop()
                    if token == '+':
                        eval_stack.append(operand1 + operand2)
                    elif token == '-':
                        eval_stack.append(operand1 - operand2)
                    elif token == '*':
                        eval_stack.append(operand1 * operand2)
                    elif token == '/':
                        if operand2 == 0:
                            raise ZeroDivisionError
                        eval_stack.append(operand1 / operand2)
                    elif token == '^':
                        eval_stack.append(operand1 ** operand2)
                except IndexError:
                    return "Error"
                except ZeroDivisionError:
                    return "Error: Division by zero"

        return eval_stack[0] if eval_stack else "Error"

    def calculate(self):
        """
        Evaluates the expression in the display using the new parser, and updates the history.
        """
        expression = self.display.get()
        try:
            result = self._parse_expression(expression)
            
            # Format the result to remove trailing '.0' if it's an integer
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            if isinstance(result, str):
                self.display.delete(0, tk.END)
                self.display.insert(0, result)
            else:
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
                self.update_history(f"{expression} = {result}")

            # Set the flag to indicate the last action was an equals sign
            self.last_was_equals = True

        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Error")

    def update_history(self, entry):
        """
        Adds a new entry to the history log and updates the listbox.
        """
        self.history.append(entry)
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            self.history_listbox.insert(tk.END, item)
        self.history_listbox.yview_moveto(1.0)


def main():
    """
    Main function to create and run the GUI application.
    """
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
