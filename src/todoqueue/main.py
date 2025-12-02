"""
TodoQueue - 시간순 우선순위 기반 할일 관리 도구

A time-based priority todo list application using queue data structure.
Created with tkinter GUI and SQLite database.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import os
from dataclasses import dataclass
from typing import List, Optional
import sys
from pathlib import Path

__version__ = "1.0.0"

@dataclass
class TodoItem:
    """할일 아이템을 나타내는 데이터 클래스"""
    id: Optional[int]
    text: str
    category: str
    tags: str
    created_at: str
    completed_at: Optional[str]
    status: str  # 'pending' or 'completed'
    order_index: int


class TodoDatabase:
    """할일 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 사용자 문서 폴더에 데이터베이스 저장
            home_dir = Path.home()
            app_dir = home_dir / "TodoQueue"
            app_dir.mkdir(exist_ok=True)
            self.db_path = str(app_dir / "todoqueue.db")
        else:
            self.db_path = db_path
        
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
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
        
        # 앱 버전 정보 저장
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT OR REPLACE INTO app_info (key, value)
            VALUES ('version', ?)
        ''', (__version__,))
        
        conn.commit()
        conn.close()
    
    def add_todo(self, text: str, category: str = '', tags: str = '') -> int:
        """새로운 할일 추가"""
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
        """대기중인 할일 목록 조회"""
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
        """완료된 할일 목록 조회"""
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
        """할일 완료 처리"""
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
        """할일 삭제"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))

        conn.commit()
        conn.close()

    def update_todo(self, todo_id: int, text: str, category: str = '', tags: str = ''):
        """할일 내용 수정"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE todos
            SET text = ?, category = ?, tags = ?
            WHERE id = ?
        ''', (text, category, tags, todo_id))

        conn.commit()
        conn.close()

    def update_todo_order(self, todo_items: List[tuple]):
        """할일 순서 업데이트"""
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
        """카테고리 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM todos WHERE category != ""')
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def add_category(self, name: str, color: str = '#3498db'):
        """새 카테고리 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO categories (name, color) VALUES (?, ?)', (name, color))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Category already exists
        
        conn.close()


