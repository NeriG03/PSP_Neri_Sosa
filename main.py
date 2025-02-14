import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib import pyplot as plt
from psp_manager import PSPManager

class ActivitySelector(tk.Toplevel):
    def __init__(self, parent, activities):
        super().__init__(parent)
        self.title("Select Activity")
        self.selected_activity = None
        
        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10)
        
        self.listbox = tk.Listbox(frame, width=40, height=10)
        self.listbox.pack()
        
        for activity in activities:
            self.listbox.insert(tk.END, activity)
            
        ttk.Button(frame, text="Select", command=self.on_select).pack(pady=5)
        
        self.transient(parent)
        self.grab_set()
        
    def on_select(self):
        if self.listbox.curselection():
            self.selected_activity = self.listbox.get(self.listbox.curselection())
            self.destroy()

class TableViewer(tk.Toplevel):
    def __init__(self, parent, dataframe):
        super().__init__(parent)
        self.title("Activity Summary")
        self.geometry("800x400")

        # Create treeview
        self.tree = ttk.Treeview(self)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Add scrollbar
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        # Configure columns
        columns = list(dataframe.columns)
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        # Set column headings
        for column in columns:
            self.tree.heading(column, text=column.title())
            # Adjust column width based on content
            max_width = max(
                len(str(dataframe[column].max())),
                len(column)
            ) * 10
            self.tree.column(column, width=max_width)

        # Add data
        for i, row in dataframe.iterrows():
            values = []
            for column in columns:
                value = row[column]
                if isinstance(value, float):
                    value = f"{value:.2f}"
                values.append(value)
            self.tree.insert("", "end", values=values)

        # Add close button
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)

