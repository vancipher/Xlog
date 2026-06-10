"""
XLog Desktop Application
نظام إدارة الحضور بتقنية RFID
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import time
import csv
import os

# Import the XLog system
try:
    from xlog_system import XLogSystem
    RFID_AVAILABLE = True
except ImportError:
    RFID_AVAILABLE = False
    print("Warning: xlog_system not available. Running in demo mode.")


class XLogDesktopApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window initially
        
        # App settings
        self.username = "admin"
        self.password = "xlog2024"
        self.logged_in = False
        
        # Initialize XLog system
        if RFID_AVAILABLE:
            try:
                self.xlog = XLogSystem()
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في تهيئة نظام RFID:\n{str(e)}")
                self.xlog = None
        else:
            self.xlog = None
        
        # Session monitoring
        self.monitoring = False
        self.monitor_thread = None
        
        # Show login window
        self.show_login()
    
    def show_login(self):
        """Display login window"""
        self.login_window = tk.Toplevel()
        self.login_window.title("XLog - تسجيل الدخول")
        self.login_window.geometry("400x500")
        self.login_window.resizable(False, False)
        
        # Center the window
        self.center_window(self.login_window, 400, 500)
        
        # Configure colors
        bg_color = "#667eea"
        self.login_window.configure(bg=bg_color)
        
        # Logo/Title Frame
        title_frame = tk.Frame(self.login_window, bg=bg_color)
        title_frame.pack(pady=40)
        
        # Title
        title_label = tk.Label(
            title_frame,
            text="🔐 نظام XLog",
            font=("Arial", 28, "bold"),
            bg=bg_color,
            fg="white"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="نظام إدارة الحضور بتقنية RFID",
            font=("Arial", 12),
            bg=bg_color,
            fg="white"
        )
        subtitle_label.pack(pady=10)
        
        # Login Form Frame
        form_frame = tk.Frame(self.login_window, bg="white", padx=40, pady=30)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        # Username
        tk.Label(
            form_frame,
            text="اسم المستخدم",
            font=("Arial", 11),
            bg="white",
            anchor="e"
        ).pack(fill=tk.X, pady=(10, 5))
        
        self.username_entry = ttk.Entry(form_frame, font=("Arial", 11))
        self.username_entry.pack(fill=tk.X, ipady=8)
        self.username_entry.insert(0, "admin")
        
        # Password
        tk.Label(
            form_frame,
            text="كلمة المرور",
            font=("Arial", 11),
            bg="white",
            anchor="e"
        ).pack(fill=tk.X, pady=(20, 5))
        
        self.password_entry = ttk.Entry(form_frame, font=("Arial", 11), show="●")
        self.password_entry.pack(fill=tk.X, ipady=8)
        
        # Error label
        self.error_label = tk.Label(
            form_frame,
            text="",
            font=("Arial", 9),
            bg="white",
            fg="#ef4444"
        )
        self.error_label.pack(pady=10)
        
        # Login button
        login_btn = tk.Button(
            form_frame,
            text="دخول",
            font=("Arial", 12, "bold"),
            bg="#2563eb",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            command=self.login
        )
        login_btn.pack(fill=tk.X, ipady=10, pady=(10, 0))
        
        # Version info
        tk.Label(
            form_frame,
            text="الإصدار 1.0 - 2024",
            font=("Arial", 8),
            bg="white",
            fg="#64748b"
        ).pack(pady=(20, 0))
        
        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Handle window close
        self.login_window.protocol("WM_DELETE_WINDOW", self.root.quit)
    
    def login(self):
        """Handle login authentication"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == self.username and password == self.password:
            self.logged_in = True
            self.login_window.destroy()
            self.show_main_window()
        else:
            self.error_label.config(text="اسم المستخدم أو كلمة المرور غير صحيحة")
    
    def show_main_window(self):
        """Display main application window"""
        self.root.deiconify()
        self.root.title("XLog - نظام إدارة الحضور")
        self.root.geometry("1200x700")
        
        # Center the window
        self.center_window(self.root, 1200, 700)
        
        # Configure style
        self.setup_styles()
        
        # Create header
        self.create_header()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_students_tab()
        self.create_session_tab()
        self.create_history_tab()
        
        # Start session monitor
        if self.xlog:
            self.start_session_monitor()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TNotebook', background='#f8fafc')
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Arial', 10))
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
    
    def create_header(self):
        """Create application header"""
        header = tk.Frame(self.root, bg="#2563eb", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text="🔐 نظام XLog - إدارة الحضور",
            font=("Arial", 18, "bold"),
            bg="#2563eb",
            fg="white"
        )
        title_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Session indicator
        self.session_indicator_frame = tk.Frame(header, bg="#64748b", padx=15, pady=5)
        self.session_indicator_frame.pack(side=tk.RIGHT, padx=20)
        
        self.session_indicator_label = tk.Label(
            self.session_indicator_frame,
            text="● لا توجد جلسة نشطة",
            font=("Arial", 10),
            bg="#64748b",
            fg="white"
        )
        self.session_indicator_label.pack()
        
        # Logout button
        logout_btn = tk.Button(
            header,
            text="تسجيل الخروج",
            font=("Arial", 10),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.logout
        )
        logout_btn.pack(side=tk.LEFT, padx=20)
    
    def create_students_tab(self):
        """Create students management tab"""
        students_frame = ttk.Frame(self.notebook)
        self.notebook.add(students_frame, text="👥 إدارة الطلاب")
        
        # Top bar
        top_frame = tk.Frame(students_frame, bg="white", pady=15)
        top_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(
            top_frame,
            text="إدارة الطلاب",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        tk.Button(
            top_frame,
            text="➕ إضافة طالب",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.show_add_student_dialog
        ).pack(side=tk.LEFT)
        
        tk.Button(
            top_frame,
            text="🔄 تحديث",
            font=("Arial", 10),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.load_students
        ).pack(side=tk.LEFT, padx=10)
        
        # Students table
        table_frame = tk.Frame(students_frame, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame)
        y_scroll.pack(side=tk.LEFT, fill=tk.Y)
        
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        columns = ("UID", "الاسم", "الرقم الجامعي", "التخصص", "الهاتف", "تاريخ التسجيل")
        self.students_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            height=20
        )
        
        y_scroll.config(command=self.students_tree.yview)
        x_scroll.config(command=self.students_tree.xview)
        
        # Configure columns
        self.students_tree.heading("UID", text="UID", anchor=tk.E)
        self.students_tree.heading("الاسم", text="الاسم", anchor=tk.E)
        self.students_tree.heading("الرقم الجامعي", text="الرقم الجامعي", anchor=tk.E)
        self.students_tree.heading("التخصص", text="التخصص", anchor=tk.E)
        self.students_tree.heading("الهاتف", text="الهاتف", anchor=tk.E)
        self.students_tree.heading("تاريخ التسجيل", text="تاريخ التسجيل", anchor=tk.E)
        
        self.students_tree.column("UID", width=150, anchor=tk.E)
        self.students_tree.column("الاسم", width=200, anchor=tk.E)
        self.students_tree.column("الرقم الجامعي", width=150, anchor=tk.E)
        self.students_tree.column("التخصص", width=150, anchor=tk.E)
        self.students_tree.column("الهاتف", width=150, anchor=tk.E)
        self.students_tree.column("تاريخ التسجيل", width=180, anchor=tk.E)
        
        self.students_tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Context menu
        self.students_tree.bind("<Button-3>", self.show_student_context_menu)
        
        # Load students
        self.load_students()
    
    def create_session_tab(self):
        """Create session management tab"""
        session_frame = ttk.Frame(self.notebook)
        self.notebook.add(session_frame, text="⏰ الجلسة")
        
        # Main container
        main_container = tk.Frame(session_frame, bg="white")
        main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Session inactive panel
        self.inactive_panel = tk.Frame(main_container, bg="white")
        self.inactive_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            self.inactive_panel,
            text="بدء جلسة جديدة",
            font=("Arial", 18, "bold"),
            bg="white"
        ).pack(pady=20)
        
        tk.Label(
            self.inactive_panel,
            text="اسم الجلسة",
            font=("Arial", 11),
            bg="white"
        ).pack(anchor=tk.E, padx=100)
        
        self.session_name_entry = ttk.Entry(
            self.inactive_panel,
            font=("Arial", 12),
            width=50
        )
        self.session_name_entry.pack(pady=10, ipady=8)
        
        tk.Button(
            self.inactive_panel,
            text="▶ بدء الجلسة",
            font=("Arial", 14, "bold"),
            bg="#10b981",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=15,
            command=self.start_session
        ).pack(pady=30)
        
        # Session active panel
        self.active_panel = tk.Frame(main_container, bg="white")
        
        # Session info
        info_frame = tk.Frame(self.active_panel, bg="white")
        info_frame.pack(fill=tk.X, pady=20)
        
        self.session_name_label = tk.Label(
            info_frame,
            text="جلسة نشطة",
            font=("Arial", 18, "bold"),
            bg="white"
        )
        self.session_name_label.pack(anchor=tk.E)
        
        self.session_info_label = tk.Label(
            info_frame,
            text="وقت البدء: --:-- | الحضور: 0",
            font=("Arial", 11),
            bg="white",
            fg="#64748b"
        )
        self.session_info_label.pack(anchor=tk.E, pady=5)
        
        # Attendance list
        tk.Label(
            self.active_panel,
            text="قائمة الحضور",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(anchor=tk.E, pady=(20, 10))
        
        list_frame = tk.Frame(self.active_panel, bg="#f8fafc", relief=tk.SOLID, borderwidth=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        y_scroll = ttk.Scrollbar(list_frame)
        y_scroll.pack(side=tk.LEFT, fill=tk.Y)
        
        self.attendance_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 11),
            yscrollcommand=y_scroll.set,
            relief=tk.FLAT,
            bg="#f8fafc",
            selectmode=tk.SINGLE,
            height=15
        )
        self.attendance_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        y_scroll.config(command=self.attendance_listbox.yview)
        
        # Stop button
        tk.Button(
            self.active_panel,
            text="⏹ إنهاء الجلسة",
            font=("Arial", 14, "bold"),
            bg="#ef4444",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=15,
            command=self.stop_session
        ).pack(pady=20)
        
        # Show inactive panel initially
        self.update_session_ui()
    
    def create_history_tab(self):
        """Create history tab"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📋 السجل")
        
        # Top bar
        top_frame = tk.Frame(history_frame, bg="white", pady=15)
        top_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(
            top_frame,
            text="سجل الجلسات",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        tk.Button(
            top_frame,
            text="🔄 تحديث",
            font=("Arial", 10),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.load_sessions
        ).pack(side=tk.LEFT)
        
        # Sessions list
        sessions_container = tk.Frame(history_frame, bg="white")
        sessions_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Canvas with scrollbar for session cards
        canvas = tk.Canvas(sessions_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(sessions_container, orient=tk.VERTICAL, command=canvas.yview)
        self.sessions_inner_frame = tk.Frame(canvas, bg="white")
        
        self.sessions_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.sessions_inner_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Load sessions
        self.load_sessions()
    
    def load_students(self):
        """Load and display students"""
        if not self.xlog:
            return
        
        # Clear existing items
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
        
        # Load students
        for uid, student in self.xlog.students.items():
            self.students_tree.insert("", tk.END, values=(
                uid,
                student.get('name', ''),
                student.get('student_id', ''),
                student.get('major', '-'),
                student.get('phone', '-'),
                self.format_datetime(student.get('registered', ''))
            ))
    
    def show_add_student_dialog(self):
        """Show dialog to add new student"""
        dialog = tk.Toplevel(self.root)
        dialog.title("إضافة طالب جديد")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        self.center_window(dialog, 500, 600)
        
        # Scan section
        scan_frame = tk.Frame(dialog, bg="#f8fafc", padx=20, pady=20)
        scan_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            scan_frame,
            text="مسح البطاقة",
            font=("Arial", 12, "bold"),
            bg="#f8fafc"
        ).pack(anchor=tk.E)
        
        scan_result = tk.Label(
            scan_frame,
            text="",
            font=("Arial", 10),
            bg="#f8fafc",
            fg="#2563eb"
        )
        scan_result.pack(pady=10)
        
        uid_var = tk.StringVar()
        
        def scan_card():
            if not self.xlog:
                messagebox.showerror("خطأ", "نظام RFID غير متاح")
                return
            
            scan_result.config(text="جاري المسح... قرب البطاقة من القارئ", fg="#f59e0b")
            dialog.update()
            
            try:
                uid = self.xlog.scan_card(timeout=5)
                if uid:
                    uid_var.set(uid)
                    scan_result.config(text=f"✓ تم المسح بنجاح! UID: {uid}", fg="#10b981")
                else:
                    scan_result.config(text="✗ لم يتم اكتشاف بطاقة", fg="#ef4444")
            except Exception as e:
                scan_result.config(text=f"✗ خطأ: {str(e)}", fg="#ef4444")
        
        tk.Button(
            scan_frame,
            text="🔍 مسح البطاقة",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=scan_card
        ).pack()
        
        # Form
        form_frame = tk.Frame(dialog, bg="white", padx=20)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Name
        tk.Label(form_frame, text="الاسم الكامل *", font=("Arial", 10), bg="white").pack(anchor=tk.E, pady=(10, 5))
        name_entry = ttk.Entry(form_frame, font=("Arial", 11))
        name_entry.pack(fill=tk.X, ipady=5)
        
        # Student ID
        tk.Label(form_frame, text="الرقم الجامعي *", font=("Arial", 10), bg="white").pack(anchor=tk.E, pady=(15, 5))
        student_id_entry = ttk.Entry(form_frame, font=("Arial", 11))
        student_id_entry.pack(fill=tk.X, ipady=5)
        
        # Major
        tk.Label(form_frame, text="التخصص", font=("Arial", 10), bg="white").pack(anchor=tk.E, pady=(15, 5))
        major_entry = ttk.Entry(form_frame, font=("Arial", 11))
        major_entry.pack(fill=tk.X, ipady=5)
        
        # Phone
        tk.Label(form_frame, text="رقم الهاتف", font=("Arial", 10), bg="white").pack(anchor=tk.E, pady=(15, 5))
        phone_entry = ttk.Entry(form_frame, font=("Arial", 11))
        phone_entry.pack(fill=tk.X, ipady=5)
        
        def save_student():
            uid = uid_var.get()
            if not uid:
                messagebox.showwarning("تحذير", "يرجى مسح البطاقة أولاً")
                return
            
            name = name_entry.get().strip()
            student_id = student_id_entry.get().strip()
            
            if not name or not student_id:
                messagebox.showwarning("تحذير", "يرجى ملء الحقول المطلوبة")
                return
            
            if self.xlog:
                self.xlog.add_student(
                    uid,
                    name,
                    student_id,
                    major_entry.get().strip(),
                    phone_entry.get().strip()
                )
                messagebox.showinfo("نجاح", "تم إضافة الطالب بنجاح")
                self.load_students()
                dialog.destroy()
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="white", pady=20)
        btn_frame.pack(fill=tk.X, padx=20)
        
        tk.Button(
            btn_frame,
            text="إلغاء",
            font=("Arial", 10),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="حفظ",
            font=("Arial", 10, "bold"),
            bg="#10b981",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=save_student
        ).pack(side=tk.LEFT, padx=5)
    
    def show_student_context_menu(self, event):
        """Show context menu for student"""
        item = self.students_tree.identify_row(event.y)
        if item:
            self.students_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="حذف الطالب", command=self.delete_selected_student)
            menu.post(event.x_root, event.y_root)
    
    def delete_selected_student(self):
        """Delete selected student"""
        selection = self.students_tree.selection()
        if not selection:
            return
        
        item = self.students_tree.item(selection[0])
        uid = item['values'][0]
        name = item['values'][1]
        
        if messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف الطالب:\n{name}"):
            if self.xlog:
                self.xlog.delete_student(uid)
                self.load_students()
                messagebox.showinfo("نجاح", "تم حذف الطالب بنجاح")
    
    def start_session(self):
        """Start attendance session"""
        session_name = self.session_name_entry.get().strip()
        
        if not session_name:
            messagebox.showwarning("تحذير", "يرجى إدخال اسم الجلسة")
            return
        
        if self.xlog:
            self.xlog.start_session(session_name)
            self.session_name_entry.delete(0, tk.END)
            self.update_session_ui()
            messagebox.showinfo("نجاح", "تم بدء الجلسة بنجاح")
    
    def stop_session(self):
        """Stop attendance session"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من إنهاء الجلسة؟"):
            if self.xlog:
                session = self.xlog.stop_session()
                if session:
                    count = len(session['attendance'])
                    messagebox.showinfo("تم الإنهاء", f"تم إنهاء الجلسة\nعدد الحضور: {count}")
                    self.update_session_ui()
                    self.load_sessions()
    
    def update_session_ui(self):
        """Update session UI based on current state"""
        if self.xlog and self.xlog.current_session:
            self.inactive_panel.pack_forget()
            self.active_panel.pack(fill=tk.BOTH, expand=True)
            
            session = self.xlog.current_session
            self.session_name_label.config(text=session['name'])
            
            count = len(session['attendance'])
            self.session_info_label.config(
                text=f"وقت البدء: {session['start_time']} | الحضور: {count}"
            )
            
            # Update header indicator
            self.session_indicator_frame.config(bg="#10b981")
            self.session_indicator_label.config(
                text=f"● جلسة نشطة: {session['name']}",
                bg="#10b981"
            )
        else:
            self.active_panel.pack_forget()
            self.inactive_panel.pack(fill=tk.BOTH, expand=True)
            
            # Update header indicator
            self.session_indicator_frame.config(bg="#64748b")
            self.session_indicator_label.config(
                text="● لا توجد جلسة نشطة",
                bg="#64748b"
            )
    
    def update_attendance_list(self):
        """Update real-time attendance list"""
        if self.xlog and self.xlog.current_session:
            self.attendance_listbox.delete(0, tk.END)
            
            for att in self.xlog.current_session['attendance']:
                self.attendance_listbox.insert(
                    0,
                    f"  {att['name']} - {att['student_id']} | {att['time'].split()[1]}  "
                )
            
            count = len(self.xlog.current_session['attendance'])
            self.session_info_label.config(
                text=f"وقت البدء: {self.xlog.current_session['start_time']} | الحضور: {count}"
            )
    
    def start_session_monitor(self):
        """Start background thread to monitor attendance"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_attendance, daemon=True)
        self.monitor_thread.start()
    
    def monitor_attendance(self):
        """Background thread to scan cards and record attendance"""
        while self.monitoring:
            if self.xlog and self.xlog.current_session:
                try:
                    uid = self.xlog.scan_card(timeout=0.5)
                    if uid:
                        if self.xlog.record_attendance(uid):
                            # Update UI in main thread
                            self.root.after(0, self.update_attendance_list)
                            self.root.after(0, self.update_session_ui)
                except Exception as e:
                    print(f"Monitor error: {e}")
            time.sleep(0.2)
    
    def load_sessions(self):
        """Load and display session history"""
        if not self.xlog:
            return
        
        # Clear existing widgets
        for widget in self.sessions_inner_frame.winfo_children():
            widget.destroy()
        
        if not self.xlog.sessions:
            tk.Label(
                self.sessions_inner_frame,
                text="لا توجد جلسات مسجلة",
                font=("Arial", 12),
                bg="white",
                fg="#64748b"
            ).pack(pady=40)
            return
        
        # Display sessions (newest first)
        for session in reversed(self.xlog.sessions):
            self.create_session_card(session)
    
    def create_session_card(self, session):
        """Create a card for a session"""
        card = tk.Frame(
            self.sessions_inner_frame,
            bg="white",
            relief=tk.SOLID,
            borderwidth=1,
            padx=20,
            pady=15
        )
        card.pack(fill=tk.X, pady=5)
        
        # Header
        header_frame = tk.Frame(card, bg="white")
        header_frame.pack(fill=tk.X)
        
        tk.Label(
            header_frame,
            text=session['name'],
            font=("Arial", 13, "bold"),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        # Stats
        stats_frame = tk.Frame(card, bg="white")
        stats_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            stats_frame,
            text=f"📅 {session['start_time']}",
            font=("Arial", 9),
            bg="white",
            fg="#64748b"
        ).pack(side=tk.RIGHT, padx=10)
        
        tk.Label(
            stats_frame,
            text=f"👥 {len(session['attendance'])} طالب",
            font=("Arial", 9),
            bg="white",
            fg="#64748b"
        ).pack(side=tk.RIGHT, padx=10)
        
        # Buttons
        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            btn_frame,
            text="📥 تحميل CSV",
            font=("Arial", 9),
            bg="#2563eb",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=lambda s=session: self.export_session(s)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="👁 عرض التفاصيل",
            font=("Arial", 9),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=lambda s=session: self.view_session_details(s)
        ).pack(side=tk.LEFT)
    
    def export_session(self, session):
        """Export session to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"{session['name']}.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['رقم', 'الرقم الجامعي', 'الاسم', 'الوقت'])
                    
                    for i, att in enumerate(session['attendance'], 1):
                        writer.writerow([
                            i,
                            att['student_id'],
                            att['name'],
                            att['time']
                        ])
                
                messagebox.showinfo("نجاح", f"تم حفظ الملف:\n{filename}")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في حفظ الملف:\n{str(e)}")
    
    def view_session_details(self, session):
        """View detailed session information"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"تفاصيل الجلسة: {session['name']}")
        dialog.geometry("600x500")
        self.center_window(dialog, 600, 500)
        
        # Header
        header = tk.Frame(dialog, bg="#2563eb", pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(
            header,
            text=session['name'],
            font=("Arial", 16, "bold"),
            bg="#2563eb",
            fg="white"
        ).pack()
        
        tk.Label(
            header,
            text=f"{session['start_time']} | عدد الحضور: {len(session['attendance'])}",
            font=("Arial", 10),
            bg="#2563eb",
            fg="white"
        ).pack()
        
        # Attendance list
        list_frame = tk.Frame(dialog, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        y_scroll = ttk.Scrollbar(list_frame)
        y_scroll.pack(side=tk.LEFT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            yscrollcommand=y_scroll.set,
            relief=tk.FLAT,
            bg="white"
        )
        listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        y_scroll.config(command=listbox.yview)
        
        for i, att in enumerate(session['attendance'], 1):
            listbox.insert(tk.END, f"{i}. {att['name']} - {att['student_id']} | {att['time']}")
        
        # Close button
        tk.Button(
            dialog,
            text="إغلاق",
            font=("Arial", 10),
            bg="#64748b",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=dialog.destroy
        ).pack(pady=(0, 20))
    
    def logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من تسجيل الخروج؟"):
            self.monitoring = False
            self.root.quit()
    
    def on_closing(self):
        """Handle window close event"""
        if messagebox.askyesno("إنهاء", "هل أنت متأكد من إغلاق البرنامج؟"):
            self.monitoring = False
            self.root.quit()
    
    def center_window(self, window, width, height):
        """Center window on screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def format_datetime(self, dt_string):
        """Format datetime string"""
        if not dt_string:
            return "-"
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return dt_string
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = XLogDesktopApp()
    app.run()
