import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys

class DynoPlotterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynomometer Data Plotter")
        
        self.data_files = {}
        self.plots = []
        
        # Dropdown menu to select file
        self.selected_file_var = tk.StringVar(value="")
        ttk.Label(root, text="Select File:").grid(row=0, column=0, padx=5, pady=5)
        self.file_menu = ttk.Combobox(root, textvariable=self.selected_file_var, values=list(self.data_files.keys()))
        self.file_menu.grid(row=0, column=1, padx=5, pady=5)

        # Create dropdowns for selecting x and y axes
        self.x_axis_var = tk.StringVar(value="")
        self.y_axis_var = tk.StringVar(value="")
        
        ttk.Label(root, text="Select X-axis:").grid(row=1, column=0, padx=5, pady=5)
        self.x_axis_menu = ttk.Combobox(root, textvariable=self.x_axis_var)
        self.x_axis_menu.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(root, text="Select Y-axis:").grid(row=2, column=0, padx=5, pady=5)
        self.y_axis_menu = ttk.Combobox(root, textvariable=self.y_axis_var)
        self.y_axis_menu.grid(row=2, column=1, padx=5, pady=5)

        # Label entry for custom plot label
        ttk.Label(root, text="Custom Plot Label:").grid(row=3, column=0, padx=5, pady=5)
        self.custom_label_var = tk.StringVar(value="")
        self.custom_label_entry = ttk.Entry(root, textvariable=self.custom_label_var)
        self.custom_label_entry.grid(row=3, column=1, padx=5, pady=5)

        # Checkbox for legend on the side
        self.legend_side_var = tk.BooleanVar(value=False)
        self.legend_side_check = ttk.Checkbutton(root, text="Legend on the side", variable=self.legend_side_var, command=self.update_legend_position)
        self.legend_side_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        
        # Button to load additional files
        load_file_button = ttk.Button(root, text="Load Additional File", command=self.load_additional_file)
        load_file_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        # Button to plot the data
        plot_button = ttk.Button(root, text="Add Plot", command=self.add_plot)
        plot_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
        
        # Button to remove the last plot
        remove_plot_button = ttk.Button(root, text="Remove Last Plot", command=self.remove_last_plot)
        remove_plot_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        
        # Button to save the plot
        save_button = ttk.Button(root, text="Save Plot", command=self.save_plot)
        save_button.grid(row=8, column=0, columnspan=2, padx=5, pady=5)
        
        # Figure and canvas for plotting
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, root)
        self.canvas.get_tk_widget().grid(row=9, column=0, columnspan=2)
    
    def load_initial_file(self, filepath):
        filename = os.path.basename(filepath)
        data = pd.read_csv(filepath)
        self.data_files[filename] = data
        self.update_file_menu()
        self.update_axis_menus()
    
    def load_additional_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filepath:
            filename = os.path.basename(filepath)
            data = pd.read_csv(filepath)
            self.data_files[filename] = data
            self.update_file_menu()
            self.update_axis_menus()
    
    def update_file_menu(self):
        self.file_menu['values'] = list(self.data_files.keys())
        if not self.selected_file_var.get():
            self.selected_file_var.set(list(self.data_files.keys())[0])
    
    def update_axis_menus(self):
        selected_file = self.selected_file_var.get()
        if selected_file:
            columns = self.data_files[selected_file].columns.tolist()
            self.x_axis_menu['values'] = columns
            self.y_axis_menu['values'] = columns
            if not self.x_axis_var.get():
                self.x_axis_var.set(columns[0])
            if not self.y_axis_var.get():
                self.y_axis_var.set(columns[1])
    
    def add_plot(self):
        selected_file = self.selected_file_var.get()
        if selected_file:
            data = self.data_files[selected_file]
            x_axis = self.x_axis_var.get()
            y_axis = self.y_axis_var.get()
            
            label = self.custom_label_var.get()
            if not label:
                label = f"{y_axis} vs {x_axis} ({selected_file})"
            
            plot_line, = self.ax.plot(data[x_axis], data[y_axis], label=label)
            self.plots.append(plot_line)
            
            self.ax.set_xlabel(x_axis)
            self.ax.set_ylabel(y_axis)
            
            self.update_legend()
            self.canvas.draw()

    def remove_last_plot(self):
        if self.plots:
            plot_line = self.plots.pop()
            plot_line.remove()
            self.update_legend()
            self.canvas.draw()

    def update_legend(self):
        if self.legend_side_var.get():
            self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            self.figure.set_size_inches(8, 4)  # Resize canvas to fit the legend on the side
        else:
            self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
            self.figure.set_size_inches(6, 4)  # Resize canvas to fit the legend on top

    def update_legend_position(self):
        self.update_legend()
        self.canvas.draw()

    def save_plot(self):
        filetypes = [("PNG files", "*.png"), ("PDF files", "*.pdf")]
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)
        
        if filepath:
            self.figure.savefig(filepath)
            messagebox.showinfo("Save Plot", f"Plot saved as {filepath}")

def load_initial_data():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    
    if not filepath:
        messagebox.showerror("Error", "No file selected!")
        sys.exit()
    
    return filepath

if __name__ == "__main__":
    root = tk.Tk()
    app = DynoPlotterApp(root)
    initial_file = load_initial_data()
    app.load_initial_file(initial_file)
    root.mainloop()