class TodoQueueApp:
    """메인 애플리케이션 클래스"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"TodoQueue v{__version__} - 시간순 할일 관리")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # 아이콘 설정 (있다면)
        try:
            # 패키지 내 아이콘 파일이 있다면 설정
            icon_path = Path(__file__).parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        self.db = TodoDatabase()
        self.drag_data = {"item": None, "index": None}
        
        self.setup_ui()
        self.refresh_todos()
        
        # 윈도우 종료 시 정리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """UI 설정"""
        # 메뉴바 생성
        self.create_menu()
        
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
        
        # 상태바
        self.create_status_bar()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_menu(self):
        """메뉴바 생성"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="데이터 백업", command=self.backup_data)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.on_closing)
        
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="사용법", command=self.show_help)
        help_menu.add_command(label="정보", command=self.show_about)
    
    def create_status_bar(self):
        """상태바 생성"""
        self.status_bar = tk.Label(self.root, text="준비됨", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                  bg='#ecf0f1', font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_add_tab(self):
        """할일 추가 탭 설정"""
        # Main container
        main_container = tk.Frame(self.add_frame, bg='#f0f0f0')
        main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container, text="📝 새로운 할일 추가", 
                             font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 25))
        
        # Todo input frame
        input_frame = tk.Frame(main_container, bg='#ffffff', relief=tk.RAISED, bd=2)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Todo text input
        tk.Label(input_frame, text="할일 내용:", font=('Arial', 12, 'bold'), 
                bg='#ffffff', fg='#34495e').pack(anchor=tk.W, padx=20, pady=(20, 8))
        
        self.todo_entry = tk.Text(input_frame, height=4, font=('Arial', 11),
                                 wrap=tk.WORD, relief=tk.FLAT, bg='#f8f9fa',
                                 bd=1)
        self.todo_entry.pack(padx=20, pady=(0, 15), fill=tk.X)
        
        # Category and tags frame
        meta_frame = tk.Frame(input_frame, bg='#ffffff')
        meta_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Category
        cat_frame = tk.Frame(meta_frame, bg='#ffffff')
        cat_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(cat_frame, text="📁 카테고리:", font=('Arial', 11, 'bold'), 
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_frame, textvariable=self.category_var, 
                                          width=25, font=('Arial', 10))
        self.category_combo.pack(side=tk.LEFT, padx=(12, 0))
        
        # Tags
        tag_frame = tk.Frame(meta_frame, bg='#ffffff')
        tag_frame.pack(fill=tk.X)
        
        tk.Label(tag_frame, text="🏷️ 태그 (쉼표로 구분):", font=('Arial', 11, 'bold'), 
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)
        
        self.tags_entry = tk.Entry(tag_frame, width=35, font=('Arial', 10), 
                                  relief=tk.FLAT, bg='#f8f9fa', bd=1)
        self.tags_entry.pack(side=tk.LEFT, padx=(12, 0))
        
        # Add button
        self.add_button = tk.Button(main_container, text="➕ 할일 추가하기", 
                                   command=self.add_todo,
                                   font=('Arial', 13, 'bold'), 
                                   bg='#3498db', fg='white',
                                   relief=tk.FLAT, padx=30, pady=12,
                                   cursor='hand2')
        self.add_button.pack(pady=25)
        
        # Keyboard shortcuts
        self.todo_entry.bind('<Control-Return>', lambda e: self.add_todo())
        self.tags_entry.bind('<Return>', lambda e: self.add_todo())
        
        # Statistics frame
        stats_frame = tk.Frame(main_container, bg='#ecf0f1', relief=tk.RAISED, bd=2)
        stats_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Label(stats_frame, text="📊 현재 상태", font=('Arial', 14, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=(15, 8))
        
        self.stats_label = tk.Label(stats_frame, text="", font=('Arial', 11),
                                   bg='#ecf0f1', fg='#34495e')
        self.stats_label.pack(pady=(0, 15))
    
    def setup_list_tab(self):
        """할일 목록 탭 설정"""
        # Toolbar
        toolbar = tk.Frame(self.list_frame, bg='#34495e', height=50)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        tk.Label(toolbar, text="📋 대기중인 할일 (드래그&드롭으로 순서 조정)", 
                font=('Arial', 13, 'bold'), bg='#34495e', fg='white').pack(side=tk.LEFT, padx=15, pady=12)
        
        refresh_btn = tk.Button(toolbar, text="🔄 새로고침", command=self.refresh_todos,
                               bg='#3498db', fg='white', relief=tk.FLAT, 
                               font=('Arial', 10), cursor='hand2', padx=15, pady=5)
        refresh_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
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
        
        # Bind events
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.todos_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
    
    def setup_completed_tab(self):
        """완료된 할일 탭 설정"""
        # Toolbar
        toolbar = tk.Frame(self.completed_frame, bg='#27ae60', height=50)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        tk.Label(toolbar, text="✅ 완료된 할일", 
                font=('Arial', 13, 'bold'), bg='#27ae60', fg='white').pack(side=tk.LEFT, padx=15, pady=12)
        
        clear_btn = tk.Button(toolbar, text="🗑️ 전체 삭제", command=self.clear_completed,
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             font=('Arial', 10), cursor='hand2', padx=15, pady=5)
        clear_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Scrollable list
        list_frame = tk.Frame(self.completed_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.completed_listbox = tk.Listbox(list_frame, font=('Arial', 11),
                                           bg='#f8f9fa', selectbackground='#27ae60')
        
        # Scrollbar for completed list
        completed_scrollbar = tk.Scrollbar(list_frame)
        completed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.completed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.completed_listbox.config(yscrollcommand=completed_scrollbar.set)
        completed_scrollbar.config(command=self.completed_listbox.yview)
    
    # Canvas 및 스크롤 관련 메소드들
    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
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
        self.status_bar.config(text=f"현재 탭: {selected_tab}")
    
    # 데이터 관련 메소드들 (기존과 동일하지만 상태바 업데이트 추가)
    def add_todo(self):
        text = self.todo_entry.get("1.0", tk.END).strip()
        category = self.category_var.get().strip()
        tags = self.tags_entry.get().strip()
        
        if not text:
            messagebox.showwarning("경고", "할일 내용을 입력해주세요!")
            self.todo_entry.focus()
            return
        
        try:
            self.db.add_todo(text, category, tags)
            
            if category and category not in self.category_combo['values']:
                self.db.add_category(category)
                self.update_categories()
            
            # Clear inputs
            self.todo_entry.delete("1.0", tk.END)
            self.category_var.set("")
            self.tags_entry.delete(0, tk.END)
            
            self.update_stats()
            self.status_bar.config(text="할일이 성공적으로 추가되었습니다!")
            
            messagebox.showinfo("성공", "할일이 추가되었습니다!")
            
        except Exception as e:
            messagebox.showerror("오류", f"할일 추가 중 오류가 발생했습니다: {str(e)}")
            self.status_bar.config(text="할일 추가 실패")
    
    def update_categories(self):
        categories = self.db.get_categories()
        self.category_combo['values'] = categories
    
    def update_stats(self):
        pending = len(self.db.get_pending_todos())
        completed = len(self.db.get_completed_todos())
        
        stats_text = f"📌 대기중: {pending}개  |  ✅ 완료됨: {completed}개"
        self.stats_label.config(text=stats_text)
    
    def refresh_todos(self):
        self.update_categories()
        self.update_stats()
        self.refresh_pending_todos()
        self.refresh_completed_todos()
        self.status_bar.config(text="할일 목록이 새로고침되었습니다.")
    
    def refresh_pending_todos(self):
        # Clear existing widgets
        for widget in self.todos_frame.winfo_children():
            widget.destroy()
        
        todos = self.db.get_pending_todos()
        
        if not todos:
            no_todos_label = tk.Label(self.todos_frame, 
                                     text="📝 아직 할일이 없습니다.\n\n'할일 추가' 탭에서 새로운 할일을 추가해보세요!",
                                     font=('Arial', 14), bg='#ffffff', fg='#7f8c8d',
                                     justify=tk.CENTER)
            no_todos_label.pack(expand=True, pady=80)
            return
        
        for i, todo in enumerate(todos):
            self.create_todo_widget(todo, i)

    def complete_todo(self, todo_id):
        try:
            self.db.complete_todo(todo_id)
            self.refresh_todos()
            self.status_bar.config(text="할일이 완료되었습니다!")
            messagebox.showinfo("완료", "할일이 완료되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"할일 완료 처리 중 오류: {str(e)}")
    
    def delete_todo(self, todo_id):
        if messagebox.askyesno("확인", "이 할일을 삭제하시겠습니까?"):
            try:
                self.db.delete_todo(todo_id)
                self.refresh_todos()
                self.status_bar.config(text="할일이 삭제되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"할일 삭제 중 오류: {str(e)}")

    def edit_todo(self, todo_id):
        """할일 수정 다이얼로그 열기"""
        # 현재 할일 정보 가져오기
        todos = self.db.get_pending_todos()
        current_todo = None
        for todo in todos:
            if todo.id == todo_id:
                current_todo = todo
                break

        if not current_todo:
            messagebox.showerror("오류", "할일을 찾을 수 없습니다.")
            return

        # 수정 다이얼로그 창 생성
        edit_window = tk.Toplevel(self.root)
        edit_window.title("할일 수정")
        edit_window.geometry("600x450")
        edit_window.resizable(False, False)
        edit_window.configure(bg='#f0f0f0')

        # 모달 윈도우로 설정
        edit_window.transient(self.root)
        edit_window.grab_set()

        # 제목
        title_label = tk.Label(edit_window, text="✏️ 할일 수정",
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(20, 25))

        # 입력 프레임
        input_frame = tk.Frame(edit_window, bg='#ffffff', relief=tk.RAISED, bd=2)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # 할일 내용
        tk.Label(input_frame, text="할일 내용:", font=('Arial', 12, 'bold'),
                bg='#ffffff', fg='#34495e').pack(anchor=tk.W, padx=20, pady=(20, 8))

        text_entry = tk.Text(input_frame, height=4, font=('Arial', 11),
                            wrap=tk.WORD, relief=tk.FLAT, bg='#f8f9fa', bd=1)
        text_entry.pack(padx=20, pady=(0, 15), fill=tk.X)
        text_entry.insert("1.0", current_todo.text)

        # 메타 정보 프레임
        meta_frame = tk.Frame(input_frame, bg='#ffffff')
        meta_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # 카테고리
        cat_frame = tk.Frame(meta_frame, bg='#ffffff')
        cat_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(cat_frame, text="📁 카테고리:", font=('Arial', 11, 'bold'),
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)

        category_var = tk.StringVar(value=current_todo.category)
        category_combo = ttk.Combobox(cat_frame, textvariable=category_var,
                                     width=25, font=('Arial', 10))
        category_combo['values'] = self.db.get_categories()
        category_combo.pack(side=tk.LEFT, padx=(12, 0))

        # 태그
        tag_frame = tk.Frame(meta_frame, bg='#ffffff')
        tag_frame.pack(fill=tk.X)

        tk.Label(tag_frame, text="🏷️ 태그 (쉼표로 구분):", font=('Arial', 11, 'bold'),
                bg='#ffffff', fg='#34495e').pack(side=tk.LEFT)

        tags_entry = tk.Entry(tag_frame, width=35, font=('Arial', 10),
                             relief=tk.FLAT, bg='#f8f9fa', bd=1)
        tags_entry.pack(side=tk.LEFT, padx=(12, 0))
        tags_entry.insert(0, current_todo.tags)

        # 버튼 프레임
        button_frame = tk.Frame(edit_window, bg='#f0f0f0')
        button_frame.pack(pady=(0, 20))

        def save_changes():
            """변경사항 저장"""
            text = text_entry.get("1.0", tk.END).strip()
            category = category_var.get().strip()
            tags = tags_entry.get().strip()

            if not text:
                messagebox.showwarning("경고", "할일 내용을 입력해주세요!")
                text_entry.focus()
                return

            try:
                self.db.update_todo(todo_id, text, category, tags)

                # 새 카테고리인 경우 추가
                if category and category not in category_combo['values']:
                    self.db.add_category(category)

                self.refresh_todos()
                self.status_bar.config(text="할일이 수정되었습니다.")
                edit_window.destroy()
                messagebox.showinfo("성공", "할일이 수정되었습니다!")

            except Exception as e:
                messagebox.showerror("오류", f"할일 수정 중 오류가 발생했습니다: {str(e)}")

        # 저장 버튼
        save_btn = tk.Button(button_frame, text="💾 저장",
                           command=save_changes,
                           font=('Arial', 12, 'bold'),
                           bg='#3498db', fg='white',
                           relief=tk.FLAT, padx=25, pady=10,
                           cursor='hand2')
        save_btn.pack(side=tk.LEFT, padx=10)

        # 취소 버튼
        cancel_btn = tk.Button(button_frame, text="❌ 취소",
                              command=edit_window.destroy,
                              font=('Arial', 12, 'bold'),
                              bg='#95a5a6', fg='white',
                              relief=tk.FLAT, padx=25, pady=10,
                              cursor='hand2')
        cancel_btn.pack(side=tk.LEFT, padx=10)

        # 키보드 단축키
        text_entry.bind('<Control-Return>', lambda e: save_changes())
        edit_window.bind('<Escape>', lambda e: edit_window.destroy())

        # 포커스 설정
        text_entry.focus()
        text_entry.tag_add("sel", "1.0", "end")

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
            try:
                completed_todos = self.db.get_completed_todos()
                for todo in completed_todos:
                    self.db.delete_todo(todo.id)
                self.refresh_todos()
                self.status_bar.config(text="완료된 할일들이 모두 삭제되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"삭제 중 오류: {str(e)}")
    
    # 메뉴 관련 메소드들
    def backup_data(self):
        """데이터 백업"""
        try:
            import shutil
            from tkinter import filedialog
            
            backup_path = filedialog.asksaveasfilename(
                title="데이터 백업 위치 선택",
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialname=f"todoqueue_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if backup_path:
                shutil.copy2(self.db.db_path, backup_path)
                messagebox.showinfo("성공", f"데이터가 성공적으로 백업되었습니다!\n위치: {backup_path}")
                self.status_bar.config(text="데이터 백업 완료")
                
        except Exception as e:
            messagebox.showerror("오류", f"백업 중 오류가 발생했습니다: {str(e)}")
            self.status_bar.config(text="데이터 백업 실패")
    
    def show_help(self):
        """사용법 도움말"""
        help_text = """
📖 TodoQueue 사용법

🔹 할일 추가:
   • '할일 추가' 탭에서 내용을 입력하고 '할일 추가' 버튼 클릭
   • Ctrl+Enter로 빠른 추가 가능
   • 카테고리와 태그로 분류 가능

🔹 할일 관리:
   • '할일 목록' 탭에서 대기중인 할일 확인
   • 드래그&드롭으로 순서 조정
   • ✅ 버튼으로 완료 처리
   • 🗑️ 버튼으로 삭제

🔹 완료된 할일:
   • '완료된 할일' 탭에서 완료 이력 확인
   • 완료 시간 순으로 정렬됨

🔹 특징:
   • 시간순 우선순위 자동 설정
   • 데이터 영구 저장
   • 카테고리 및 태그 지원
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("TodoQueue 사용법")
        help_window.geometry("500x400")
        help_window.resizable(False, False)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, font=('Arial', 11),
                             padx=20, pady=20, bg='#f8f9fa')
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # 스크롤바
        scrollbar = tk.Scrollbar(help_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
    
    def show_about(self):
        """정보 다이얼로그"""
        about_text = f"""
TodoQueue v{__version__}

시간순 우선순위 기반 할일 관리 도구

🎯 개발 목적:
   생각나는 순간의 우선순위를 존중하는
   직관적인 할일 관리

🛠️ 기술 스택:
   • Python {sys.version.split()[0]}
   • tkinter (GUI)
   • SQLite (데이터베이스)

📊 데이터 위치:
   {Path(self.db.db_path).parent}

💡 큐(Queue) 자료구조 기반
   FIFO(First In, First Out) 원칙

© 2024 TodoQueue Project
        """
        
        about_window = tk.Toplevel(self.root)
        about_window.title("TodoQueue 정보")
        about_window.geometry("400x350")
        about_window.resizable(False, False)
        
        tk.Label(about_window, text=about_text, 
                font=('Arial', 10), justify=tk.LEFT,
                padx=20, pady=20, bg='#ffffff').pack(fill=tk.BOTH, expand=True)
        
        # 확인 버튼
        tk.Button(about_window, text="확인", command=about_window.destroy,
                 bg='#3498db', fg='white', font=('Arial', 11),
                 padx=20, pady=5).pack(pady=10)
    
    def create_todo_widget(self, todo: TodoItem, index: int):
        """할일 위젯 생성"""
        # Main todo frame
        todo_frame = tk.Frame(self.todos_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        todo_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # Add drag and drop bindings
        todo_frame.bind("<Button-1>", lambda e, idx=index: self.start_drag(e, idx))
        todo_frame.bind("<B1-Motion>", self.on_drag)
        todo_frame.bind("<ButtonRelease-1>", self.on_drop)
        
        # Left frame for content
        content_frame = tk.Frame(todo_frame, bg='#ffffff')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        # Todo text
        text_label = tk.Label(content_frame, text=todo.text, 
                             font=('Arial', 12), bg='#ffffff', fg='#2c3e50',
                             anchor=tk.W, justify=tk.LEFT, wraplength=450)
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
        meta_info.append(f"#{index + 1}")
        
        if meta_info:
            meta_label = tk.Label(content_frame, text=" | ".join(meta_info),
                                 font=('Arial', 9), bg='#ffffff', fg='#7f8c8d',
                                 anchor=tk.W)
            meta_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Right frame for buttons
        button_frame = tk.Frame(todo_frame, bg='#ffffff')
        button_frame.pack(side=tk.RIGHT, padx=15, pady=12)
        
        # Complete button
        complete_btn = tk.Button(button_frame, text="✅",
                               command=lambda: self.complete_todo(todo.id),
                               bg='#27ae60', fg='white', relief=tk.FLAT,
                               font=('Arial', 14), cursor='hand2',
                               width=3, height=1, anchor=tk.CENTER)
        complete_btn.pack(side=tk.TOP, pady=(0, 6))

        # Edit button
        edit_btn = tk.Button(button_frame, text="✏️",
                           command=lambda: self.edit_todo(todo.id),
                           bg='#f39c12', fg='white', relief=tk.FLAT,
                           font=('Arial', 14), cursor='hand2',
                           width=3, height=1, anchor=tk.CENTER)
        edit_btn.pack(side=tk.TOP, pady=(0, 6))

        # Delete button
        delete_btn = tk.Button(button_frame, text="🗑️",
                             command=lambda: self.delete_todo(todo.id),
                             bg='#e74c3c', fg='white', relief=tk.FLAT,
                             font=('Arial', 14), cursor='hand2',
                             width=3, height=1, anchor=tk.CENTER)
        delete_btn.pack(side=tk.TOP)
        
        # Drag indicator
        drag_label = tk.Label(todo_frame, text="⋮⋮", font=('Arial', 16), 
                             bg='#ffffff', fg='#bdc3c7', cursor='hand2')
        drag_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # Bind drag events to all child widgets
        for widget in [todo_frame, content_frame, text_label, button_frame, drag_label]:
            if hasattr(widget, 'bind'):
                widget.bind("<Button-1>", lambda e, idx=index: self.start_drag(e, idx))
                widget.bind("<B1-Motion>", self.on_drag)
                widget.bind("<ButtonRelease-1>", self.on_drop)

    def start_drag(self, event, index):
        """드래그 시작"""
        self.drag_data["item"] = index
        self.drag_data["start_y"] = event.y_root
        # 드래그 시작 시 커서 변경
        event.widget.config(cursor="hand2")
        self.status_bar.config(text=f"할일 #{index + 1} 이동 중...")

    def on_drag(self, event):
        """드래그 중 시각적 피드백"""
        if self.drag_data["item"] is not None:
            # 현재 마우스 위치 기반 예상 이동 거리 계산
            widget_height = 70
            y_offset = event.y_root - self.drag_data["start_y"]
            position_change = round(y_offset / widget_height)

            if position_change != 0:
                start_index = self.drag_data["item"]
                todos = self.db.get_pending_todos()
                target_index = max(0, min(len(todos) - 1, start_index + position_change))

                # 상태바에 예상 위치 표시
                if target_index != start_index:
                    self.status_bar.config(text=f"할일 #{start_index + 1} → #{target_index + 1}로 이동")

    def on_drop(self, event):
        """드래그 완료 처리"""
        if self.drag_data["item"] is not None:
            start_index = self.drag_data["item"]
            
            # Calculate target position based on mouse position
            widget_height = 70  # Approximate height of each todo widget
            y_offset = event.y_root - self.drag_data["start_y"]
            position_change = round(y_offset / widget_height)
            
            if position_change != 0:
                todos = self.db.get_pending_todos()
                target_index = max(0, min(len(todos) - 1, start_index + position_change))
                
                if start_index != target_index:
                    # Reorder the todos
                    todo_ids = [todo.id for todo in todos]
                    
                    # Remove the dragged item
                    dragged_id = todo_ids.pop(start_index)
                    
                    # Insert at new position
                    todo_ids.insert(target_index, dragged_id)
                    
                    # Update database
                    self.db.update_todo_order(todo_ids)
                    
                    # Refresh display
                    self.refresh_pending_todos()
                    self.status_bar.config(text=f"할일 순서가 변경되었습니다 ({start_index + 1} → {target_index + 1})")
        
        # Reset drag data
        self.drag_data = {"item": None, "start_y": None}
    
    def on_closing(self):
        """애플리케이션 종료 처리"""
        if messagebox.askokcancel("종료", "TodoQueue를 종료하시겠습니까?"):
            self.status_bar.config(text="종료 중...")
            self.root.destroy()
    
    def run(self):
        """애플리케이션 실행"""
        self.status_bar.config(text="TodoQueue가 시작되었습니다.")
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        app = TodoQueueApp()
        app.run()
    except Exception as e:
        # 예상치 못한 오류 처리
        import traceback
        error_msg = f"애플리케이션 실행 중 오류가 발생했습니다:\n\n{str(e)}\n\n{traceback.format_exc()}"
        
        # tkinter를 사용할 수 없는 경우를 대비해 try-except
        try:
            messagebox.showerror("오류", error_msg)
        except:
            print(error_msg)


if __name__ == "__main__":
    main()
