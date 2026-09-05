import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
import calendar
from datetime import datetime, timedelta

# Save next to the script/executable (works for .py and PyInstaller-built exe)
if getattr(sys, "frozen", False):
    # Running as frozen executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as a normal .py file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_PATH = os.path.join(BASE_DIR, "calorie_counter_save.json")

class CalorieCounter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calorie Counter")
        self.resizable(False, False)
        self.records = self.load_records()
        self.current_date = datetime.now().date()
        self.selected_date = None  # No date selected initially

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Tab 1 - Calendar with Counter
        self.calendar_frame = tk.Frame(self.notebook)
        self.notebook.add(self.calendar_frame, text="Calendar")
        self.setup_calendar_tab()

        # Tab 2 - Backoffice
        self.backoffice_frame = tk.Frame(self.notebook)
        self.notebook.add(self.backoffice_frame, text="Backoffice")
        self.setup_backoffice_tab()

        # Keyboard bindings
        self.bind("<Return>", lambda e: self.add_custom())
        

        # Ensure save on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_tab_changed(self, event):
        """Handle tab change - reset calendar view when switching to Calendar tab"""
        if self.notebook.index(self.notebook.select()) == 0:  # Calendar tab
            self.selected_date = None
            self.hide_counter_and_history()
            self.show_calendar()
            self.build_calendar()

    def setup_calendar_tab(self):
        """Setup the calendar tab with calendar and counter/history side by side"""
        main_container = tk.Frame(self.calendar_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - Calendar
        self.left_frame = tk.Frame(main_container)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.cal_frame = tk.Frame(self.left_frame)
        self.cal_frame.pack()

        # Right side container - Counter and History (side by side)
        self.right_container = tk.Frame(main_container)

        # Counter section (left of right side)
        self.counter_container = tk.Frame(self.right_container)

        # Back button
        back_frame = tk.Frame(self.counter_container)
        back_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        tk.Button(back_frame, text="← Back", command=self.back_to_calendar).pack(side=tk.LEFT)

        tk.Label(self.counter_container, text="Add Record", font=("Segoe UI", 12, "bold")).pack()

        # Total display for selected day
        self.total_label = tk.Label(self.counter_container, text="Select a day", font=("Segoe UI", 16), padx=10, pady=10)
        self.total_label.pack()

        # Quick add buttons (row 1)
        buttons_frame_1 = tk.Frame(self.counter_container)
        buttons_frame_1.pack()
        tk.Button(buttons_frame_1, text="+50", width=8, height=2, command=lambda: self.add(50)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(buttons_frame_1, text="+150", width=8, height=2, command=lambda: self.add(150)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(buttons_frame_1, text="+500", width=8, height=2, command=lambda: self.add(500)).pack(side=tk.LEFT, padx=3, pady=3)

        # Quick subtract buttons (row 2)
        buttons_frame_2 = tk.Frame(self.counter_container)
        buttons_frame_2.pack()
        tk.Button(buttons_frame_2, text="-50", width=8, height=2, command=lambda: self.subtract(50)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(buttons_frame_2, text="-150", width=8, height=2, command=lambda: self.subtract(150)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(buttons_frame_2, text="-500", width=8, height=2, command=lambda: self.subtract(500)).pack(side=tk.LEFT, padx=3, pady=3)

        # Custom entry and +/- buttons
        entry_frame = tk.Frame(self.counter_container)
        entry_frame.pack()
        self.custom_entry = tk.Entry(entry_frame, width=10, justify="center")
        self.custom_entry.pack(side=tk.LEFT, padx=3, pady=3)
        self.custom_entry.insert(0, "0")
        tk.Button(entry_frame, text="+", width=8, height=2, command=self.add_custom).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(entry_frame, text="-", width=8, height=2, command=self.subtract_custom).pack(side=tk.LEFT, padx=3, pady=3)

        # History section (right of right side)
        self.history_container = tk.Frame(self.right_container)

        # Table header with fixed widths
        header_frame = tk.Frame(self.history_container)
        header_frame.pack(fill=tk.X, padx=5, pady=(0, 2))

        tk.Label(header_frame, text="Timestamp", font=("Segoe UI", 9, "bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=1)
        tk.Label(header_frame, text="Calories", font=("Segoe UI", 9, "bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        tk.Label(header_frame, text="Delete", font=("Segoe UI", 9, "bold"), width=5, anchor="center").pack(side=tk.LEFT, padx=1)

        # Separator
        tk.Frame(self.history_container, height=1, bg="gray").pack(fill=tk.X, padx=5, pady=1)

        # Scrollable history
        self.history_canvas = tk.Canvas(self.history_container, height=300, width=250, highlightthickness=0, bg="white")
        scrollbar = tk.Scrollbar(self.history_container, orient="vertical", command=self.history_canvas.yview)
        self.history_scrollable_frame = tk.Frame(self.history_canvas, bg="white")

        self.history_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        )

        self.history_canvas.create_window((0, 0), window=self.history_scrollable_frame, anchor="nw")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        self.history_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.history_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.history_canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.build_calendar()

    def hide_counter_and_history(self):
        """Hide counter and history sections when no date is selected"""
        self.counter_container.pack_forget()
        self.history_container.pack_forget()
        self.right_container.pack_forget()
        self.total_label.config(text="Select a day")

    def show_counter_and_history(self):
        """Show counter and history sections when a date is selected"""
        self.right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.counter_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.history_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def hide_calendar(self):
        """Hide calendar"""
        self.left_frame.pack_forget()

    def show_calendar(self):
        """Show calendar"""
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    def back_to_calendar(self):
        """Go back to calendar view"""
        self.selected_date = None
        self.hide_counter_and_history()
        self.show_calendar()
        self.build_calendar()

    def build_calendar(self):
        """Build the calendar widget for the current month"""
        # Clear previous calendar
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        # Month/Year navigation
        nav_frame = tk.Frame(self.cal_frame)
        nav_frame.pack()

        tk.Button(nav_frame, text="<", command=self.prev_month).pack(side=tk.LEFT, padx=5)
        month_label = tk.Label(nav_frame, text=f"{self.current_date.strftime('%B %Y')}", font=("Segoe UI", 12, "bold"), width=20)
        month_label.pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text=">", command=self.next_month).pack(side=tk.LEFT, padx=5)

        # Calendar grid
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)

        # Days of week header
        days_frame = tk.Frame(self.cal_frame)
        days_frame.pack()
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            tk.Label(days_frame, text=day, font=("Segoe UI", 9, "bold"), width=5).pack(side=tk.LEFT)

        # Calendar days
        for week in cal:
            week_frame = tk.Frame(self.cal_frame)
            week_frame.pack()
            for day in week:
                if day == 0:
                    tk.Label(week_frame, text="", width=5).pack(side=tk.LEFT)
                else:
                    date_obj = datetime(self.current_date.year, self.current_date.month, day).date()
                    day_total = self.get_day_total(date_obj)

                    # Highlight today
                    is_today = date_obj == datetime.now().date()
                    
                    if is_today:
                        bg_color = "#e3f2fd"
                        fg_color = "black"
                    else:
                        bg_color = "white"
                        fg_color = "black"

                    # Check if has records
                    has_records = any(
                        record["date"] == str(date_obj)
                        for record in self.records
                    )
                    font_weight = "bold" if has_records else "normal"

                    btn = tk.Button(
                        week_frame,
                        text=f"{day}\n{day_total}",
                        width=5,
                        height=3,
                        bg=bg_color,
                        fg=fg_color,
                        font=("Segoe UI", 8, font_weight),
                        command=lambda d=date_obj: self.select_date(d)
                    )
                    btn.pack(side=tk.LEFT, padx=1, pady=1)

    def prev_month(self):
        """Navigate to previous month"""
        first_day = self.current_date.replace(day=1)
        self.current_date = first_day - timedelta(days=1)
        self.build_calendar()

    def next_month(self):
        """Navigate to next month"""
        last_day = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = (last_day - timedelta(days=last_day.day - 1)).replace(day=1)
        self.build_calendar()

    def select_date(self, date_obj):
        """Select a date and update display"""
        self.selected_date = date_obj
        self.hide_calendar()
        self.show_counter_and_history()
        self.total_label.config(text=self._format_total())
        self.update_history_display()

    def update_history_display(self):
        """Update the history panel with records for the selected date"""
        if self.selected_date is None:
            return

        # Clear previous entries without flickering
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        # Get records for selected date and sort by timestamp descending
        records = self.get_day_records(self.selected_date)
        records_sorted = sorted(records, key=lambda r: r["timestamp"], reverse=True)

        if not records_sorted:
            tk.Label(self.history_scrollable_frame, text="No records", fg="gray", bg="white").pack(pady=10)
        else:
            # Display each record
            for record in records_sorted:
                record_frame = tk.Frame(self.history_scrollable_frame, bg="white")
                record_frame.pack(fill=tk.X, padx=0, pady=0)

                # Timestamp
                dt = datetime.fromisoformat(record["timestamp"])
                time_str = dt.strftime("%H:%M:%S")
                time_label = tk.Label(record_frame, text=time_str, font=("Segoe UI", 9), width=12, anchor="w", bg="white")
                time_label.pack(side=tk.LEFT, padx=1, pady=2)

                # Amount (with color coding)
                amount = record["amount"]
                color = "green" if amount > 0 else "red"
                sign = "+" if amount > 0 else ""

                amount_label = tk.Label(record_frame, text=f"{sign}{amount}", fg=color, font=("Segoe UI", 9), width=12, anchor="w", bg="white")
                amount_label.pack(side=tk.LEFT, padx=1, pady=2, expand=True, fill=tk.X)

                # Delete button
                delete_btn = tk.Button(
                    record_frame,
                    text="✕",
                    fg="red",
                    font=("Segoe UI", 8, "bold"),
                    command=lambda r=record: self.delete_record(r),
                    relief=tk.FLAT,
                    width=4,
                    height=1,
                    bg="white",
                    activebackground="white"
                )
                delete_btn.pack(side=tk.LEFT, padx=1, pady=2)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        try:
            if self.history_canvas.winfo_viewable():
                if event.num == 5 or event.delta < 0:
                    self.history_canvas.yview_scroll(1, "units")
                elif event.num == 4 or event.delta > 0:
                    self.history_canvas.yview_scroll(-1, "units")
        except:
            pass

    def setup_backoffice_tab(self):
        """Setup the backoffice tab"""
        title = tk.Label(self.backoffice_frame, text="Backoffice", font=("Segoe UI", 16, "bold"), padx=20, pady=20)
        title.pack()

        # Wipe all data button
        wipe_all_btn = tk.Button(
            self.backoffice_frame,
            text="Wipe All Data",
            fg="white",
            bg="#dc3545",
            font=("Segoe UI", 12),
            command=self.wipe_all_data,
            width=30,
            pady=10
        )
        wipe_all_btn.pack(padx=20, pady=10)

        # Wipe current day data button
        wipe_day_btn = tk.Button(
            self.backoffice_frame,
            text="Wipe Current Day Data",
            fg="white",
            bg="#fd7e14",
            font=("Segoe UI", 12),
            command=self.wipe_current_day,
            width=30,
            pady=10
        )
        wipe_day_btn.pack(padx=20, pady=10)

        # Info label
        info_label = tk.Label(
            self.backoffice_frame,
            text="Total Records: 0",
            font=("Segoe UI", 10),
            fg="gray"
        )
        info_label.pack(padx=20, pady=20)
        self.info_label = info_label

        self.update_backoffice_info()

    def update_backoffice_info(self):
        """Update backoffice info display"""
        total_records = len(self.records)
        today_records = len(self.get_day_records(datetime.now().date()))
        self.info_label.config(text=f"Total Records: {total_records} | Today's Records: {today_records}")

    def wipe_all_data(self):
        """Wipe all data with confirmation"""
        if messagebox.askyesno("Confirm", "Are you sure you want to wipe ALL data? This cannot be undone."):
            self.records = []
            self.save_records()
            self.update_backoffice_info()
            self.update_history_display()
            messagebox.showinfo("Success", "All data has been wiped.")

    def wipe_current_day(self):
        """Wipe current day data with confirmation"""
        if messagebox.askyesno("Confirm", f"Are you sure you want to wipe today's data ({datetime.now().date()})? This cannot be undone."):
            date_str = str(datetime.now().date())
            self.records = [r for r in self.records if r["date"] != date_str]
            self.save_records()
            self.update_backoffice_info()
            if self.selected_date == datetime.now().date():
                self.update_history_display()
            messagebox.showinfo("Success", "Today's data has been wiped.")

    def _format_total(self):
        if self.selected_date is None:
            return "Select a day"
        total = self.get_day_total(self.selected_date)
        date_str = self.selected_date.strftime("%d/%m") if self.selected_date != datetime.now().date() else "Today"
        return f"{date_str}: {total} kcal"

    def load_records(self):
        """Load all records from the save file"""
        try:
            if os.path.exists(SAVE_PATH):
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("records", [])
        except Exception:
            pass
        return []

    def save_records(self):
        """Save all records to the save file"""
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump({"records": self.records}, f, indent=2)
        except Exception:
            pass

    def get_day_total(self, date_obj):
        """Calculate total calories for a specific day"""
        date_str = str(date_obj)
        total = 0
        for record in self.records:
            if record["date"] == date_str:
                total += record["amount"]
        return total

    def get_day_records(self, date_obj):
        """Get all records for a specific day"""
        date_str = str(date_obj)
        return [r for r in self.records if r["date"] == date_str]

    def add(self, amount):
        try:
            amount = int(amount)
        except ValueError:
            return

        if self.selected_date is None:
            return

        record = {
            "date": str(self.selected_date),
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }
        self.records.append(record)
        self.save_records()
        self.total_label.config(text=self._format_total())
        self.update_backoffice_info()
        self.update_history_display()

    def subtract(self, amount):
        try:
            amount = int(amount)
        except ValueError:
            return

        if self.selected_date is None:
            return

        # Check if subtracting would go below 0
        current_total = self.get_day_total(self.selected_date)
        if current_total - amount < 0:
            messagebox.showwarning("Warning", "Cannot subtract. Daily calories cannot go below 0.")
            return

        record = {
            "date": str(self.selected_date),
            "amount": -amount,
            "timestamp": datetime.now().isoformat()
        }
        self.records.append(record)
        self.save_records()
        self.total_label.config(text=self._format_total())
        self.update_backoffice_info()
        self.update_history_display()

    def add_custom(self):
        text = self.custom_entry.get().strip()
        if not text:
            return
        
        try:
            if int(text) == 0:
                return
            value = int(text)
        except ValueError:
            messagebox.showerror("Invalid", "Please enter a valid integer calorie amount.")
            return
        self.add(value)

    def subtract_custom(self):
        text = self.custom_entry.get().strip()
        if not text:
            return
        try:
            if int(text) == 0:
                return
            value = int(text)
        except ValueError:
            messagebox.showerror("Invalid", "Please enter a valid integer calorie amount.")
            return
        self.subtract(value)

    def reset(self):
        """Reset total for selected day (delete all records for that day)"""
        if self.selected_date is None:
            return
        date_str = str(self.selected_date)
        self.records = [r for r in self.records if r["date"] != date_str]
        self.save_records()
        self.total_label.config(text=self._format_total())
        self.update_backoffice_info()
        self.update_history_display()

    def delete_record(self, record):
        """Delete a specific record"""
        if record in self.records:
            # Check if deleting would go below 0
            current_total = self.get_day_total(self.selected_date)
            new_total = current_total - record["amount"]
            
            if new_total < 0:
                messagebox.showwarning("Warning", "Cannot delete. Daily calories cannot go below 0.")
                return
            
            self.records.remove(record)
            self.save_records()
            self.total_label.config(text=self._format_total())
            self.update_backoffice_info()
            self.update_history_display()

    def on_close(self):
        """Save on close and exit"""
        self.save_records()
        self.destroy()

if __name__ == "__main__":
    app = CalorieCounter()
    app.mainloop()