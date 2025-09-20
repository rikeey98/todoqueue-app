import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class TodoItem:
    id: Optional[int]
    text: str
    category: str
    tags: str
    created_at: str
    completed_at: Optional[str]
    status: str  # 'pending' or 'completed'
    order_index: int

class TodoDatabase:
    def __init__(self, db_path: str = "todoqueue.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT DEFAULT 'pending',
                order_index INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#3498db'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_todo(self, text: str, category: str = '', tags: str = '') -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get next order index
        cursor.execute('SELECT MAX(order_index) FROM todos WHERE status = "pending"')
        max_order = cursor.fetchone()[0]
        next_order = (max_order or 0) + 1
        
        created_at = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO todos (text, category, tags, created_at, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', (text, category, tags, created_at, next_order))
        
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return todo_id
    
    def get_pending_todos(self) -> List[TodoItem]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, text, category, tags, created_at, completed_at, status, order_index
            FROM todos 
            WHERE status = "pending"
            ORDER BY order_index ASC
        ''')
        
        todos = []
        for row in cursor.fetchall():
            todos.append(TodoItem(*row))
        
        conn.close()
        return todos
    
    def get_completed_todos(self) -> List[TodoItem]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, text, category, tags, created_at, completed_at, status, order_index
            FROM todos 
            WHERE status = "completed"
            ORDER BY completed_at DESC
        ''')
        
        todos = []
        for row in cursor.fetchall():
            todos.append(TodoItem(*row))
        
        conn.close()
        return todos
    
    def complete_todo(self, todo_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        completed_at = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE todos 
            SET status = "completed", completed_at = ?
            WHERE id = ?
        ''', (completed_at, todo_id))
        
        conn.commit()
        conn.close()
    
    def delete_todo(self, todo_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        
        conn.commit()
        conn.close()
    
    def update_todo_order(self, todo_items: List[tuple]):
        """Update order of todos based on new positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for order_index, todo_id in enumerate(todo_items):
            cursor.execute('''
                UPDATE todos 
                SET order_index = ?
                WHERE id = ?
            ''', (order_index, todo_id))
        
        conn.commit()
        conn.close()
    
    def get_categories(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM todos WHERE category != ""')
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def add_category(self, name: str, color: str = '#3498db'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO categories (name, color) VALUES (?, ?)', (name, color))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Category already exists
        
        conn.close()

class TodoQueueApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TodoQueue - 시간순 할일 관리")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.db = TodoDatabase()
        self.drag_data = {"item": None, "index": None}
        
        self.setup_ui()
        self.refresh_todos()
    
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Add Todo
        self.add_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.add_frame, text="할일 추가")
        self.setup_add_tab()
        
        # Tab 2: Todo List
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="할일 목록")
        self.setup_list_tab()
        
        # Tab 3: Completed
        self.completed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.completed_frame, text="완료된 할일")
        self.setup_completed_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def setup_add_tab(self):
        # Main container
        main_container = tk.Frame(self.add_frame, bg='#f0f0f0')
        main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container, text="새로운 할일 추가", 
                             font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Todo input frame
        input_frame = tk.Frame(main_container, bg='#ffffff', relief=tk.RAISED, bd=1)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Todo text input
        tk.Label(input_frame, text="할일 내용:", font=('Arial', 11), 
                bg='#ffffff', fg='#34495e').pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.todo_entry = tk.Text(input_frame, height=3, width=50, font=('Arial', 10),
                                 wrap=tk.WORD, relief=tk.FLAT, bg='#f8f9fa')
        self.todo_entry.pack(padx=15, pady=(0, 10), fill=tk.X)
        
        # Category and tags frame
        meta_frame = tk.Frame(input_frame, bg='#ffffff')
        meta_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Category
        cat_frame = tk.Frame(meta_frame, bg='#ffffff')
        cat_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(cat_frame, text="카테고리:", font=('Arial', 10), 
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_frame, textvariable=self.category_var, 
                                          width=20, font=('Arial', 9))
        self.category_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Tags
        tag_frame = tk.Frame(meta_frame, bg='#ffffff')
        tag_frame.pack(fill=tk.X)
        
        tk.Label(tag_frame, text="태그 (쉼표로 구분):", font=('Arial', 10), 
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)
        
        self.tags_entry = tk.Entry(tag_frame, width=30, font=('Arial', 9), 
                                  relief=tk.FLAT, bg='#f8f9fa')
        self.tags_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Add button
        self.add_button = tk.Button(main_container, text="📝 할일 추가", 
                                   command=self.add_todo,
                                   font=('Arial', 12, 'bold'), 
                                   bg='#3498db', fg='white',
                                   relief=tk.FLAT, padx=20, pady=10,
                                   cursor='hand2')
        self.add_button.pack(pady=20)
        
        # Bind Enter key
        self.todo_entry.bind('<Control-Return>', lambda e: self.add_todo())
        
        # Statistics frame
        stats_frame = tk.Frame(main_container, bg='#ecf0f1', relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Label(stats_frame, text="📊 현재 상태", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=(10, 5))
        
        self.stats_label = tk.Label(stats_frame, text="", font=('Arial', 10),
                                   bg='#ecf0f1', fg='#34495e')
        self.stats_label.pack(pady=(0, 10))
    
    def setup_list_tab(self):
        # Toolbar
        toolbar = tk.Frame(self.list_frame, bg='#34495e', height=40)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        tk.Label(toolbar, text="📋 대기중인 할일 (드래그&드롭으로 순서 조정 가능)", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        refresh_btn = tk.Button(toolbar, text="🔄 새로고침", command=self.refresh_todos,
                               bg='#3498db', fg='white', relief=tk.FLAT, 
                               font=('Arial', 9), cursor='hand2')
        refresh_btn.pack(side=tk.RIGHT, padx=10, pady=6)
        
        # Scrollable list frame
        list_container = tk.Frame(self.list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(list_container, yscrollcommand=scrollbar.set, bg='#ffffff')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas
        self.todos_frame = tk.Frame(self.canvas, bg='#ffffff')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.todos_frame, anchor="nw")
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.todos_frame.bind('<Configure>', self.on_frame_configure)
        
        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def setup_completed_tab(self):
        # Toolbar
        toolbar = tk.Frame(self.completed_frame, bg='#27ae60', height=40)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        tk.Label(toolbar, text="✅ 완료된 할일", 
                font=('Arial', 12, 'bold'), bg='#27ae60', fg='white').pack(side=tk.LEFT, padx=10, pady=8)
        
        clear_btn = tk.Button(toolbar, text="🗑️ 전체 삭제", command=self.clear_completed,
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             font=('Arial', 9), cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=10, pady=6)
        
        # Scrollable list
        self.completed_listbox = tk.Listbox(self.completed_frame, font=('Arial', 10),
                                           bg='#f8f9fa', selectbackground='#27ae60')
        self.completed_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for completed list
        completed_scrollbar = tk.Scrollbar(self.completed_listbox)
        completed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.completed_listbox.config(yscrollcommand=completed_scrollbar.set)
        completed_scrollbar.config(command=self.completed_listbox.yview)
    
    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Update the width of the todos_frame to match canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_tab_changed(self, event):
        selected_tab = event.widget.tab('current')['text']
        if selected_tab in ['할일 목록', '완료된 할일']:
            self.refresh_todos()
    
    def add_todo(self):
        text = self.todo_entry.get("1.0", tk.END).strip()
        category = self.category_var.get().strip()
        tags = self.tags_entry.get().strip()
        
        if not text:
            messagebox.showwarning("경고", "할일 내용을 입력해주세요!")
            return
        
        # Add to database
        self.db.add_todo(text, category, tags)
        
        # Add category if new
        if category and category not in self.category_combo['values']:
            self.db.add_category(category)
            self.update_categories()
        
        # Clear inputs
        self.todo_entry.delete("1.0", tk.END)
        self.category_var.set("")
        self.tags_entry.delete(0, tk.END)
        
        # Update stats
        self.update_stats()
        
        messagebox.showinfo("성공", "할일이 추가되었습니다!")
    
    def update_categories(self):
        categories = self.db.get_categories()
        self.category_combo['values'] = categories
    
    def update_stats(self):
        pending = len(self.db.get_pending_todos())
        completed = len(self.db.get_completed_todos())
        
        stats_text = f"대기중: {pending}개 | 완료됨: {completed}개"
        self.stats_label.config(text=stats_text)
    
    def refresh_todos(self):
        self.update_categories()
        self.update_stats()
        self.refresh_pending_todos()
        self.refresh_completed_todos()
    
    def refresh_pending_todos(self):
        # Clear existing widgets
        for widget in self.todos_frame.winfo_children():
            widget.destroy()
        
        todos = self.db.get_pending_todos()
        
        if not todos:
            no_todos_label = tk.Label(self.todos_frame, 
                                     text="📝 아직 할일이 없습니다.\n'할일 추가' 탭에서 새로운 할일을 추가해보세요!",
                                     font=('Arial', 12), bg='#ffffff', fg='#7f8c8d',
                                     justify=tk.CENTER)
            no_todos_label.pack(expand=True, pady=50)
            return
        
        for i, todo in enumerate(todos):
            self.create_todo_widget(todo, i)
    
    def create_todo_widget(self, todo: TodoItem, index: int):
        # Main todo frame
        todo_frame = tk.Frame(self.todos_frame, bg='#ffffff', relief=tk.RAISED, bd=1)
        todo_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Add drag and drop bindings
        todo_frame.bind("<Button-1>", lambda e, idx=index: self.start_drag(e, idx))
        todo_frame.bind("<B1-Motion>", self.on_drag)
        todo_frame.bind("<ButtonRelease-1>", self.on_drop)
        
        # Left frame for content
        content_frame = tk.Frame(todo_frame, bg='#ffffff')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # Todo text
        text_label = tk.Label(content_frame, text=todo.text, 
                             font=('Arial', 11), bg='#ffffff', fg='#2c3e50',
                             anchor=tk.W, justify=tk.LEFT, wraplength=400)
        text_label.pack(anchor=tk.W)
        
        # Meta info
        meta_info = []
        if todo.category:
            meta_info.append(f"📁 {todo.category}")
        if todo.tags:
            meta_info.append(f"🏷️ {todo.tags}")
        
        created_time = datetime.datetime.fromisoformat(todo.created_at)
        time_str = created_time.strftime("%m/%d %H:%M")
        meta_info.append(f"🕐 {time_str}")
        
        if meta_info:
            meta_label = tk.Label(content_frame, text=" | ".join(meta_info),
                                 font=('Arial', 9), bg='#ffffff', fg='#7f8c8d',
                                 anchor=tk.W)
            meta_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Right frame for buttons
        button_frame = tk.Frame(todo_frame, bg='#ffffff')
        button_frame.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # Complete button
        complete_btn = tk.Button(button_frame, text="✅", 
                               command=lambda: self.complete_todo(todo.id),
                               bg='#27ae60', fg='white', relief=tk.FLAT,
                               font=('Arial', 12), cursor='hand2',
                               width=3)
        complete_btn.pack(side=tk.TOP, pady=(0, 5))
        
        # Delete button
        delete_btn = tk.Button(button_frame, text="🗑️", 
                             command=lambda: self.delete_todo(todo.id),
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             font=('Arial', 12), cursor='hand2',
                             width=3)
        delete_btn.pack(side=tk.TOP)
        
        # Drag indicator
        drag_label = tk.Label(todo_frame, text="⋮⋮", font=('Arial', 14), 
                             bg='#ffffff', fg='#bdc3c7', cursor='hand2')
        drag_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind drag events to all child widgets
        for widget in [todo_frame, content_frame, text_label, button_frame, drag_label]:
            if hasattr(widget, 'bind'):
                widget.bind("<Button-1>", lambda e, idx=index: self.start_drag(e, idx))
                widget.bind("<B1-Motion>", self.on_drag)
                widget.bind("<ButtonRelease-1>", self.on_drop)
    
    def start_drag(self, event, index):
        self.drag_data["item"] = index
        self.drag_data["start_y"] = event.y_root
    
    def on_drag(self, event):
        if self.drag_data["item"] is not None:
            # Visual feedback could be added here
            pass
    
    def on_drop(self, event):
        if self.drag_data["item"] is not None:
            start_index = self.drag_data["item"]
            
            # Calculate target position based on mouse position
            widget_height = 60  # Approximate height of each todo widget
            y_offset = event.y_root - self.drag_data["start_y"]
            position_change = round(y_offset / widget_height)
            
            if position_change != 0:
                todos = self.db.get_pending_todos()
                target_index = max(0, min(len(todos) - 1, start_index + position_change))
                
                if start_index != target_index:
                    # Reorder the todos
                    new_order = []
                    todo_ids = [todo.id for todo in todos]
                    
                    # Remove the dragged item
                    dragged_id = todo_ids.pop(start_index)
                    
                    # Insert at new position
                    todo_ids.insert(target_index, dragged_id)
                    
                    # Update database
                    self.db.update_todo_order(todo_ids)
                    
                    # Refresh display
                    self.refresh_pending_todos()
        
        # Reset drag data
        self.drag_data = {"item": None, "start_y": None}
    
    def complete_todo(self, todo_id):
        self.db.complete_todo(todo_id)
        self.refresh_todos()
        messagebox.showinfo("완료", "할일이 완료되었습니다!")
    
    def delete_todo(self, todo_id):
        if messagebox.askyesno("확인", "이 할일을 삭제하시겠습니까?"):
            self.db.delete_todo(todo_id)
            self.refresh_todos()
    
    def refresh_completed_todos(self):
        self.completed_listbox.delete(0, tk.END)
        
        completed_todos = self.db.get_completed_todos()
        
        for todo in completed_todos:
            completed_time = datetime.datetime.fromisoformat(todo.completed_at)
            time_str = completed_time.strftime("%m/%d %H:%M")
            
            display_text = f"✅ {todo.text}"
            if todo.category:
                display_text += f" [📁 {todo.category}]"
            display_text += f" - 완료: {time_str}"
            
            self.completed_listbox.insert(tk.END, display_text)
    
    def clear_completed(self):
        if messagebox.askyesno("확인", "완료된 모든 할일을 삭제하시겠습니까?"):
            completed_todos = self.db.get_completed_todos()
            for todo in completed_todos:
                self.db.delete_todo(todo.id)
            self.refresh_todos()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TodoQueueApp()
    app.run()