class PSPGUI:
    def __init__(self):
        self.psp = PSPManager()
        self.root = tk.Tk()
        self.root.title("PSP Manager")
        self.setup_gui()
        self.timer_id = None
        self.last_graph = None
        self.pause_timer_id = None
        self.is_paused = False

    def setup_gui(self):
        # Project Frame
        project_frame = ttk.LabelFrame(self.root, text="Project Management")
        project_frame.pack(padx=5, pady=5, fill="x")

        # Project Creation
        create_frame = ttk.Frame(project_frame)
        create_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(create_frame, text="New Project:").pack(side="left", padx=5)
        self.project_entry = ttk.Entry(create_frame)
        self.project_entry.pack(side="left", padx=5)
        ttk.Button(create_frame, text="Create Project", 
                  command=self.create_project).pack(side="left", padx=5)

        # Project Selection
        select_frame = ttk.Frame(project_frame)
        select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(select_frame, text="Select Project:").pack(side="left", padx=5)
        self.project_selector = ttk.Combobox(select_frame, state="readonly")
        self.project_selector.pack(side="left", padx=5)
        self.update_project_list()
        
        # Activity Frame (disabled initially)
        self.activity_frame = ttk.LabelFrame(self.root, text="Activity Management")
        self.activity_frame.pack(padx=5, pady=5, fill="x")
        self.activity_frame.pack_forget()  # Hide initially

        # Activity Selection
        activity_select_frame = ttk.Frame(self.activity_frame)
        activity_select_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(activity_select_frame, text="Activity:").pack(side="left", padx=5)
        self.activity_combobox = ttk.Combobox(activity_select_frame, 
                                            values=self.psp.PREDEFINED_ACTIVITIES,
                                            state="readonly")
        self.activity_combobox.pack(side="left", padx=5)

        # Comment Entry
        comment_frame = ttk.Frame(self.activity_frame)
        comment_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(comment_frame, text="Comment:").pack(side="left", padx=5)
        self.comment_entry = ttk.Entry(comment_frame, width=40)
        self.comment_entry.pack(side="left", padx=5)
        
        # Buttons Frame
        buttons_frame = ttk.Frame(self.activity_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="Start", 
                                     command=self.start_activity)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Pause", 
                                    command=self.stop_activity, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.resume_pause_button = ttk.Button(buttons_frame, text="Resume Work", 
                                            command=self.resume_from_pause,
                                            state="disabled")
        self.resume_pause_button.pack(side="left", padx=5)

        self.timer_label = ttk.Label(buttons_frame, text="Time: 0:00")
        self.timer_label.pack(side="left", padx=5)
        
        self.resume_button = ttk.Button(buttons_frame, text="Resume Activity", 
                                      command=self.show_activity_selector)
        self.resume_button.pack(side="left", padx=5)

        # Add pause timer and finish button
        self.pause_timer_label = ttk.Label(buttons_frame, text="Pause: 0:00")
        self.pause_timer_label.pack(side="left", padx=5)
        
        self.finish_button = ttk.Button(buttons_frame, text="Finish", 
                                      command=self.finish_activity,
                                      state="disabled")
        self.finish_button.pack(side="left", padx=5)

        # View Frame
        self.view_frame = ttk.LabelFrame(self.root, text="View Data")
        self.view_frame.pack(padx=5, pady=5, fill="x")
        self.view_frame.pack_forget()  # Hide initially

        ttk.Button(self.view_frame, text="Show Summary", 
                  command=self.show_summary).pack(side="left", padx=5)
        ttk.Button(self.view_frame, text="Show Graph", 
                  command=self.show_graph).pack(side="left", padx=5)

        # Bind project selection
        self.project_selector.bind('<<ComboboxSelected>>', self.on_project_selected)

    def update_project_list(self):
        projects = list(self.psp.projects.keys())
        self.project_selector['values'] = projects
        if projects:
            self.project_selector.set(projects[0])

    def create_project(self):
        name = self.project_entry.get()
        if name:
            self.psp.create_project(name)
            self.project_entry.delete(0, tk.END)
            self.update_project_list()

    def on_project_selected(self, event=None):
        project = self.project_selector.get()
        if project:
            self.psp.current_project = project
            # Mostrar frames
            self.activity_frame.pack(padx=5, pady=5, fill="x")
            self.view_frame.pack(padx=5, pady=5, fill="x")
            # Asegurar que los frames sean visibles
            self.activity_frame.lift()
            self.view_frame.lift()
            # Actualizar la interfaz
            self.root.update()
        else:
            self.activity_frame.pack_forget()
            self.view_frame.pack_forget()

    def update_timer(self):
        if self.psp.current_activity:
            elapsed = self.psp.get_elapsed_time()
            minutes = int(elapsed)
            seconds = int((elapsed - minutes) * 60)
            self.timer_label.config(text=f"Time: {minutes}:{seconds:02d}")
            self.timer_id = self.root.after(1000, self.update_timer)

    def update_pause_timer(self):
        if self.psp.pause_start_time:
            elapsed = self.psp.get_pause_time()
            minutes = int(elapsed)
            seconds = int((elapsed - minutes) * 60)
            self.pause_timer_label.config(text=f"Pause: {minutes}:{seconds:02d}")
            self.pause_timer_id = self.root.after(1000, self.update_pause_timer)

    def start_activity(self):
        if not self.psp.current_project:
            messagebox.showerror("Error", "Please select a project first")
            return
        activity = self.activity_combobox.get()
        comment = self.comment_entry.get()
        if activity:
            self.psp.start_activity(activity, comment)
            self.update_button_states(working=True)
            self.update_timer()

    def stop_activity(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.psp.pause_activity()
        self.is_paused = True
        self.update_button_states(paused=True)
        self.update_pause_timer()

    def resume_from_pause(self):
        if self.psp.resume_from_pause():
            if self.pause_timer_id:
                self.root.after_cancel(self.pause_timer_id)
                self.pause_timer_id = None
            self.is_paused = False
            self.update_button_states(working=True)
            self.update_timer()

    def update_button_states(self, working=False, paused=False):
        if working:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.resume_pause_button.config(state="disabled")
            self.finish_button.config(state="normal")
            self.resume_button.config(state="disabled")
        elif paused:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            self.resume_pause_button.config(state="normal")
            self.finish_button.config(state="normal")
            self.resume_button.config(state="disabled")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.resume_pause_button.config(state="disabled")
            self.finish_button.config(state="disabled")
            self.resume_button.config(state="normal")

    def finish_activity(self):
        if self.pause_timer_id:
            self.root.after_cancel(self.pause_timer_id)
            self.pause_timer_id = None
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        self.psp.finish_activity()
        self.is_paused = False
        self.update_button_states()
        self.activity_combobox.set('')
        self.comment_entry.delete(0, tk.END)
        self.timer_label.config(text="Time: 0:00")
        self.pause_timer_label.config(text="Pause: 0:00")
        self.show_graph()

    def show_activity_selector(self):
        activities = self.psp.get_activity_history()
        if not activities:
            messagebox.showinfo("Info", "No previous activities to resume")
            return
            
        dialog = ActivitySelector(self.root, activities)
        self.root.wait_window(dialog)
        
        if dialog.selected_activity:
            self.resume_activity(dialog.selected_activity)

    def resume_activity(self, activity_name):
        if self.psp.resume_activity(activity_name):
            self.activity_combobox.set(activity_name)
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.resume_button.config(state="disabled")
            self.update_timer()

    def show_summary(self):
        if self.psp.current_project:
            df = self.psp.get_project_summary(self.psp.current_project)
            if not df.empty:
                TableViewer(self.root, df)
            else:
                messagebox.showinfo("Info", "No activities to display")

    def show_graph(self):
        if self.psp.current_project:
            if self.last_graph:
                plt.close(self.last_graph)
            self.last_graph = self.psp.plot_project_times(self.psp.current_project)

    def run(self):
        # Cleanup timer on window close
        def on_closing():
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
            if self.pause_timer_id:
                self.root.after_cancel(self.pause_timer_id)
            self.root.destroy()
            
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = PSPGUI()
    app.run()
