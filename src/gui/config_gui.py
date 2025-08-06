#!/usr/bin/env python3
"""
GUI Configuration Interface for Superscalar Pipeline Simulator

This module provides a simple GUI for configuring the simulator parameters.
"""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

import yaml


class ConfigurationGUI:
    """Simple GUI for configuring the simulator."""
    
    def __init__(self):
        """Initialize the configuration GUI."""
        self.root = tk.Tk()
        self.root.title("Superscalar Pipeline Simulator - Configuration")
        self.root.geometry("800x600")
        
        # Configuration data
        self.config = self._load_default_config()
        
        # Create GUI elements
        self._create_widgets()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            'pipeline': {
                'num_stages': 6,
                'fetch_width': 4,
                'issue_width': 4,
                'execute_units': {
                    'ALU': {'count': 2},
                    'FPU': {'count': 1},
                    'LSU': {'count': 1}
                }
            },
            'branch_predictor': {
                'type': 'gshare',
                'num_entries': 1024,
                'history_length': 8
            },
            'cache': {
                'instruction_cache': {
                    'size': 32768,
                    'block_size': 64,
                    'associativity': 4
                },
                'data_cache': {
                    'size': 32768,
                    'block_size': 64,
                    'associativity': 4
                },
                'memory_size': 1048576
            },
            'simulation': {
                'max_cycles': 10000,
                'output_file': 'simulation_results.txt',
                'enable_visualization': False,
                'enable_profiling': True
            },
            'debug': {
                'enabled': False,
                'log_level': 'INFO'
            }
        }
    
    def _create_widgets(self):
        """Create GUI widgets."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pipeline tab
        pipeline_frame = ttk.Frame(notebook)
        notebook.add(pipeline_frame, text="Pipeline")
        self._create_pipeline_tab(pipeline_frame)
        
        # Branch Predictor tab
        bp_frame = ttk.Frame(notebook)
        notebook.add(bp_frame, text="Branch Predictor")
        self._create_branch_predictor_tab(bp_frame)
        
        # Cache tab
        cache_frame = ttk.Frame(notebook)
        notebook.add(cache_frame, text="Cache")
        self._create_cache_tab(cache_frame)
        
        # Simulation tab
        sim_frame = ttk.Frame(notebook)
        notebook.add(sim_frame, text="Simulation")
        self._create_simulation_tab(sim_frame)
        
        # Buttons frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Load Config", command=self._load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Config", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Run Simulator", command=self._run_simulator).pack(side=tk.RIGHT, padx=5)
    
    def _create_pipeline_tab(self, parent):
        """Create pipeline configuration tab."""
        # Pipeline parameters
        ttk.Label(parent, text="Pipeline Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Fetch width
        ttk.Label(frame, text="Fetch Width:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fetch_width_var = tk.StringVar(value=str(self.config['pipeline']['fetch_width']))
        ttk.Entry(frame, textvariable=self.fetch_width_var, width=10).grid(row=0, column=1, padx=10)
        
        # Issue width
        ttk.Label(frame, text="Issue Width:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.issue_width_var = tk.StringVar(value=str(self.config['pipeline']['issue_width']))
        ttk.Entry(frame, textvariable=self.issue_width_var, width=10).grid(row=1, column=1, padx=10)
        
        # Execution units
        ttk.Label(parent, text="Execution Units", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        
        units_frame = ttk.Frame(parent)
        units_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # ALU count
        ttk.Label(units_frame, text="ALU Count:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.alu_count_var = tk.StringVar(value=str(self.config['pipeline']['execute_units']['ALU']['count']))
        ttk.Entry(units_frame, textvariable=self.alu_count_var, width=10).grid(row=0, column=1, padx=10)
        
        # FPU count
        ttk.Label(units_frame, text="FPU Count:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fpu_count_var = tk.StringVar(value=str(self.config['pipeline']['execute_units']['FPU']['count']))
        ttk.Entry(units_frame, textvariable=self.fpu_count_var, width=10).grid(row=1, column=1, padx=10)
        
        # LSU count
        ttk.Label(units_frame, text="LSU Count:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.lsu_count_var = tk.StringVar(value=str(self.config['pipeline']['execute_units']['LSU']['count']))
        ttk.Entry(units_frame, textvariable=self.lsu_count_var, width=10).grid(row=2, column=1, padx=10)
    
    def _create_branch_predictor_tab(self, parent):
        """Create branch predictor configuration tab."""
        ttk.Label(parent, text="Branch Predictor Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Predictor type
        ttk.Label(frame, text="Predictor Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bp_type_var = tk.StringVar(value=self.config['branch_predictor']['type'])
        bp_combo = ttk.Combobox(frame, textvariable=self.bp_type_var, values=['always_taken', 'bimodal', 'gshare'])
        bp_combo.grid(row=0, column=1, padx=10, sticky=tk.W)
        
        # Number of entries
        ttk.Label(frame, text="Number of Entries:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bp_entries_var = tk.StringVar(value=str(self.config['branch_predictor']['num_entries']))
        ttk.Entry(frame, textvariable=self.bp_entries_var, width=10).grid(row=1, column=1, padx=10)
        
        # History length
        ttk.Label(frame, text="History Length:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.bp_history_var = tk.StringVar(value=str(self.config['branch_predictor']['history_length']))
        ttk.Entry(frame, textvariable=self.bp_history_var, width=10).grid(row=2, column=1, padx=10)
    
    def _create_cache_tab(self, parent):
        """Create cache configuration tab."""
        ttk.Label(parent, text="Cache Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Instruction cache
        ttk.Label(parent, text="Instruction Cache", font=('Arial', 10, 'bold')).pack(pady=(10, 5))
        
        icache_frame = ttk.Frame(parent)
        icache_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(icache_frame, text="Size (bytes):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.icache_size_var = tk.StringVar(value=str(self.config['cache']['instruction_cache']['size']))
        ttk.Entry(icache_frame, textvariable=self.icache_size_var, width=10).grid(row=0, column=1, padx=10)
        
        ttk.Label(icache_frame, text="Block Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.icache_block_var = tk.StringVar(value=str(self.config['cache']['instruction_cache']['block_size']))
        ttk.Entry(icache_frame, textvariable=self.icache_block_var, width=10).grid(row=1, column=1, padx=10)
        
        # Data cache
        ttk.Label(parent, text="Data Cache", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        
        dcache_frame = ttk.Frame(parent)
        dcache_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(dcache_frame, text="Size (bytes):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dcache_size_var = tk.StringVar(value=str(self.config['cache']['data_cache']['size']))
        ttk.Entry(dcache_frame, textvariable=self.dcache_size_var, width=10).grid(row=0, column=1, padx=10)
        
        ttk.Label(dcache_frame, text="Block Size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.dcache_block_var = tk.StringVar(value=str(self.config['cache']['data_cache']['block_size']))
        ttk.Entry(dcache_frame, textvariable=self.dcache_block_var, width=10).grid(row=1, column=1, padx=10)
        
        # Memory size
        ttk.Label(parent, text="Main Memory", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        
        mem_frame = ttk.Frame(parent)
        mem_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(mem_frame, text="Memory Size (bytes):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.memory_size_var = tk.StringVar(value=str(self.config['cache']['memory_size']))
        ttk.Entry(mem_frame, textvariable=self.memory_size_var, width=15).grid(row=0, column=1, padx=10)
    
    def _create_simulation_tab(self, parent):
        """Create simulation configuration tab."""
        ttk.Label(parent, text="Simulation Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Max cycles
        ttk.Label(frame, text="Max Cycles:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_cycles_var = tk.StringVar(value=str(self.config['simulation']['max_cycles']))
        ttk.Entry(frame, textvariable=self.max_cycles_var, width=10).grid(row=0, column=1, padx=10)
        
        # Output file
        ttk.Label(frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_file_var = tk.StringVar(value=self.config['simulation']['output_file'])
        ttk.Entry(frame, textvariable=self.output_file_var, width=30).grid(row=1, column=1, padx=10)
        
        # Checkboxes
        self.enable_viz_var = tk.BooleanVar(value=self.config['simulation']['enable_visualization'])
        ttk.Checkbutton(frame, text="Enable Visualization", variable=self.enable_viz_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.enable_prof_var = tk.BooleanVar(value=self.config['simulation']['enable_profiling'])
        ttk.Checkbutton(frame, text="Enable Profiling", variable=self.enable_prof_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Debug options
        ttk.Label(parent, text="Debug Options", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        
        debug_frame = ttk.Frame(parent)
        debug_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.debug_enabled_var = tk.BooleanVar(value=self.config['debug']['enabled'])
        ttk.Checkbutton(debug_frame, text="Enable Debug", variable=self.debug_enabled_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(debug_frame, text="Log Level:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.log_level_var = tk.StringVar(value=self.config['debug']['log_level'])
        log_combo = ttk.Combobox(debug_frame, textvariable=self.log_level_var, values=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        log_combo.grid(row=1, column=1, padx=10, sticky=tk.W)
    
    def _update_config_from_gui(self):
        """Update configuration from GUI values."""
        try:
            # Pipeline
            self.config['pipeline']['fetch_width'] = int(self.fetch_width_var.get())
            self.config['pipeline']['issue_width'] = int(self.issue_width_var.get())
            self.config['pipeline']['execute_units']['ALU']['count'] = int(self.alu_count_var.get())
            self.config['pipeline']['execute_units']['FPU']['count'] = int(self.fpu_count_var.get())
            self.config['pipeline']['execute_units']['LSU']['count'] = int(self.lsu_count_var.get())
            
            # Branch predictor
            self.config['branch_predictor']['type'] = self.bp_type_var.get()
            self.config['branch_predictor']['num_entries'] = int(self.bp_entries_var.get())
            self.config['branch_predictor']['history_length'] = int(self.bp_history_var.get())
            
            # Cache
            self.config['cache']['instruction_cache']['size'] = int(self.icache_size_var.get())
            self.config['cache']['instruction_cache']['block_size'] = int(self.icache_block_var.get())
            self.config['cache']['data_cache']['size'] = int(self.dcache_size_var.get())
            self.config['cache']['data_cache']['block_size'] = int(self.dcache_block_var.get())
            self.config['cache']['memory_size'] = int(self.memory_size_var.get())
            
            # Simulation
            self.config['simulation']['max_cycles'] = int(self.max_cycles_var.get())
            self.config['simulation']['output_file'] = self.output_file_var.get()
            self.config['simulation']['enable_visualization'] = self.enable_viz_var.get()
            self.config['simulation']['enable_profiling'] = self.enable_prof_var.get()
            
            # Debug
            self.config['debug']['enabled'] = self.debug_enabled_var.get()
            self.config['debug']['log_level'] = self.log_level_var.get()
            
            return True
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values: {e}")
            return False
    
    def _load_config(self):
        """Load configuration from file."""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("YAML files", "*.yaml"), ("YAML files", "*.yml"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename) as f:
                    self.config = yaml.safe_load(f)
                self._update_gui_from_config()
                messagebox.showinfo("Success", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def _save_config(self):
        """Save configuration to file."""
        if not self._update_config_from_gui():
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("YAML files", "*.yml"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                messagebox.showinfo("Success", "Configuration saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def _reset_config(self):
        """Reset configuration to defaults."""
        self.config = self._load_default_config()
        self._update_gui_from_config()
        messagebox.showinfo("Reset", "Configuration reset to defaults!")
    
    def _update_gui_from_config(self):
        """Update GUI from configuration values."""
        # Pipeline
        self.fetch_width_var.set(str(self.config['pipeline']['fetch_width']))
        self.issue_width_var.set(str(self.config['pipeline']['issue_width']))
        self.alu_count_var.set(str(self.config['pipeline']['execute_units']['ALU']['count']))
        self.fpu_count_var.set(str(self.config['pipeline']['execute_units']['FPU']['count']))
        self.lsu_count_var.set(str(self.config['pipeline']['execute_units']['LSU']['count']))
        
        # Branch predictor
        self.bp_type_var.set(self.config['branch_predictor']['type'])
        self.bp_entries_var.set(str(self.config['branch_predictor']['num_entries']))
        self.bp_history_var.set(str(self.config['branch_predictor']['history_length']))
        
        # Cache
        self.icache_size_var.set(str(self.config['cache']['instruction_cache']['size']))
        self.icache_block_var.set(str(self.config['cache']['instruction_cache']['block_size']))
        self.dcache_size_var.set(str(self.config['cache']['data_cache']['size']))
        self.dcache_block_var.set(str(self.config['cache']['data_cache']['block_size']))
        self.memory_size_var.set(str(self.config['cache']['memory_size']))
        
        # Simulation
        self.max_cycles_var.set(str(self.config['simulation']['max_cycles']))
        self.output_file_var.set(self.config['simulation']['output_file'])
        self.enable_viz_var.set(self.config['simulation']['enable_visualization'])
        self.enable_prof_var.set(self.config['simulation']['enable_profiling'])
        
        # Debug
        self.debug_enabled_var.set(self.config['debug']['enabled'])
        self.log_level_var.set(self.config['debug']['log_level'])
    
    def _run_simulator(self):
        """Run the simulator with current configuration."""
        if not self._update_config_from_gui():
            return
        
        # Save current config to temporary file
        temp_config = Path("temp_config.yaml")
        try:
            with open(temp_config, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            # Ask for benchmark file
            benchmark_file = filedialog.askopenfilename(
                title="Select Benchmark File",
                filetypes=[("Assembly files", "*.asm"), ("All files", "*.*")]
            )
            
            if benchmark_file:
                # Show info about running simulator
                messagebox.showinfo(
                    "Running Simulator",
                    f"Simulator will run with:\n"
                    f"Config: {temp_config}\n"
                    f"Benchmark: {benchmark_file}\n\n"
                    f"Command to run manually:\n"
                    f"python src/main.py --config {temp_config} --benchmark {benchmark_file}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to prepare simulation: {e}")
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Main function to run the configuration GUI."""
    try:
        app = ConfigurationGUI()
        app.run()
    except ImportError:
        print("GUI dependencies not available. Please install tkinter.")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On macOS: tkinter should be included with Python")
        print("On Windows: tkinter should be included with Python")
    except Exception as e:
        print(f"Error running GUI: {e}")


if __name__ == "__main__":
    main()
