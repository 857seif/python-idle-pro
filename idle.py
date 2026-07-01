import os
import sys
import ast
import json
import subprocess
import threading
import importlib.util
import struct
import marshal
import zlib
import shutil
import time
import webbrowser
from uuid import uuid4 as uniquename
from tkinter import filedialog, messagebox, Text, Scrollbar, RIGHT, Y, LEFT, BOTH, END, Toplevel, Listbox, StringVar, Menu, Tk

# Try to import customtkinter, fallback to tkinter if not available
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("⚠️ customtkinter not found, using tkinter fallback")
    # Create a minimal compatibility layer
    class ctk:
        class CTk(Tk):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        class CTkFrame:
            def __init__(self, master, **kwargs):
                self.frame = Tk.Frame(master)
                self._kwargs = kwargs
            def pack(self, **kwargs):
                self.frame.pack(**kwargs)
            def winfo_children(self):
                return self.frame.winfo_children()
            def winfo_ismapped(self):
                return self.frame.winfo_ismapped()
            def destroy(self):
                self.frame.destroy()

        class CTkButton:
            def __init__(self, master, text="", command=None, width=100, height=28, fg_color=None, hover_color=None, font=None, **kwargs):
                self.btn = Tk.Button(master, text=text, command=command, width=width//10)
                self._command = command
            def pack(self, **kwargs):
                self.btn.pack(**kwargs)
            def configure(self, **kwargs):
                if 'text' in kwargs:
                    self.btn.configure(text=kwargs['text'])
                if 'fg_color' in kwargs:
                    self.btn.configure(bg=kwargs['fg_color'])

        class CTkLabel:
            def __init__(self, master, text="", font=None, text_color=None, **kwargs):
                self.lbl = Tk.Label(master, text=text)
            def pack(self, **kwargs):
                self.lbl.pack(**kwargs)
            def configure(self, **kwargs):
                if 'text' in kwargs:
                    self.lbl.configure(text=kwargs['text'])

        class CTkEntry:
            def __init__(self, master, placeholder_text="", width=100, height=28, textvariable=None, **kwargs):
                self.entry = Tk.Entry(master, width=width//10)
                self._placeholder = placeholder_text
            def pack(self, **kwargs):
                self.entry.pack(**kwargs)
            def get(self):
                return self.entry.get()
            def delete(self, a, b):
                self.entry.delete(a, b)
            def insert(self, pos, text):
                self.entry.insert(pos, text)
            def bind(self, event, callback):
                self.entry.bind(event, callback)

        class CTkTextbox:
            def __init__(self, master, wrap="word", font=None, height=100, border_width=0, fg_color=None, **kwargs):
                self.text = Text(master, wrap=wrap, height=height//20)
            def pack(self, **kwargs):
                self.text.pack(**kwargs)
            def insert(self, pos, text):
                self.text.insert(pos, text)
            def see(self, pos):
                self.text.see(pos)
            def delete(self, a, b):
                self.text.delete(a, b)

        class CTkCheckBox:
            def __init__(self, master, text="", variable=None, font=None, **kwargs):
                self.cb = Tk.Checkbutton(master, text=text, variable=variable)
            def grid(self, **kwargs):
                self.cb.grid(**kwargs)

        class CTkProgressBar:
            def __init__(self, master, width=280, height=16, corner_radius=8):
                self.bar = Tk.Frame(master, width=width, height=height, bg="#333")
                self.fill = Tk.Frame(self.bar, width=0, height=height, bg="#00ff00")
                self.fill.place(x=0, y=0)
            def pack(self, **kwargs):
                self.bar.pack(**kwargs)
            def set(self, value):
                max_width = self.bar.winfo_width() or 280
                self.fill.configure(width=int(max_width * value))

        class CTkComboBox:
            def __init__(self, master, values=[], variable=None, font=None, width=300, **kwargs):
                self.var = variable or StringVar()
                self.combo = Tk.OptionMenu(master, self.var, *values)
            def pack(self, **kwargs):
                self.combo.pack(**kwargs)

        class CTkScrollableFrame:
            def __init__(self, master, label_text="", corner_radius=8, width=350, fg_color=None, height=200, **kwargs):
                self.frame = Tk.Frame(master)
                self.label = Tk.Label(self.frame, text=label_text)
                self.label.pack()
                self.canvas = Tk.Canvas(self.frame, width=width, height=height)
                self.canvas.pack(side="left", fill="both", expand=True)
                self.scrollbar = Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
                self.scrollbar.pack(side="right", fill="y")
                self.canvas.configure(yscrollcommand=self.scrollbar.set)
                self.inner = Tk.Frame(self.canvas)
                self.canvas.create_window((0,0), window=self.inner, anchor="nw")
            def pack(self, **kwargs):
                self.frame.pack(**kwargs)
            def winfo_children(self):
                return self.inner.winfo_children()

        class CTkToplevel:
            def __init__(self, master):
                self.window = Toplevel(master)
            def title(self, text):
                self.window.title(text)
            def geometry(self, geo):
                self.window.geometry(geo)
            def resizable(self, a, b):
                self.window.resizable(a, b)
            def transient(self, master):
                self.window.transient(master)
            def grab_set(self):
                self.window.grab_set()
            def destroy(self):
                self.window.destroy()

        class BooleanVar:
            def __init__(self, value=False):
                self.var = Tk.BooleanVar(value=value)
            def get(self):
                return self.var.get()
            def set(self, value):
                self.var.set(value)

        class StringVar:
            def __init__(self, value=""):
                self.var = Tk.StringVar(value=value)
            def get(self):
                return self.var.get()
            def set(self, value):
                self.var.set(value)

        @staticmethod
        def set_appearance_mode(mode):
            pass

        @staticmethod
        def set_default_color_theme(theme):
            pass

LANG = 'ar'  # Default to Arabic since user is Arabic
TEXTS = {
    'en': {
        'APP_TITLE': "🐍 Python IDLE Pro — Professional Integrated Editor",
        'TAB_UNSAVED': "Unsaved",
        'BTN_NEW': "📄 New",
        'BTN_OPEN': "📂 Open",
        'BTN_SAVE': "💾 Save",
        'BTN_SAVE_AS': "💾 Save As",
        'BTN_CLOSE': "✕ Close",
        'STATUS_UNSAVED': "📄 Unsaved",
        'STATUS_NO_ACTIVE': "📄 No active file",
        'PANEL_TITLE': "Control Panel",
        'BTN_NEW_PROJECT': "📁 New Project",
        'BTN_REQUIREMENTS': "📦 Requirements",
        'BTN_ANALYZE': "🔍 Analyze",
        'BTN_INSTALL_MISSING': "⬇️ Install Missing",
        'LIBS_TITLE': "📦 Imported Libraries",
        'BTN_FORMAT': "🎨 Format (Black)",
        'BTN_LINT': "🔍 Lint (Flake8)",
        'BTN_TERMINAL': "🖥️ Terminal",
        'BUILD_TITLE': "🛠️ Build (PyInstaller)",
        'CHECK_ONEFILE': "--onefile",
        'CHECK_NOCONSOLE': "--noconsole",
        'CHECK_WINDOWED': "--windowed",
        'CHECK_PYARMOR': "🔐 Encrypt PyArmor",
        'LABEL_FILENAME': "File name:",
        'LABEL_ICON': "Icon .ico:",
        'BTN_RUN': "▶️ Run",
        'BTN_BUILD': "⚡ Build EXE",
        'EXTRACT_TITLE': "📦 Extract EXE",
        'BTN_EXTRACT_PYC': "🔍 Extract .pyc",
        'BTN_PYLINGUAL': "🌐 pylingual.io",
        'LOG_TITLE': "📋 Event Log",
        'PROGRESS_WAITING': "⏳ Waiting...",
        'LOG_READY': "✅ Python IDLE Pro ready – supports Arabic and auto-GUI detection.",
        'LOG_NEW_FILE': "📄 Content cleared (new file)",
        'LOG_TAB_CREATED': "📄 New file created in tab",
        'LOG_OPEN_ERROR': "❌ Error opening file: {error}",
        'LOG_ALREADY_OPEN': "📂 File already open: {path}",
        'LOG_FILE_OPENED': "📂 Opened file: {path}",
        'LOG_FILE_SAVED': "💾 Saved file: {path}",
        'LOG_ANALYZING': "🔍 Analyzing code... (may take a moment)",
        'LOG_EDITOR_EMPTY': "ℹ️ Editor is empty.",
        'LOG_NO_EXTERNAL': "✅ No external libraries required.",
        'LOG_LIBS_FOUND': "📦 Found {count} external libraries.",
        'LOG_SYNTAX_ERROR': "⚠️ Syntax error: {error}",
        'LOG_ANALYSIS_ERROR': "❌ Analysis error: {error}",
        'LOG_ALL_INSTALLED': "✅ All selected libraries are installed.",
        'LOG_INSTALLING_START': "⬇️ Installing {count} libraries...",
        'LOG_INSTALLING_LIB': "📦 Installing {lib} ...",
        'LOG_INSTALL_SUCCESS': "✅ Successfully installed {lib}.",
        'LOG_INSTALL_FAIL': "❌ Failed to install {lib} (code {code})",
        'LOG_INSTALL_EXCEPTION': "❌ Exception installing {lib}: {error}",
        'MSG_INSTALL_DONE_SUCCESS': "Installation complete.",
        'MSG_INSTALL_DONE_ERROR': "Errors occurred during installation.",
        'LOG_GUI_DETECTED': "🖥️ GUI detected – running without terminal window",
        'LOG_NO_GUI': "💻 No GUI – running with terminal window",
        'LOG_RUN_SUCCESS_GUI': "✅ GUI application started successfully.",
        'LOG_RUN_SUCCESS_NON_GUI': "✅ File executed in terminal window.",
        'LOG_RUN_FAIL': "❌ Execution failed: {error}",
        'LOG_FORMAT_SUCCESS': "✅ Code formatted using Black.",
        'LOG_FORMAT_FAIL': "❌ Formatting failed: {error}",
        'LOG_LINT_RESULT': "🔍 Lint results:\n{output}",
        'LOG_LINT_CLEAN': "✅ No linting errors.",
        'LOG_REQ_GEN_SUCCESS': "✅ Created {path}",
        'LOG_PYARMOR_INSTALLING': "⚠️ PyArmor not installed. Installing...",
        'LOG_PYARMOR_SUCCESS': "✅ PyArmor installed successfully.",
        'LOG_PYARMOR_FAIL': "❌ PyArmor installation failed.",
        'LOG_ENCRYPTING': "🔐 Attempting to encrypt file with PyArmor...",
        'LOG_TRYING_CMD': "▶️ Trying command: {cmd}",
        'LOG_ENCRYPT_SUCCESS': "✅ File encrypted successfully.",
        'LOG_ENCRYPT_FAIL': "⚠️ Command failed (code {code})",
        'LOG_ENCRYPT_EXCEPTION': "❌ Exception: {error}",
        'LOG_ENCRYPT_ALL_FAIL': "❌ All PyArmor attempts failed automatically.",
        'LOG_MANUAL_CMD': "You can run this manually:\n{cmd}",
        'LOG_ENCRYPTED_FILE_SELECTED': "🔐 Encrypted file selected manually: {path}",
        'LOG_PYARMOR_TEMP_CLEAN': "🧹 Removed temporary PyArmor folder.",
        'LOG_BUILD_CMD': "⚡ Building EXE with command: {cmd}",
        'LOG_BUILD_SUCCESS': "🎉 EXE built successfully! (dist folder)",
        'LOG_BUILD_FAIL': "❌ Build failed with code: {code}",
        'LOG_BUILD_EXCEPTION': "❌ Exception during build: {error}",
        'LOG_EXTRACT_SELECTED': "📂 Selected EXE: {path}",
        'LOG_EXTRACT_START': "⏳ Starting extraction...",
        'LOG_EXTRACT_SUCCESS': "✅ Extraction completed successfully",
        'LOG_EXTRACT_CLEANING': "🧹 Cleaning up extracted folder...",
        'LOG_EXTRACT_MAIN': "🔍 Main file: {path}",
        'LOG_EXTRACT_COPIED': "📄 Copied .pyc to: {path}",
        'LOG_EXTRACT_DELETED': "🗑️ Removed temporary folder",
        'LOG_EXTRACT_FAIL': "❌ Process failed: {error}",
        'DIALOG_CLOSE_TAB_TITLE': "Close Tab",
        'DIALOG_CLOSE_TAB_MSG': "The file '{}' has unsaved changes. Close without saving?",
        'DIALOG_ANALYZE_FIRST': "Analyze the code first using the 'Analyze' button.",
        'DIALOG_INSTALL_COMPLETE': "All specified libraries are already installed.",
        'DIALOG_INSTALL_ERROR': "Failed to install PyInstaller:\n{error}",
        'DIALOG_NO_FILE_RUN': "No active file to run.",
        'DIALOG_SELF_EXEC_WARN': "This file is the application itself (Python IDLE Pro).\nRunning it will open a new instance.\nPlease open or create a different file.",
        'DIALOG_UNSAVED_RUN': "File has unsaved changes. Save before running?\n(Choose 'Yes' to save, 'No' to run without saving, 'Cancel' to abort)",
        'DIALOG_UNSAVED_BUILD': "File has unsaved changes. Save before building?\n(Choose 'Yes' to save, 'No' to build without saving, 'Cancel' to abort)",
        'DIALOG_PYTHON_NOT_FOUND': "System Python interpreter not found. Ensure Python is installed and added to PATH.",
        'DIALOG_SAVE_FIRST': "Save the file first.",
        'DIALOG_NO_EXTERNAL_LIBS': "No external libraries found.",
        'DIALOG_PYARMOR_FAILED': "PyArmor automatic execution failed.\nYou can run this manually:\n{cmd}\n\nAfter encryption, select the encrypted file manually.",
        'DIALOG_SELECT_ENCRYPTED': "No encrypted file selected. Continue without encryption?",
        'DIALOG_NO_ENCRYPTED_CONTINUE': "Proceed without encryption?",
        'EXTRACT_ASK': "✅ .pyc extracted successfully!\n{path}\n\nDo you want to open pylingual.io to upload and decompile it?",
        'EXTRACT_TITLE_DONE': "Extraction Complete",
        'ICON_SELECTED': "🖼️ Selected icon: {path}",
        'DIALOG_ERROR': "Error",
        'DIALOG_INFO': "Information",
        'DIALOG_WARNING': "Warning",
    },
    'ar': {
        'APP_TITLE': "🐍 Python IDLE Pro — محرر متكامل احترافي",
        'TAB_UNSAVED': "غير محفوظ",
        'BTN_NEW': "📄 جديد",
        'BTN_OPEN': "📂 فتح",
        'BTN_SAVE': "💾 حفظ",
        'BTN_SAVE_AS': "💾 حفظ باسم",
        'BTN_CLOSE': "✕ إغلاق",
        'STATUS_UNSAVED': "📄 غير محفوظ",
        'STATUS_NO_ACTIVE': "📄 لا يوجد ملف نشط",
        'PANEL_TITLE': "لوحة التحكم",
        'BTN_NEW_PROJECT': "📁 مشروع جديد",
        'BTN_REQUIREMENTS': "📦 المتطلبات",
        'BTN_ANALYZE': "🔍 تحليل",
        'BTN_INSTALL_MISSING': "⬇️ تثبيت المفقودة",
        'LIBS_TITLE': "📦 المكتبات المستوردة",
        'BTN_FORMAT': "🎨 تنسيق (Black)",
        'BTN_LINT': "🔍 فحص (Flake8)",
        'BTN_TERMINAL': "🖥️ طرفية",
        'BUILD_TITLE': "🛠️ البناء (PyInstaller)",
        'CHECK_ONEFILE': "--onefile",
        'CHECK_NOCONSOLE': "--noconsole",
        'CHECK_WINDOWED': "--windowed",
        'CHECK_PYARMOR': "🔐 تشفير PyArmor",
        'LABEL_FILENAME': "اسم الملف:",
        'LABEL_ICON': "أيقونة .ico:",
        'BTN_RUN': "▶️ تشغيل",
        'BTN_BUILD': "⚡ بناء EXE",
        'EXTRACT_TITLE': "📦 استخراج EXE",
        'BTN_EXTRACT_PYC': "🔍 استخراج .pyc",
        'BTN_PYLINGUAL': "🌐 pylingual.io",
        'LOG_TITLE': "📋 سجل الأحداث",
        'PROGRESS_WAITING': "⏳ انتظار",
        'LOG_READY': "✅ Python IDLE Pro جاهز – يدعم العربية والـ GUI التلقائي",
        'LOG_NEW_FILE': "📄 تم مسح المحتوى (ملف جديد)",
        'LOG_TAB_CREATED': "📄 تم إنشاء ملف جديد في تبويب",
        'LOG_OPEN_ERROR': "❌ خطأ في فتح الملف: {error}",
        'LOG_ALREADY_OPEN': "📂 الملف مفتوح بالفعل: {path}",
        'LOG_FILE_OPENED': "📂 تم فتح الملف: {path}",
        'LOG_FILE_SAVED': "💾 تم حفظ الملف: {path}",
        'LOG_ANALYZING': "🔍 جاري تحليل الكود... (قد يستغرق لحظات)",
        'LOG_EDITOR_EMPTY': "ℹ️ المحرر فارغ.",
        'LOG_NO_EXTERNAL': "✅ لا توجد مكتبات خارجية مطلوبة.",
        'LOG_LIBS_FOUND': "📦 تم العثور على {count} مكتبة خارجية.",
        'LOG_SYNTAX_ERROR': "⚠️ خطأ نحوي: {error}",
        'LOG_ANALYSIS_ERROR': "❌ خطأ في التحليل: {error}",
        'LOG_ALL_INSTALLED': "✅ جميع المكتبات المحددة مثبتة.",
        'LOG_INSTALLING_START': "⬇️ جاري تثبيت {count} مكتبة...",
        'LOG_INSTALLING_LIB': "📦 تثبيت {lib} ...",
        'LOG_INSTALL_SUCCESS': "✅ تم تثبيت {lib}.",
        'LOG_INSTALL_FAIL': "❌ فشل {lib} (كود {code})",
        'LOG_INSTALL_EXCEPTION': "❌ استثناء {lib}: {error}",
        'MSG_INSTALL_DONE_SUCCESS': "تمت عملية التثبيت.",
        'MSG_INSTALL_DONE_ERROR': "حدثت أخطاء أثناء التثبيت.",
        'LOG_GUI_DETECTED': "🖥️ تم الكشف عن واجهة GUI – سيتم التشغيل بدون نافذة طرفية",
        'LOG_NO_GUI': "💻 لا يوجد GUI – سيتم التشغيل مع نافذة طرفية",
        'LOG_RUN_SUCCESS_GUI': "✅ تم تشغيل تطبيق GUI بنجاح.",
        'LOG_RUN_SUCCESS_NON_GUI': "✅ تم تشغيل الملف في نافذة طرفية.",
        'LOG_RUN_FAIL': "❌ فشل التشغيل: {error}",
        'LOG_FORMAT_SUCCESS': "✅ تم تنسيق الكود باستخدام Black.",
        'LOG_FORMAT_FAIL': "❌ فشل التنسيق: {error}",
        'LOG_LINT_RESULT': "🔍 نتائج الفحص:\n{output}",
        'LOG_LINT_CLEAN': "✅ لا توجد أخطاء.",
        'LOG_REQ_GEN_SUCCESS': "✅ تم إنشاء {path}",
        'LOG_PYARMOR_INSTALLING': "⚠️ PyArmor غير مثبت. جاري التثبيت...",
        'LOG_PYARMOR_SUCCESS': "✅ تم تثبيت PyArmor بنجاح.",
        'LOG_PYARMOR_FAIL': "❌ فشل تثبيت PyArmor.",
        'LOG_ENCRYPTING': "🔐 محاولة تشفير الملف باستخدام PyArmor...",
        'LOG_TRYING_CMD': "▶️ محاولة الأمر: {cmd}",
        'LOG_ENCRYPT_SUCCESS': "✅ تم تشفير الملف بنجاح.",
        'LOG_ENCRYPT_FAIL': "⚠️ فشل الأمر (كود {code})",
        'LOG_ENCRYPT_EXCEPTION': "❌ استثناء: {error}",
        'LOG_ENCRYPT_ALL_FAIL': "❌ فشلت جميع محاولات تشغيل PyArmor تلقائياً.",
        'LOG_MANUAL_CMD': "يمكنك تشغيل الأمر التالي يدوياً:\n{cmd}",
        'LOG_ENCRYPTED_FILE_SELECTED': "🔐 تم اختيار الملف المشفر يدوياً: {path}",
        'LOG_PYARMOR_TEMP_CLEAN': "🧹 تم حذف المجلد المؤقت لـ PyArmor.",
        'LOG_BUILD_CMD': "⚡ بناء EXE بالأمر: {cmd}",
        'LOG_BUILD_SUCCESS': "🎉 تم بناء EXE بنجاح! (مجلد dist)",
        'LOG_BUILD_FAIL': "❌ فشل البناء بكود: {code}",
        'LOG_BUILD_EXCEPTION': "❌ استثناء أثناء البناء: {error}",
        'LOG_EXTRACT_SELECTED': "📂 تم اختيار EXE: {path}",
        'LOG_EXTRACT_START': "⏳ بدء الاستخراج...",
        'LOG_EXTRACT_SUCCESS': "✅ تم الاستخراج بنجاح",
        'LOG_EXTRACT_CLEANING': "🧹 جاري تنظيف المجلد...",
        'LOG_EXTRACT_MAIN': "🔍 الملف الرئيسي: {path}",
        'LOG_EXTRACT_COPIED': "📄 تم نسخ .pyc إلى: {path}",
        'LOG_EXTRACT_DELETED': "🗑️ تم حذف المجلد المؤقت",
        'LOG_EXTRACT_FAIL': "❌ فشل العملية: {error}",
        'DIALOG_CLOSE_TAB_TITLE': "إغلاق",
        'DIALOG_CLOSE_TAB_MSG': "الملف '{}' به تعديلات غير محفوظة. هل تريد الإغلاق دون حفظ؟",
        'DIALOG_ANALYZE_FIRST': "قم بتحليل الكود أولاً (زر 'تحليل').",
        'DIALOG_INSTALL_COMPLETE': "جميع المكتبات موجودة مسبقاً.",
        'DIALOG_INSTALL_ERROR': "فشل تثبيت PyInstaller:\n{error}",
        'DIALOG_NO_FILE_RUN': "لا يوجد ملف نشط لتشغيله.",
        'DIALOG_SELF_EXEC_WARN': "هذا الملف هو البرنامج نفسه (Python IDLE Pro).\nتشغيله سيؤدي إلى فتح نسخة جديدة من البرنامج.\nيرجى فتح ملف آخر أو إنشاء ملف جديد للتشغيل.",
        'DIALOG_UNSAVED_RUN': "الملف به تغييرات غير محفوظة. هل تريد حفظه قبل التشغيل؟\n(اختر 'نعم' للحفظ، 'لا' للتشغيل بدون حفظ، 'إلغاء' لإلغاء العملية)",
        'DIALOG_UNSAVED_BUILD': "الملف به تغييرات غير محفوظة. هل تريد حفظه قبل البناء؟\n(اختر 'نعم' للحفظ، 'لا' للبناء بدون حفظ، 'إلغاء' لإلغاء العملية)",
        'DIALOG_PYTHON_NOT_FOUND': "لم يتم العثور على مفسر Python النظامي. تأكد من تثبيت Python وإضافته إلى PATH.",
        'DIALOG_SAVE_FIRST': "احفظ الملف أولاً.",
        'DIALOG_NO_EXTERNAL_LIBS': "لا توجد مكتبات خارجية.",
        'DIALOG_PYARMOR_FAILED': "فشل تشغيل PyArmor تلقائياً.\nيمكنك تشغيل الأمر التالي يدوياً:\n{cmd}\n\nبعد التشفير، اختر الملف المشفر يدوياً.",
        'DIALOG_SELECT_ENCRYPTED': "لم تختر ملفاً. هل تريد المتابعة بدون تشفير؟",
        'DIALOG_NO_ENCRYPTED_CONTINUE': "هل تريد المتابعة بدون تشفير؟",
        'EXTRACT_ASK': "✅ تم استخراج ملف .pyc الرئيسي بنجاح:\n{path}\n\nهل تريد فتح موقع pylingual.io لرفعه وتحويله إلى كود Python؟",
        'EXTRACT_TITLE_DONE': "تم الاستخراج",
        'ICON_SELECTED': "🖼️ تم اختيار الأيقونة: {path}",
        'DIALOG_ERROR': "خطأ",
        'DIALOG_INFO': "تنبيه",
        'DIALOG_WARNING': "تحذير",
    }
}
T = TEXTS[LANG]

PROGRAM_PATH = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)

if CTK_AVAILABLE:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

class CTOCEntry:
    def __init__(self, position, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name):
        self.position = position
        self.cmprsdDataSize = cmprsdDataSize
        self.uncmprsdDataSize = uncmprsdDataSize
        self.cmprsFlag = cmprsFlag
        self.typeCmprsData = typeCmprsData
        self.name = name

class PyInstArchive:
    PYINST20_COOKIE_SIZE = 24
    PYINST21_COOKIE_SIZE = 24 + 64
    MAGIC = b'MEI\014\013\012\013\016'

    def __init__(self, path, logger=None):
        self.filePath = path
        self.pycMagic = b'\0' * 4
        self.barePycList = []
        self.logger = logger
        self.entry_point_name = None

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def open(self):
        try:
            self.fPtr = open(self.filePath, 'rb')
            self.fileSize = os.stat(self.filePath).st_size
        except:
            self.log('[!] Error: Could not open {0}'.format(self.filePath))
            return False
        return True

    def close(self):
        try:
            self.fPtr.close()
        except:
            pass

    def checkFile(self):
        self.log('[+] Processing {0}'.format(self.filePath))
        searchChunkSize = 8192
        endPos = self.fileSize
        self.cookiePos = -1

        if endPos < len(self.MAGIC):
            self.log('[!] Error : File is too short or truncated')
            return False

        while True:
            startPos = endPos - searchChunkSize if endPos >= searchChunkSize else 0
            chunkSize = endPos - startPos
            if chunkSize < len(self.MAGIC):
                break
            self.fPtr.seek(startPos, os.SEEK_SET)
            data = self.fPtr.read(chunkSize)
            offs = data.rfind(self.MAGIC)
            if offs != -1:
                self.cookiePos = startPos + offs
                break
            endPos = startPos + len(self.MAGIC) - 1
            if startPos == 0:
                break

        if self.cookiePos == -1:
            self.log('[!] Error : Missing cookie, unsupported pyinstaller version or not a pyinstaller archive')
            return False

        self.fPtr.seek(self.cookiePos + self.PYINST20_COOKIE_SIZE, os.SEEK_SET)
        if b'python' in self.fPtr.read(64).lower():
            self.pyinstVer = 21
            self.log('[+] Pyinstaller version: 2.1+')
        else:
            self.pyinstVer = 20
            self.log('[+] Pyinstaller version: 2.0')
        return True

    def getCArchiveInfo(self):
        try:
            if self.pyinstVer == 20:
                self.fPtr.seek(self.cookiePos, os.SEEK_SET)
                (magic, lengthofPackage, toc, tocLen, pyver) = struct.unpack('!8siiii', self.fPtr.read(self.PYINST20_COOKIE_SIZE))
            elif self.pyinstVer == 21:
                self.fPtr.seek(self.cookiePos, os.SEEK_SET)
                (magic, lengthofPackage, toc, tocLen, pyver, pylibname) = struct.unpack('!8sIIii64s', self.fPtr.read(self.PYINST21_COOKIE_SIZE))
        except:
            self.log('[!] Error : The file is not a pyinstaller archive')
            return False

        self.pymaj, self.pymin = (pyver//100, pyver%100) if pyver >= 100 else (pyver//10, pyver%10)
        self.log('[+] Python version: {0}.{1}'.format(self.pymaj, self.pymin))

        tailBytes = self.fileSize - self.cookiePos - (self.PYINST20_COOKIE_SIZE if self.pyinstVer == 20 else self.PYINST21_COOKIE_SIZE)
        self.overlaySize = lengthofPackage + tailBytes
        self.overlayPos = self.fileSize - self.overlaySize
        self.tableOfContentsPos = self.overlayPos + toc
        self.tableOfContentsSize = tocLen
        self.log('[+] Length of package: {0} bytes'.format(lengthofPackage))
        return True

    def parseTOC(self):
        self.fPtr.seek(self.tableOfContentsPos, os.SEEK_SET)
        self.tocList = []
        parsedLen = 0
        while parsedLen < self.tableOfContentsSize:
            (entrySize, ) = struct.unpack('!i', self.fPtr.read(4))
            nameLen = struct.calcsize('!iIIIBc')
            (entryPos, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name) = struct.unpack(
                '!IIIBc{0}s'.format(entrySize - nameLen),
                self.fPtr.read(entrySize - 4)
            )
            try:
                name = name.decode("utf-8").rstrip("\0")
            except UnicodeDecodeError:
                newName = str(uniquename())
                self.log('[!] Warning: File name {0} contains invalid bytes. Using random name {1}'.format(name, newName))
                name = newName
            if name.startswith("/"):
                name = name.lstrip("/")
            if len(name) == 0:
                name = str(uniquename())
                self.log('[!] Warning: Found an unamed file in CArchive. Using random name {0}'.format(name))

            self.tocList.append(CTOCEntry(
                self.overlayPos + entryPos,
                cmprsdDataSize,
                uncmprsdDataSize,
                cmprsFlag,
                typeCmprsData,
                name
            ))
            parsedLen += entrySize
        self.log('[+] Found {0} files in CArchive'.format(len(self.tocList)))

    def _writeRawData(self, filepath, data, base_dir):
        nm = filepath.replace('\\', os.path.sep).replace('/', os.path.sep).replace('..', '__')
        full_path = os.path.join(base_dir, nm)
        nmDir = os.path.dirname(full_path)
        if nmDir != '' and not os.path.exists(nmDir):
            os.makedirs(nmDir)
        with open(full_path, 'wb') as f:
            f.write(data)

    def extractFiles(self, output_dir):
        self.log('[+] Beginning extraction...please standby')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for entry in self.tocList:
            self.fPtr.seek(entry.position, os.SEEK_SET)
            data = self.fPtr.read(entry.cmprsdDataSize)
            if entry.cmprsFlag == 1:
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    self.log('[!] Error : Failed to decompress {0}'.format(entry.name))
                    continue
            if entry.typeCmprsData == b'd' or entry.typeCmprsData == b'o':
                continue

            if entry.typeCmprsData == b's':
                self.log('[+] Possible entry point: {0}.pyc'.format(entry.name))
                self.entry_point_name = entry.name + '.pyc'
                if self.pycMagic == b'\0' * 4:
                    self.barePycList.append(entry.name + '.pyc')
                self._writePyc(entry.name + '.pyc', data, output_dir)

            elif entry.typeCmprsData == b'M' or entry.typeCmprsData == b'm':
                if data[2:4] == b'\r\n':
                    if self.pycMagic == b'\0' * 4:
                        self.pycMagic = data[0:4]
                    self._writeRawData(entry.name + '.pyc', data, output_dir)
                else:
                    if self.pycMagic == b'\0' * 4:
                        self.barePycList.append(entry.name + '.pyc')
                    self._writePyc(entry.name + '.pyc', data, output_dir)
            else:
                self._writeRawData(entry.name, data, output_dir)
                if entry.typeCmprsData == b'z' or entry.typeCmprsData == b'Z':
                    self._extractPyz(entry.name, output_dir)

        self._fixBarePycs(output_dir)
        return output_dir

    def _fixBarePycs(self, base_dir):
        for pycFile in self.barePycList:
            full_path = os.path.join(base_dir, pycFile)
            try:
                with open(full_path, 'r+b') as f:
                    f.write(self.pycMagic)
            except FileNotFoundError:
                continue

    def _writePyc(self, filename, data, base_dir):
        full_path = os.path.join(base_dir, filename.replace('\\', os.path.sep).replace('/', os.path.sep).replace('..', '__'))
        nmDir = os.path.dirname(full_path)
        if nmDir != '' and not os.path.exists(nmDir):
            os.makedirs(nmDir)
        with open(full_path, 'wb') as pycFile:
            pycFile.write(self.pycMagic)
            if self.pymaj >= 3 and self.pymin >= 7:
                pycFile.write(b'\0' * 4)
                pycFile.write(b'\0' * 8)
            else:
                pycFile.write(b'\0' * 4)
                if self.pymaj >= 3 and self.pymin >= 3:
                    pycFile.write(b'\0' * 4)
            pycFile.write(data)

    def _extractPyz(self, name, base_dir):
        dirName = os.path.join(base_dir, name + '_extracted')
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        full_pyz = os.path.join(base_dir, name)
        with open(full_pyz, 'rb') as f:
            pyzMagic = f.read(4)
            if pyzMagic != b'PYZ\0':
                return
            pyzPycMagic = f.read(4)
            if self.pycMagic == b'\0' * 4:
                self.pycMagic = pyzPycMagic
            elif self.pycMagic != pyzPycMagic:
                self.pycMagic = pyzPycMagic
                self.log('[!] Warning: pyc magic of files inside PYZ archive are different from those in CArchive')

            if self.pymaj != sys.version_info.major or self.pymin != sys.version_info.minor:
                self.log('[!] Warning: This script is running in a different Python version than the one used to build the executable.')
                self.log('[!] Please run this script in Python {0}.{1} to prevent extraction errors during unmarshalling'.format(self.pymaj, self.pymin))
                self.log('[!] Skipping pyz extraction')
                return

            (tocPosition, ) = struct.unpack('!i', f.read(4))
            f.seek(tocPosition, os.SEEK_SET)
            try:
                toc = marshal.load(f)
            except:
                self.log('[!] Unmarshalling FAILED. Cannot extract {0}. Extracting remaining files.'.format(name))
                return

            self.log('[+] Found {0} files in PYZ archive'.format(len(toc)))
            if type(toc) == list:
                toc = dict(toc)

            for key in toc.keys():
                (ispkg, pos, length) = toc[key]
                f.seek(pos, os.SEEK_SET)
                fileName = key
                try:
                    fileName = fileName.decode('utf-8')
                except:
                    pass
                fileName = fileName.replace('..', '__').replace('.', os.path.sep)
                if ispkg == 1:
                    filePath = os.path.join(dirName, fileName, '__init__.pyc')
                else:
                    filePath = os.path.join(dirName, fileName + '.pyc')
                fileDir = os.path.dirname(filePath)
                if not os.path.exists(fileDir):
                    os.makedirs(fileDir)
                if length == 0:
                    self.log('[!] Warning: Empty file {0}'.format(filePath))
                    self._writePyc(filePath, b"", base_dir)
                    continue
                try:
                    data = f.read(length)
                    data = zlib.decompress(data)
                except:
                    self.log('[!] Error: Failed to decompress {0}, probably encrypted. Extracting as is.'.format(filePath))
                    with open(filePath + '.encrypted', 'wb') as enc_f:
                        enc_f.write(data)
                else:
                    self._writePyc(filePath, data, base_dir)


class PyManagerPro(ctk.CTk if CTK_AVAILABLE else Tk):
    def __init__(self):
        if CTK_AVAILABLE:
            super().__init__()
        else:
            Tk.__init__(self)

        self.title(T['APP_TITLE'])
        self.minsize(1024, 600)
        self.option_add("*Font", "Arial 12")

        self.config_file = os.path.join(os.path.expanduser("~"), ".pymanager_config.json")
        self.load_config()

        self.open_files = {}
        self.active_tab_id = None
        self.next_tab_id = 0

        self.detected_libs = []
        self.lib_checkboxes = []
        self.install_status_labels = []
        self.build_process = None
        self.progress_running = False
        self.last_line_count = 0

        self.terminal_process = None

        self.autocomplete_listbox = None
        self.autocomplete_window = None
        self.autocomplete_entries = []
        self.autocomplete_index = 0
        self.current_word = ""

        # Main container
        if CTK_AVAILABLE:
            self.main_paned = ctk.CTkFrame(self, fg_color="transparent")
        else:
            self.main_paned = Tk.Frame(self)
        self.main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Editor frame
        if CTK_AVAILABLE:
            self.editor_frame = ctk.CTkFrame(self.main_paned, corner_radius=10, fg_color="#0d0d1a")
        else:
            self.editor_frame = Tk.Frame(self.main_paned, bg="#0d0d1a")
        self.editor_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Tab bar
        if CTK_AVAILABLE:
            self.tab_bar = ctk.CTkFrame(self.editor_frame, fg_color="transparent", height=32)
        else:
            self.tab_bar = Tk.Frame(self.editor_frame, height=32)
        self.tab_bar.pack(fill="x", padx=6, pady=(6, 0))
        if CTK_AVAILABLE:
            self.tab_slider = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        else:
            self.tab_slider = Tk.Frame(self.tab_bar)
        self.tab_slider.pack(side="left", fill="both", expand=True)

        # Toolbar
        if CTK_AVAILABLE:
            self.editor_toolbar = ctk.CTkFrame(self.editor_frame, fg_color="transparent")
        else:
            self.editor_toolbar = Tk.Frame(self.editor_frame)
        self.editor_toolbar.pack(fill="x", padx=6, pady=(3, 0))

        btn_new = ctk.CTkButton(self.editor_toolbar, text=T['BTN_NEW'], width=70, height=26,
                                command=self.new_file, fg_color="#2a6bb0")
        btn_new.pack(side="left", padx=2)
        btn_open = ctk.CTkButton(self.editor_toolbar, text=T['BTN_OPEN'], width=70, height=26,
                                 command=self.open_file, fg_color="#2a6bb0")
        btn_open.pack(side="left", padx=2)
        btn_save = ctk.CTkButton(self.editor_toolbar, text=T['BTN_SAVE'], width=70, height=26,
                                 command=self.save_file, fg_color="#008f4c")
        btn_save.pack(side="left", padx=2)
        btn_save_as = ctk.CTkButton(self.editor_toolbar, text=T['BTN_SAVE_AS'], width=90, height=26,
                                    command=self.save_as_file, fg_color="#b06b2a")
        btn_save_as.pack(side="left", padx=2)

        btn_close_tab = ctk.CTkButton(self.editor_toolbar, text=T['BTN_CLOSE'], width=70, height=26,
                                      command=self.close_current_tab, fg_color="#b02a2a")
        btn_close_tab.pack(side="left", padx=5)

        self.file_status_label = ctk.CTkLabel(self.editor_toolbar, text=T['STATUS_UNSAVED'],
                                              font=("Arial", 11, "bold"), text_color="#88ddff")
        self.file_status_label.pack(side="right", padx=10)

        # Editor container
        if CTK_AVAILABLE:
            self.editor_container = ctk.CTkFrame(self.editor_frame, fg_color="transparent")
        else:
            self.editor_container = Tk.Frame(self.editor_frame)
        self.editor_container.pack(fill="both", expand=True, padx=6, pady=(3, 6))

        # Line numbers
        self.line_numbers = Text(self.editor_container, width=4, padx=3, pady=3, takefocus=0,
                                 font=("Arial", 12), background="#1e1e2e", foreground="#8888aa",
                                 relief="flat", borderwidth=0, state="disabled")
        self.line_numbers.pack(side="left", fill="y")

        # Main editor - NOW WITH KEYBOARD SHORTCUTS ENABLED BY DEFAULT
        self.editor = Text(self.editor_container, wrap="none", font=("Arial", 12),
                           background="#0d0d1a", foreground="#eeeeee",
                           insertbackground="white", relief="flat", borderwidth=0,
                           highlightthickness=0, undo=True)
        self.editor.pack(side="left", fill="both", expand=True)

        # Enable default keyboard shortcuts (Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A)
        # The Text widget already supports these by default, but we ensure they work

        # Context menu
        self.editor_context_menu = Menu(self.editor, tearoff=0)
        self.editor_context_menu.add_command(label="Cut", command=lambda: self.editor.event_generate("<<Cut>>"))
        self.editor_context_menu.add_command(label="Copy", command=lambda: self.editor.event_generate("<<Copy>>"))
        self.editor_context_menu.add_command(label="Paste", command=lambda: self.editor.event_generate("<<Paste>>"))
        self.editor_context_menu.add_command(label="Select All", command=lambda: self.editor.event_generate("<<SelectAll>>"))
        self.editor.bind("<Button-3>", self.show_editor_context_menu)

        # Bind keyboard shortcuts explicitly
        self.editor.bind("<Control-c>", lambda e: self._copy_text())
        self.editor.bind("<Control-v>", lambda e: self._paste_text())
        self.editor.bind("<Control-x>", lambda e: self._cut_text())
        self.editor.bind("<Control-a>", lambda e: self._select_all())
        self.editor.bind("<KeyRelease>", self.on_editor_change)
        self.editor.bind("<MouseWheel>", self.on_editor_scroll)
        self.editor.bind("<Button-4>", self.on_editor_scroll)
        self.editor.bind("<Button-5>", self.on_editor_scroll)
        self.editor.bind("<Configure>", self.on_editor_resize)
        self.editor.bind("<FocusIn>", self.on_editor_focus)
        self.editor.bind("<Control-space>", self.show_autocomplete)
        self.editor.bind("<Escape>", self.hide_autocomplete)

        # Scrollbar
        self.editor_vscroll = Scrollbar(self.editor_container, orient="vertical",
                                        command=self.on_editor_vscroll)
        self.editor_vscroll.pack(side="right", fill="y")
        self.editor.config(yscrollcommand=self.editor_vscroll.set)
        self.line_numbers.config(yscrollcommand=self.on_line_scroll)

        # Control panel
        if CTK_AVAILABLE:
            self.control_frame = ctk.CTkScrollableFrame(
                self.main_paned, corner_radius=10, width=350,
                fg_color="#111125", label_text=T['PANEL_TITLE']
            )
        else:
            self.control_frame = Tk.Frame(self.main_paned, width=350)
            self.control_frame.pack_propagate(False)
        self.control_frame.pack(side="right", fill="both", padx=(8, 0))

        self._build_control_panel()

        self.new_file()
        self.log(T['LOG_READY'])

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts for the whole app
        self.bind_all("<Control-s>", lambda e: self.save_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<F5>", lambda e: self.run_script())
        self.bind_all("<Control-Shift-S>", lambda e: self.save_as_file())

        self.autocomplete_active = False

    def _copy_text(self):
        """Copy selected text to clipboard"""
        try:
            selected = self.editor.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected)
        except:
            pass
        return "break"

    def _paste_text(self):
        """Paste text from clipboard"""
        try:
            text = self.clipboard_get()
            self.editor.insert("insert", text)
        except:
            pass
        return "break"

    def _cut_text(self):
        """Cut selected text"""
        try:
            selected = self.editor.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected)
            self.editor.delete("sel.first", "sel.last")
        except:
            pass
        return "break"

    def _select_all(self):
        """Select all text in editor"""
        self.editor.tag_add("sel", "1.0", "end")
        return "break"

    def show_editor_context_menu(self, event):
        self.editor_context_menu.post(event.x_root, event.y_root)

    def get_python_interpreter(self):
        """Get the correct Python interpreter - FIXED VERSION"""
        # First, try to find a system Python that's different from frozen executable
        if getattr(sys, 'frozen', False):
            # We're running as a frozen executable
            # Try common Python commands
            for cmd in ['python', 'python3', 'py']:
                python_path = shutil.which(cmd)
                if python_path:
                    if os.path.abspath(python_path) != os.path.abspath(sys.executable):
                        return python_path

            # Try py launcher on Windows
            try:
                result = subprocess.run(['py', '-3', '-c', 'import sys; print(sys.executable)'],
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    py_path = result.stdout.strip()
                    if os.path.abspath(py_path) != os.path.abspath(sys.executable):
                        return py_path
            except:
                pass

            # Check common installation paths
            common_paths = [
                r"C:\Python313\python.exe",
                r"C:\Python312\python.exe",
                r"C:\Python311\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python39\python.exe",
                r"C:\Python38\python.exe",
                r"C:\Users\{}\AppData\Local\Programs\Python\Python313\python.exe".format(os.getenv('USERNAME')),
                r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(os.getenv('USERNAME')),
                r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME')),
                r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME')),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    if os.path.abspath(path) != os.path.abspath(sys.executable):
                        return path

            # If we can't find another Python, use current but warn
            self.log("⚠️ Warning: Using frozen executable as interpreter. Arabic variables may not work.")
            return sys.executable
        else:
            # Running from source - use current interpreter
            return sys.executable

    def _build_control_panel(self):
        # Quick actions
        if CTK_AVAILABLE:
            quick_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        else:
            quick_frame = Tk.Frame(self.control_frame)
        quick_frame.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkButton(quick_frame, text=T['BTN_NEW_PROJECT'], width=120, height=28,
                      command=self.new_project, fg_color="#2a6bb0").pack(side="left", padx=2)
        ctk.CTkButton(quick_frame, text=T['BTN_REQUIREMENTS'], width=120, height=28,
                      command=self.generate_requirements, fg_color="#008f4c").pack(side="left", padx=2)

        # Analyze frame
        if CTK_AVAILABLE:
            analyze_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        else:
            analyze_frame = Tk.Frame(self.control_frame)
        analyze_frame.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkButton(analyze_frame, text=T['BTN_ANALYZE'], width=130, height=30,
                      command=self.analyze_editor_code, fg_color="#6b2ab0").pack(side="left", padx=4)
        ctk.CTkButton(analyze_frame, text=T['BTN_INSTALL_MISSING'], width=140, height=30,
                      command=self.install_missing_libs, fg_color="#008f4c").pack(side="right", padx=4)

        # Libraries scroll frame
        if CTK_AVAILABLE:
            self.lib_scroll_frame = ctk.CTkScrollableFrame(
                self.control_frame, label_text=T['LIBS_TITLE'],
                corner_radius=8, height=120
            )
        else:
            self.lib_scroll_frame = Tk.Frame(self.control_frame)
            Tk.Label(self.lib_scroll_frame, text=T['LIBS_TITLE']).pack()
        self.lib_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(4, 8))

        if CTK_AVAILABLE:
            self.libs_container = ctk.CTkFrame(self.lib_scroll_frame, fg_color="transparent")
        else:
            self.libs_container = Tk.Frame(self.lib_scroll_frame)
        self.libs_container.pack(fill="both", expand=True, padx=4, pady=4)

        # Tools frame
        if CTK_AVAILABLE:
            tools_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        else:
            tools_frame = Tk.Frame(self.control_frame)
        tools_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(tools_frame, text=T['BTN_FORMAT'], width=110, height=28,
                      command=self.format_code, fg_color="#2a6bb0").pack(side="left", padx=2)
        ctk.CTkButton(tools_frame, text=T['BTN_LINT'], width=110, height=28,
                      command=self.lint_code, fg_color="#b06b2a").pack(side="left", padx=2)
        ctk.CTkButton(tools_frame, text=T['BTN_TERMINAL'], width=100, height=28,
                      command=self.toggle_terminal, fg_color="#6b2ab0").pack(side="left", padx=2)

        # Terminal frame
        if CTK_AVAILABLE:
            self.terminal_frame = ctk.CTkFrame(self.control_frame, fg_color="#0a0a1a", corner_radius=6)
        else:
            self.terminal_frame = Tk.Frame(self.control_frame, bg="#0a0a1a")
        self.terminal_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.terminal_frame.pack_forget()

        self.terminal_text = ctk.CTkTextbox(self.terminal_frame, wrap="word", font=("Arial", 11), height=100)
        self.terminal_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.terminal_entry = ctk.CTkEntry(self.terminal_frame, placeholder_text="Enter command...")
        self.terminal_entry.pack(fill="x", padx=4, pady=(0,4))
        self.terminal_entry.bind("<Return>", self.execute_terminal_command)

        # Build frame
        if CTK_AVAILABLE:
            build_frame = ctk.CTkFrame(self.control_frame, corner_radius=8, fg_color="#1a1a30")
        else:
            build_frame = Tk.Frame(self.control_frame, bg="#1a1a30")
        build_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(build_frame, text=T['BUILD_TITLE'], font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=4)

        if CTK_AVAILABLE:
            opt_grid = ctk.CTkFrame(build_frame, fg_color="transparent")
        else:
            opt_grid = Tk.Frame(build_frame)
        opt_grid.pack(fill="x", padx=8, pady=4)

        self.onefile_var = ctk.BooleanVar(value=True)
        self.noconsole_var = ctk.BooleanVar(value=True)
        self.windowed_var = ctk.BooleanVar(value=False)
        self.pyarmor_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(opt_grid, text=T['CHECK_ONEFILE'], variable=self.onefile_var, font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=1)
        ctk.CTkCheckBox(opt_grid, text=T['CHECK_NOCONSOLE'], variable=self.noconsole_var, font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=1)
        ctk.CTkCheckBox(opt_grid, text=T['CHECK_WINDOWED'], variable=self.windowed_var, font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=1)
        ctk.CTkCheckBox(opt_grid, text=T['CHECK_PYARMOR'], variable=self.pyarmor_var, font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=1)

        ctk.CTkLabel(opt_grid, text=T['LABEL_FILENAME'], font=("Arial", 11)).grid(row=0, column=1, sticky="w", padx=(15, 4))
        self.output_name_entry = ctk.CTkEntry(opt_grid, placeholder_text="my_app", width=100, height=26)
        self.output_name_entry.grid(row=0, column=2, sticky="w", pady=1)

        ctk.CTkLabel(opt_grid, text=T['LABEL_ICON'], font=("Arial", 11)).grid(row=1, column=1, sticky="w", padx=(15, 4))
        icon_sel = ctk.CTkFrame(opt_grid, fg_color="transparent")
        icon_sel.grid(row=1, column=2, sticky="w", pady=1)
        self.icon_path_var = ctk.StringVar(value="")
        ctk.CTkEntry(icon_sel, textvariable=self.icon_path_var, placeholder_text="path", width=70, height=26).pack(side="left")
        ctk.CTkButton(icon_sel, text="📂", width=26, height=26, command=self.select_icon).pack(side="right", padx=2)

        action_frame = ctk.CTkFrame(build_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=8, pady=(6, 4))

        self.run_btn = ctk.CTkButton(action_frame, text=T['BTN_RUN'], width=110, height=30,
                                     command=self.run_script, fg_color="#b06b2a")
        self.run_btn.pack(side="left", padx=4)

        self.build_btn = ctk.CTkButton(action_frame, text=T['BTN_BUILD'], width=110, height=30,
                                       command=self.build_exe, fg_color="#b02a6b")
        self.build_btn.pack(side="right", padx=4)

        self.progress_bar = ctk.CTkProgressBar(build_frame, width=280, height=16, corner_radius=8)
        self.progress_bar.pack(pady=(6, 2), padx=8)
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(build_frame, text=T['PROGRESS_WAITING'], font=("Arial", 11), text_color="#88ddff")
        self.progress_label.pack(pady=(0, 4))

        # EXE Extract frame
        if CTK_AVAILABLE:
            exe_extract_frame = ctk.CTkFrame(self.control_frame, corner_radius=8, fg_color="#1a1a30")
        else:
            exe_extract_frame = Tk.Frame(self.control_frame, bg="#1a1a30")
        exe_extract_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(exe_extract_frame, text=T['EXTRACT_TITLE'], font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=4)

        exe_btn_frame = ctk.CTkFrame(exe_extract_frame, fg_color="transparent")
        exe_btn_frame.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(exe_btn_frame, text=T['BTN_EXTRACT_PYC'], width=140, height=28,
                      command=self.extract_pyc_from_exe, fg_color="#b06b2a").grid(row=0, column=0, padx=4, pady=2)
        ctk.CTkButton(exe_btn_frame, text=T['BTN_PYLINGUAL'], width=140, height=28,
                      command=lambda: webbrowser.open("https://pylingual.io/"), fg_color="#2a6bb0").grid(row=0, column=1, padx=4, pady=2)

        # Log frame
        if CTK_AVAILABLE:
            log_frame = ctk.CTkFrame(self.control_frame, corner_radius=8, fg_color="#0a0a1a")
        else:
            log_frame = Tk.Frame(self.control_frame, bg="#0a0a1a")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        ctk.CTkLabel(log_frame, text=T['LOG_TITLE'], font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=4)

        self.log_text = ctk.CTkTextbox(
            log_frame, wrap="word", font=("Arial", 11),
            height=100, border_width=0, fg_color="#0a0a1a"
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))


    def load_config(self):
        default = {
            "theme": "Dark",
            "window_geometry": "1280x700",
            "last_file": None,
            "autocomplete": True,
            "lint_on_save": False,
        }
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except:
            self.config = default
        if CTK_AVAILABLE:
            ctk.set_appearance_mode(self.config.get("theme", "Dark"))
        self.geometry(self.config.get("window_geometry", "1280x700"))

    def save_config(self):
        self.config["window_geometry"] = self.geometry()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except:
            pass

    def on_closing(self):
        if self.active_tab_id:
            self.config["last_file"] = self.open_files[self.active_tab_id]['path']
        self.save_config()
        self.destroy()

    def add_tab(self, path=None, content=""):
        tab_id = str(self.next_tab_id)
        self.next_tab_id += 1
        if CTK_AVAILABLE:
            tab_frame = ctk.CTkFrame(self.tab_slider, fg_color="transparent")
        else:
            tab_frame = Tk.Frame(self.tab_slider)
        tab_frame.pack(side="left", padx=1, pady=1)
        btn = ctk.CTkButton(tab_frame, text=os.path.basename(path) if path else T['TAB_UNSAVED'],
                            width=80, height=24, corner_radius=4,
                            fg_color="#2a2a4a", hover_color="#3a3a6a",
                            font=("Arial", 11),
                            command=lambda: self.switch_tab(tab_id))
        btn.pack(side="left")
        close_btn = ctk.CTkButton(tab_frame, text="✕", width=18, height=18, fg_color="#b02a2a",
                                  hover_color="#d03a3a", font=("Arial", 9),
                                  command=lambda: self.close_tab(tab_id))
        close_btn.pack(side="left", padx=(0, 2))
        self.open_files[tab_id] = {
            'path': path,
            'content': content,
            'modified': False,
            'button': btn,
            'tab_frame': tab_frame,
            'close_btn': close_btn
        }
        self.switch_tab(tab_id)
        self.update_status_label()
        return tab_id

    def switch_tab(self, tab_id):
        if self.active_tab_id == tab_id:
            return
        if self.active_tab_id is not None:
            current = self.open_files[self.active_tab_id]
            current['content'] = self.editor.get("1.0", "end-1c")
            current['modified'] = self.editor.edit_modified()
        if self.active_tab_id is not None:
            old_btn = self.open_files[self.active_tab_id]['button']
            old_btn.configure(fg_color="#2a2a4a")
        self.active_tab_id = tab_id
        data = self.open_files[tab_id]
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", data['content'])
        self.editor.edit_modified(data['modified'])
        data['button'].configure(fg_color="#4a4a8a")
        self.update_tab_title(tab_id)
        self.update_status_label()
        self.last_line_count = 0
        self.update_line_numbers()

    def close_tab(self, tab_id):
        if tab_id not in self.open_files:
            return
        data = self.open_files[tab_id]
        if data['modified']:
            if not messagebox.askyesno(T['DIALOG_CLOSE_TAB_TITLE'], T['DIALOG_CLOSE_TAB_MSG'].format(os.path.basename(data['path']) if data['path'] else T['TAB_UNSAVED'])):
                return
        data['tab_frame'].destroy()
        del self.open_files[tab_id]
        if self.active_tab_id == tab_id:
            self.active_tab_id = None
            if self.open_files:
                new_active = list(self.open_files.keys())[0]
                self.switch_tab(new_active)
            else:
                self.new_file()
        else:
            self.update_tab_title(tab_id)

    def close_current_tab(self):
        if self.active_tab_id is not None:
            self.close_tab(self.active_tab_id)

    def update_tab_title(self, tab_id):
        if tab_id not in self.open_files:
            return
        data = self.open_files[tab_id]
        name = os.path.basename(data['path']) if data['path'] else T['TAB_UNSAVED']
        if data['modified']:
            name += " *"
        data['button'].configure(text=name)

    def update_status_label(self):
        if self.active_tab_id is None:
            self.file_status_label.configure(text=T['STATUS_NO_ACTIVE'])
            return
        data = self.open_files[self.active_tab_id]
        path = data['path']
        if path:
            self.file_status_label.configure(text=f"📄 {os.path.basename(path)}")
        else:
            self.file_status_label.configure(text=T['STATUS_UNSAVED'])

    def get_active_file_path(self):
        if self.active_tab_id is None:
            return None
        return self.open_files[self.active_tab_id]['path']

    def get_active_content(self):
        if self.active_tab_id is None:
            return ""
        return self.editor.get("1.0", "end-1c")

    def save_current_content(self):
        if self.active_tab_id is not None:
            self.open_files[self.active_tab_id]['content'] = self.editor.get("1.0", "end-1c")
            self.open_files[self.active_tab_id]['modified'] = self.editor.edit_modified()
            self.update_tab_title(self.active_tab_id)

    def update_line_numbers(self, event=None):
        if self.active_tab_id is None:
            return
        try:
            first, last = self.editor.yview()
        except:
            first, last = 0.0, 1.0
        line_count = int(self.editor.index('end-1c').split('.')[0])
        if line_count == self.last_line_count:
            return
        self.last_line_count = line_count
        lines = "\n".join(str(i+1) for i in range(line_count))
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", lines)
        self.line_numbers.config(state="disabled")
        self.line_numbers.config(width=max(3, len(str(line_count)) + 1))
        self.editor.yview_moveto(first)
        self.line_numbers.yview_moveto(first)

    def on_editor_change(self, event=None):
        if self.active_tab_id is not None:
            self.open_files[self.active_tab_id]['modified'] = self.editor.edit_modified()
            self.update_tab_title(self.active_tab_id)
        self.update_line_numbers()

    def on_editor_scroll(self, event):
        try:
            first, last = self.editor.yview()
            self.line_numbers.yview_moveto(first)
        except:
            pass

    def on_line_scroll(self, *args):
        try:
            first, last = self.line_numbers.yview()
            self.editor.yview_moveto(first)
        except:
            pass

    def on_editor_vscroll(self, *args):
        self.editor.yview(*args)
        try:
            first, last = self.editor.yview()
            self.line_numbers.yview_moveto(first)
        except:
            pass

    def on_editor_resize(self, event):
        self.update_line_numbers()

    def on_editor_focus(self, event):
        self.update_line_numbers()

    def new_file(self):
        content = self.editor.get("1.0", "end-1c") if self.active_tab_id is not None else ""
        if self.active_tab_id is not None and len(self.open_files) == 1:
            data = self.open_files[self.active_tab_id]
            if data['path'] is None and not data['modified'] and data['content'] == "":
                self.editor.delete("1.0", "end")
                self.editor.edit_modified(False)
                data['content'] = ""
                data['modified'] = False
                self.update_tab_title(self.active_tab_id)
                self.update_status_label()
                self.last_line_count = 0
                self.update_line_numbers()
                self.log(T['LOG_NEW_FILE'])
                return
        self.add_tab(content="")
        self.log(T['LOG_TAB_CREATED'])

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        threading.Thread(target=self._open_file_thread, args=(file_path,), daemon=True).start()

    def _open_file_thread(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.after(0, lambda: self._open_file_done(file_path, content))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_OPEN_ERROR'].format(error=e)))
            self.after(0, lambda: messagebox.showerror(T['DIALOG_ERROR'], f"Cannot read file:\n{e}"))

    def _open_file_done(self, file_path, content):
        for tid, data in self.open_files.items():
            if data['path'] == file_path:
                self.switch_tab(tid)
                self.log(T['LOG_ALREADY_OPEN'].format(path=file_path))
                return
        self.add_tab(path=file_path, content=content)
        self.log(T['LOG_FILE_OPENED'].format(path=file_path))
        self.analyze_editor_code()

    def save_file(self):
        if self.active_tab_id is None:
            return
        data = self.open_files[self.active_tab_id]
        if data['path'] is None:
            self.save_as_file()
            return
        try:
            content = self.editor.get("1.0", "end-1c")
            with open(data['path'], "w", encoding="utf-8") as f:
                f.write(content)
            data['modified'] = False
            self.editor.edit_modified(False)
            self.update_tab_title(self.active_tab_id)
            self.update_status_label()
            self.log(T['LOG_FILE_SAVED'].format(path=data['path']))
            self.analyze_editor_code()
        except Exception as e:
            self.log(T['LOG_OPEN_ERROR'].format(error=e))
            messagebox.showerror(T['DIALOG_ERROR'], f"Cannot save file:\n{e}")

    def save_as_file(self):
        if self.active_tab_id is None:
            return
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        data = self.open_files[self.active_tab_id]
        data['path'] = file_path
        self.save_file()

    def new_project(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Project Template")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Choose a project template:", font=("Arial", 14, "bold")).pack(pady=10)

        templates = [
            "📄 Blank",
            "🖼️ Tkinter (GUI)",
            "🎮 Pygame (Game)",
            "🌐 Flask (Web)",
            "📦 Django (Web)",
            "⚡ FastAPI (Web)",
            "🧩 Tkinter OOP",
            "💎 PyQt5 (GUI)",
            "📱 Kivy (Mobile)",
            "🤖 Discord Bot",
            "🌿 BeautifulSoup (Scraper)",
            "📊 Data Science (Pandas/Matplotlib)"
        ]

        selected = StringVar(value=templates[0])
        combo = ctk.CTkComboBox(dialog, values=templates, variable=selected, font=("Arial", 12), width=300)
        combo.pack(pady=10)

        def create_project():
            choice = selected.get()
            dialog.destroy()
            folder = filedialog.askdirectory(title="Select Project Folder")
            if not folder:
                return
            os.makedirs(folder, exist_ok=True)

            templates_content = {
                "📄 Blank": """# Blank Project
print("Welcome to your new project!")
""",
                "🖼️ Tkinter (GUI)": """import tkinter as tk

root = tk.Tk()
root.title("Tkinter App")
root.geometry("400x300")

label = tk.Label(root, text="Hello World!")
label.pack(pady=50)

button = tk.Button(root, text="Click Me", command=lambda: label.config(text="Clicked!"))
button.pack()

root.mainloop()
""",
                "🎮 Pygame (Game)": """import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Pygame Game")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 255, 255), (300, 200), 50)
    pygame.display.flip()
    clock.tick(60)
""",
                "🌐 Flask (Web)": """from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Welcome to Flask!</h1>'

if __name__ == '__main__':
    app.run(debug=True)
""",
                "📦 Django (Web)": """# Django project – create using django-admin startproject
# This is just a placeholder settings file.
print("Run: django-admin startproject myproject")
""",
                "⚡ FastAPI (Web)": """from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def home():
    return {'message': 'Hello from FastAPI'}

# Run with: uvicorn main:app --reload
""",
                "🧩 Tkinter OOP": """import tkinter as tk

class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter OOP App")
        self.label = tk.Label(root, text="Hello")
        self.label.pack()
        self.button = tk.Button(root, text="Click", command=self.click)
        self.button.pack()

    def click(self):
        self.label.config(text="Clicked!")

root = tk.Tk()
app = MyApp(root)
root.mainloop()
""",
                "💎 PyQt5 (GUI)": """from PyQt5 import QtWidgets
import sys

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
window.setWindowTitle("PyQt5 App")
window.setGeometry(100, 100, 400, 300)

label = QtWidgets.QLabel("Hello from PyQt5", window)
label.move(150, 120)

window.show()
sys.exit(app.exec_())
""",
                "📱 Kivy (Mobile)": """from kivy.app import App
from kivy.uix.label import Label

class MyApp(App):
    def build(self):
        return Label(text="Hello from Kivy")

if __name__ == '__main__':
    MyApp().run()
""",
                "🤖 Discord Bot": """import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

bot.run('TOKEN_HERE')
""",
                "🌿 BeautifulSoup (Scraper)": """import requests
from bs4 import BeautifulSoup

url = 'https://example.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

print(soup.title.text)
""",
                "📊 Data Science (Pandas/Matplotlib)": """import pandas as pd
import matplotlib.pyplot as plt

data = {'name': ['Alice', 'Bob', 'Charlie'], 'score': [85, 92, 78]}
df = pd.DataFrame(data)
print(df)

df.plot(kind='bar', x='name', y='score')
plt.title('Scores')
plt.show()
"""
            }

            for key, code in templates_content.items():
                if key == choice:
                    content = code
                    break
            else:
                content = templates_content[templates[0]]

            main_file = os.path.join(folder, "main.py")
            with open(main_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"✅ Created {choice} project in {folder}")
            self.open_file_path(main_file)

        ctk.CTkButton(dialog, text="Create Project", command=create_project, fg_color="#008f4c").pack(pady=20)

    def open_file_path(self, file_path):
        threading.Thread(target=self._open_file_thread, args=(file_path,), daemon=True).start()

    def analyze_editor_code(self):
        self.log(T['LOG_ANALYZING'])
        self.start_progress(T['LOG_ANALYZING'])
        threading.Thread(target=self._analyze_thread, daemon=True).start()

    def _analyze_thread(self):
        try:
            code = self.editor.get("1.0", "end-1c")
            if not code.strip():
                self.after(0, lambda: self.log(T['LOG_EDITOR_EMPTY']))
                self.after(0, lambda: self._display_no_libs())
                self.after(0, lambda: self.stop_progress(True))
                return

            tree = ast.parse(code)
            libs_set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        libs_set.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        libs_set.add(node.module.split('.')[0])

            builtin_modules = set(sys.builtin_module_names)
            std_libs = {
                'sys', 'os', 're', 'math', 'json', 'csv', 'datetime', 'collections',
                'itertools', 'functools', 'typing', 'argparse', 'logging', 'subprocess',
                'shutil', 'pathlib', 'time', 'random', 'string', 'socket', 'hashlib',
                'base64', 'threading', 'multiprocessing', 'pickle', 'sqlite3', 'xml',
                'html', 'urllib', 'http', 'email', 'tempfile', 'stat', 'io', 'textwrap',
                'pprint', 'inspect', 'pdb', 'unittest', 'doctest', 'dataclasses', 'enum',
                'warnings', 'contextlib', 'abc', 'weakref', 'copy', 'struct', 'array',
                'bisect', 'heapq', 'decimal', 'fractions', 'calendar', 'locale',
                'gettext', 'importlib', 'pkgutil', 'traceback', 'linecache', 'tkinter',
                'cProfile', 'pstats', 'zipfile', 'tarfile', 'configparser', 'xmlrpc'
            }
            std_libs.update(builtin_modules)

            external_libs = [lib for lib in libs_set if lib not in std_libs and not lib.startswith('_')]

            if not external_libs:
                self.after(0, lambda: self.log(T['LOG_NO_EXTERNAL']))
                self.after(0, lambda: self._display_no_libs())
                self.after(0, lambda: self.stop_progress(True))
                return

            self.after(0, lambda: self.log(T['LOG_LIBS_FOUND'].format(count=len(external_libs))))
            self.after(0, lambda: self._display_libs(external_libs))
            self.after(0, lambda: self.stop_progress(True))
        except SyntaxError as e:
            self.after(0, lambda: self.log(T['LOG_SYNTAX_ERROR'].format(error=e)))
            self.after(0, lambda: self._display_error(T['LOG_SYNTAX_ERROR'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_ANALYSIS_ERROR'].format(error=e)))
            self.after(0, lambda: self._display_error(T['LOG_ANALYSIS_ERROR'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))

    def _display_no_libs(self):
        self.clear_libs_display()
        ctk.CTkLabel(self.libs_container, text="✅ All imports are built-in.", font=("Arial", 12)).pack(pady=10)

    def _display_error(self, msg):
        self.clear_libs_display()
        ctk.CTkLabel(self.libs_container, text=msg, font=("Arial", 12), text_color="#ff4444").pack(pady=10)

    def _display_libs(self, external_libs):
        self.clear_libs_display()
        self.detected_libs = external_libs
        for lib in sorted(external_libs):
            row = ctk.CTkFrame(self.libs_container, fg_color="transparent")
            row.pack(fill="x", pady=1)

            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(row, text=lib, variable=var, font=("Arial", 11, "bold"))
            cb.pack(side="left", padx=(4, 8))
            self.lib_checkboxes.append((lib, var))

            is_installed = self.check_lib_installed(lib)
            status = "✅ Installed" if is_installed else "❌ Not installed"
            color = "#66ff88" if is_installed else "#ff6688"
            label = ctk.CTkLabel(row, text=status, font=("Arial", 10), text_color=color)
            label.pack(side="left", padx=4)
            self.install_status_labels.append(label)

    def clear_libs_display(self):
        for widget in self.libs_container.winfo_children():
            widget.destroy()
        self.lib_checkboxes = []
        self.install_status_labels = []

    def check_lib_installed(self, lib_name):
        try:
            spec = importlib.util.find_spec(lib_name)
            return spec is not None
        except (ImportError, AttributeError, ValueError):
            return False

    def install_missing_libs(self):
        if not self.detected_libs:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_ANALYZE_FIRST'])
            return

        libs_to_install = []
        for lib, var in self.lib_checkboxes:
            if var.get() and not self.check_lib_installed(lib):
                libs_to_install.append(lib)

        if not libs_to_install:
            self.log(T['LOG_ALL_INSTALLED'])
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_INSTALL_COMPLETE'])
            return

        self.log(T['LOG_INSTALLING_START'].format(count=len(libs_to_install)))
        self.start_progress(T['LOG_INSTALLING_START'].format(count=len(libs_to_install)))

        def install_thread():
            success = True
            for lib in libs_to_install:
                try:
                    self.log(T['LOG_INSTALLING_LIB'].format(lib=lib))
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "pip", "install", lib],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace", bufsize=1
                    )
                    for line in proc.stdout:
                        self.log(f"  {line.strip()}")
                    proc.wait()
                    if proc.returncode == 0:
                        self.log(T['LOG_INSTALL_SUCCESS'].format(lib=lib))
                    else:
                        self.log(T['LOG_INSTALL_FAIL'].format(lib=lib, code=proc.returncode))
                        success = False
                except Exception as e:
                    self.log(T['LOG_INSTALL_EXCEPTION'].format(lib=lib, error=e))
                    success = False
            self.after(0, lambda: self.stop_progress(success))
            self.after(0, lambda: messagebox.showinfo(T['DIALOG_INFO'], T['MSG_INSTALL_DONE_SUCCESS'] if success else T['MSG_INSTALL_DONE_ERROR']))
            self.after(0, self.analyze_editor_code)

        threading.Thread(target=install_thread, daemon=True).start()

    def _is_gui_script(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code)
            gui_libs = {'tkinter', 'PyQt5', 'PySide2', 'PySide6', 'wx', 'wxpython', 'pygame', 'kivy', 'PySimpleGUI', 'dearpygui'}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split('.')[0]
                        if name in gui_libs:
                            return True
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split('.')[0]
                        if name in gui_libs:
                            return True
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in {'Tk', 'Toplevel', 'QApplication', 'QWidget', 'wx.App', 'pygame.init'}:
                            return True
            return False
        except:
            return False

    def run_script(self):
        """Run the current script - FIXED for Arabic variables"""
        if self.active_tab_id is None:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_NO_FILE_RUN'])
            return

        file_path = self.get_active_file_path()
        if not file_path:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_SAVE_FIRST'])
            return

        if os.path.abspath(file_path) == PROGRAM_PATH:
            messagebox.showwarning(T['DIALOG_WARNING'], T['DIALOG_SELF_EXEC_WARN'])
            return

        data = self.open_files[self.active_tab_id]
        if data['modified']:
            answer = messagebox.askyesnocancel(T['DIALOG_WARNING'], T['DIALOG_UNSAVED_RUN'])
            if answer is None:
                return
            elif answer:
                self.save_file()
                if not self.get_active_file_path():
                    return

        is_gui = self._is_gui_script(file_path)
        python_exe = self.get_python_interpreter()

        # Check if we found a proper interpreter
        if getattr(sys, 'frozen', False) and os.path.abspath(python_exe) == os.path.abspath(sys.executable):
            messagebox.showerror(T['DIALOG_ERROR'], T['DIALOG_PYTHON_NOT_FOUND'])
            self.stop_progress(False)
            return

        self.log(f"ℹ️ Using interpreter: {python_exe}")
        self.log(f"ℹ️ File: {file_path}")

        if is_gui:
            self.log(T['LOG_GUI_DETECTED'])
        else:
            self.log(T['LOG_NO_GUI'])

        self.start_progress(T['BTN_RUN'])
        if is_gui:
            threading.Thread(target=self._run_gui, args=(python_exe, file_path), daemon=True).start()
        else:
            threading.Thread(target=self._run_non_gui, args=(python_exe, file_path), daemon=True).start()

    def _run_gui(self, python_exe, file_path):
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [python_exe, file_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=None, stderr=None, stdin=None,
                    close_fds=True
                )
            else:
                subprocess.Popen(
                    [python_exe, file_path],
                    stdout=None, stderr=None, stdin=None,
                    start_new_session=True
                )
            self.after(0, lambda: self.log(T['LOG_RUN_SUCCESS_GUI']))
            self.after(0, lambda: self.stop_progress(True))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_RUN_FAIL'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))

    def _run_non_gui(self, python_exe, file_path):
        try:
            if sys.platform == "win32":
                cmd = [python_exe, "-i", file_path]
                self.log(f"▶️ Running: {' '.join(cmd)}")
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=None, stderr=None, stdin=None,
                    close_fds=True
                )
            else:
                cmd = [python_exe, "-i", file_path]
                self.log(f"▶️ Running: {' '.join(cmd)}")
                terminals = [
                    ["gnome-terminal", "--"] + cmd,
                    ["xterm", "-hold", "-e"] + cmd,
                    ["konsole", "-e"] + cmd,
                    ["xfce4-terminal", "-e"] + cmd,
                    ["lxterminal", "-e"] + cmd,
                    ["terminator", "-e"] + cmd,
                ]
                executed = False
                for term_cmd in terminals:
                    try:
                        subprocess.Popen(term_cmd, stdout=None, stderr=None, stdin=None, start_new_session=True)
                        executed = True
                        break
                    except FileNotFoundError:
                        continue
                if not executed:
                    subprocess.Popen(cmd, stdout=None, stderr=None, stdin=None, start_new_session=True)
            self.after(0, lambda: self.log(T['LOG_RUN_SUCCESS_NON_GUI']))
            self.after(0, lambda: self.stop_progress(True))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_RUN_FAIL'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))

    def toggle_terminal(self):
        if self.terminal_frame.winfo_ismapped():
            self.terminal_frame.pack_forget()
        else:
            self.terminal_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def execute_terminal_command(self, event=None):
        cmd = self.terminal_entry.get().strip()
        if not cmd:
            return
        self.terminal_entry.delete(0, "end")
        self.terminal_text.insert("end", f"> {cmd}\n")
        self.terminal_text.see("end")

        threading.Thread(target=self._run_terminal_command, args=(cmd,), daemon=True).start()

    def _run_terminal_command(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                self.after(0, self._append_terminal_text, line)
            proc.wait()
            if proc.returncode != 0:
                self.after(0, self._append_terminal_text, f"❗ Exited with code {proc.returncode}\n")
        except Exception as e:
            self.after(0, self._append_terminal_text, f"❌ {e}\n")

    def _append_terminal_text(self, text):
        self.terminal_text.insert("end", text)
        self.terminal_text.see("end")

    def format_code(self):
        file_path = self.get_active_file_path()
        if not file_path:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_SAVE_FIRST'])
            return
        self.save_file()
        self.start_progress(T['BTN_FORMAT'])
        threading.Thread(target=self._format_thread, args=(file_path,), daemon=True).start()

    def _format_thread(self, file_path):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=False, capture_output=True)
            result = subprocess.run([sys.executable, "-m", "black", file_path], capture_output=True, text=True)
            if result.returncode == 0:
                with open(file_path, "r", encoding="utf-8") as f:
                    new_content = f.read()
                self.after(0, lambda: self._apply_formatted_code(new_content))
                self.after(0, lambda: self.log(T['LOG_FORMAT_SUCCESS']))
                self.after(0, lambda: self.stop_progress(True))
            else:
                self.after(0, lambda: self.log(T['LOG_FORMAT_FAIL'].format(error=result.stderr)))
                self.after(0, lambda: self.stop_progress(False))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_FORMAT_FAIL'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))

    def _apply_formatted_code(self, new_content):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", new_content)

    def lint_code(self):
        file_path = self.get_active_file_path()
        if not file_path:
            return
        self.save_file()
        self.start_progress(T['BTN_LINT'])
        threading.Thread(target=self._lint_thread, args=(file_path,), daemon=True).start()

    def _lint_thread(self, file_path):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "flake8"], check=False, capture_output=True)
            result = subprocess.run([sys.executable, "-m", "flake8", file_path], capture_output=True, text=True)
            output = result.stdout.strip()
            self.after(0, lambda: self._show_lint_result(output))
            self.after(0, lambda: self.stop_progress(True))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_LINT_RESULT'].format(output=str(e))))
            self.after(0, lambda: self.stop_progress(False))

    def _show_lint_result(self, output):
        if output:
            self.log(T['LOG_LINT_RESULT'].format(output=output))
        else:
            self.log(T['LOG_LINT_CLEAN'])

    def generate_requirements(self):
        self.start_progress(T['BTN_REQUIREMENTS'])
        threading.Thread(target=self._requirements_thread, daemon=True).start()

    def _requirements_thread(self):
        try:
            code = self.editor.get("1.0", "end-1c")
            if not code.strip():
                self.after(0, lambda: self.log(T['LOG_EDITOR_EMPTY']))
                self.after(0, lambda: self.stop_progress(False))
                return

            tree = ast.parse(code)
            libs_set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        libs_set.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        libs_set.add(node.module.split('.')[0])

            builtin_modules = set(sys.builtin_module_names)
            std_libs = {
                'sys', 'os', 're', 'math', 'json', 'csv', 'datetime', 'collections',
                'itertools', 'functools', 'typing', 'argparse', 'logging', 'subprocess',
                'shutil', 'pathlib', 'time', 'random', 'string', 'socket', 'hashlib',
                'base64', 'threading', 'multiprocessing', 'pickle', 'sqlite3', 'xml',
                'html', 'urllib', 'http', 'email', 'tempfile', 'stat', 'io', 'textwrap',
                'pprint', 'inspect', 'pdb', 'unittest', 'doctest', 'dataclasses', 'enum',
                'warnings', 'contextlib', 'abc', 'weakref', 'copy', 'struct', 'array',
                'bisect', 'heapq', 'decimal', 'fractions', 'calendar', 'locale',
                'gettext', 'importlib', 'pkgutil', 'traceback', 'linecache', 'tkinter',
                'cProfile', 'pstats', 'zipfile', 'tarfile', 'configparser', 'xmlrpc'
            }
            std_libs.update(builtin_modules)

            external_libs = [lib for lib in libs_set if lib not in std_libs and not lib.startswith('_')]

            if not external_libs:
                self.after(0, lambda: self.log(T['LOG_NO_EXTERNAL']))
                self.after(0, lambda: messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_NO_EXTERNAL_LIBS']))
                self.after(0, lambda: self.stop_progress(False))
                return

            self.after(0, lambda: self._save_requirements(external_libs))
        except Exception as e:
            self.after(0, lambda: self.log(T['LOG_ANALYSIS_ERROR'].format(error=e)))
            self.after(0, lambda: self.stop_progress(False))

    def _save_requirements(self, libs):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                for lib in sorted(libs):
                    f.write(lib + "\n")
            self.log(T['LOG_REQ_GEN_SUCCESS'].format(path=file_path))
            self.stop_progress(True)
        else:
            self.stop_progress(False)

    def show_autocomplete(self, event=None):
        try:
            import jedi
        except ImportError:
            self.log("⚠️ Please install jedi: pip install jedi")
            return

        cursor = self.editor.index("insert")
        line = self.editor.get(cursor + " linestart", cursor)
        import re
        match = re.search(r'([a-zA-Z0-9_.]+)$', line)
        if not match:
            return
        word = match.group(1)
        self.current_word = word
        if not word:
            return

        try:
            script = jedi.Script(self.editor.get("1.0", "end-1c"), path=self.get_active_file_path() or "")
            completions = script.complete(line, len(word))
            suggestions = [c.name for c in completions if c.name.startswith(word)]
            if not suggestions:
                return
            suggestions = list(dict.fromkeys(suggestions))
        except Exception as e:
            self.log(f"❌ Autocomplete error: {e}")
            return

        self.hide_autocomplete()
        self.autocomplete_window = Toplevel(self)
        self.autocomplete_window.wm_overrideredirect(True)
        self.autocomplete_window.config(bg="#2a2a4a")
        listbox = Listbox(self.autocomplete_window, bg="#1e1e2e", fg="#eeeeee",
                          font=("Arial", 11), borderwidth=0, highlightthickness=0,
                          selectbackground="#4a4a8a")
        listbox.pack(fill="both", expand=True)
        for item in suggestions:
            listbox.insert("end", item)
        listbox.bind("<Double-Button-1>", self.on_autocomplete_select)
        listbox.bind("<Return>", self.on_autocomplete_select)
        listbox.bind("<Escape>", lambda e: self.hide_autocomplete())
        listbox.bind("<Key-Up>", lambda e: self.navigate_autocomplete(-1))
        listbox.bind("<Key-Down>", lambda e: self.navigate_autocomplete(1))
        if suggestions:
            listbox.selection_set(0)
        self.autocomplete_listbox = listbox

        x, y = self.editor.bbox(self.editor.index("insert"))[:2]
        x += self.editor.winfo_rootx()
        y += self.editor.winfo_rooty() + 20
        self.autocomplete_window.geometry(f"300x200+{x}+{y}")
        self.autocomplete_window.deiconify()
        self.autocomplete_active = True

    def hide_autocomplete(self, event=None):
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
            self.autocomplete_listbox = None
            self.autocomplete_active = False

    def navigate_autocomplete(self, direction):
        if self.autocomplete_listbox:
            cur = self.autocomplete_listbox.curselection()
            if cur:
                idx = cur[0]
            else:
                idx = -1
            new_idx = idx + direction
            if 0 <= new_idx < self.autocomplete_listbox.size():
                self.autocomplete_listbox.selection_clear(0, "end")
                self.autocomplete_listbox.selection_set(new_idx)
                self.autocomplete_listbox.see(new_idx)

    def on_autocomplete_select(self, event=None):
        if self.autocomplete_listbox:
            selection = self.autocomplete_listbox.curselection()
            if selection:
                word = self.autocomplete_listbox.get(selection[0])
                cursor = self.editor.index("insert")
                line_start = cursor + " linestart"
                line = self.editor.get(line_start, cursor)
                import re
                match = re.search(r'([a-zA-Z0-9_.]+)$', line)
                if match:
                    start = cursor + f"-{len(match.group(1))}c"
                    self.editor.delete(start, cursor)
                    self.editor.insert(start, word)
        self.hide_autocomplete()

    def ensure_pyarmor_installed(self):
        try:
            import pyarmor
            return True
        except ImportError:
            self.log(T['LOG_PYARMOR_INSTALLING'])
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "pyarmor"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1
                )
                for line in proc.stdout:
                    self.log(f"  {line.strip()}")
                proc.wait()
                if proc.returncode == 0:
                    self.log(T['LOG_PYARMOR_SUCCESS'])
                    return True
                else:
                    self.log(T['LOG_PYARMOR_FAIL'])
                    return False
            except Exception as e:
                self.log(T['LOG_PYARMOR_FAIL'])
                return False

    def build_exe(self):
        if self.active_tab_id is None:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_NO_FILE_RUN'])
            return

        file_path = self.get_active_file_path()
        if not file_path:
            messagebox.showinfo(T['DIALOG_INFO'], T['DIALOG_SAVE_FIRST'])
            return

        data = self.open_files[self.active_tab_id]
        if data['modified']:
            answer = messagebox.askyesnocancel(T['DIALOG_WARNING'], T['DIALOG_UNSAVED_BUILD'])
            if answer is None:
                return
            elif answer:
                self.save_file()
                if not self.get_active_file_path():
                    return

        if not self.check_lib_installed("PyInstaller"):
            self.log("⚠️ PyInstaller not found. Installing...")
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1
                )
                for line in proc.stdout:
                    self.log(f"  {line.strip()}")
                proc.wait()
                if proc.returncode != 0:
                    self.log("❌ Failed to install PyInstaller.")
                    messagebox.showerror(T['DIALOG_ERROR'], T['DIALOG_INSTALL_ERROR'].format(error="Check console."))
                    return
                self.log("✅ PyInstaller installed.")
            except Exception as e:
                self.log(f"❌ Failed to install PyInstaller: {e}")
                messagebox.showerror(T['DIALOG_ERROR'], T['DIALOG_INSTALL_ERROR'].format(error=e))
                return

        source_file = file_path
        use_pyarmor = self.pyarmor_var.get()
        temp_encrypt_dir = None
        encryption_success = False

        if use_pyarmor:
            if not self.ensure_pyarmor_installed():
                messagebox.showerror(T['DIALOG_ERROR'], "PyArmor installation failed.")
                return

            temp_encrypt_dir = os.path.join(os.path.dirname(file_path), "temp_pyarmor")
            if os.path.exists(temp_encrypt_dir):
                shutil.rmtree(temp_encrypt_dir, ignore_errors=True)
            os.makedirs(temp_encrypt_dir)

            self.log(T['LOG_ENCRYPTING'])

            python_exe = sys.executable
            commands = [
                [python_exe, "-m", "pyarmor", "gen", "-O", temp_encrypt_dir, file_path],
                [python_exe, "-m", "pyarmor", "obfuscate", "--output", temp_encrypt_dir, file_path],
                [python_exe, "-m", "pyarmor", "gen", file_path],
                [python_exe, "-m", "pyarmor", "obfuscate", file_path],
                ["pyarmor", "gen", "-O", temp_encrypt_dir, file_path],
                ["pyarmor", "obfuscate", "--output", temp_encrypt_dir, file_path],
                ["pyarmor", "gen", file_path],
                ["pyarmor", "obfuscate", file_path],
            ]

            for cmd in commands:
                self.log(T['LOG_TRYING_CMD'].format(cmd=' '.join(cmd)))
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        cwd=os.path.dirname(file_path)
                    )
                    for line in proc.stdout:
                        self.log(f"  {line.strip()}")
                    proc.wait()
                    if proc.returncode == 0:
                        self.log(T['LOG_ENCRYPT_SUCCESS'])
                        encryption_success = True
                        break
                    else:
                        self.log(T['LOG_ENCRYPT_FAIL'].format(code=proc.returncode))
                except Exception as e:
                    self.log(T['LOG_ENCRYPT_EXCEPTION'].format(error=e))

            if not encryption_success:
                self.log(T['LOG_ENCRYPT_ALL_FAIL'])
                manual_cmd = f'"{python_exe}" -m pyarmor gen -O "{temp_encrypt_dir}" "{file_path}"'
                self.log(T['LOG_MANUAL_CMD'].format(cmd=manual_cmd))
                if messagebox.askyesno(T['DIALOG_ERROR'], T['DIALOG_PYARMOR_FAILED'].format(cmd=manual_cmd)):
                    encrypted_file = filedialog.askopenfilename(
                        title="Select encrypted file",
                        filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
                    )
                    if encrypted_file:
                        source_file = encrypted_file
                        self.log(T['LOG_ENCRYPTED_FILE_SELECTED'].format(path=source_file))
                        if os.path.exists(temp_encrypt_dir):
                            shutil.rmtree(temp_encrypt_dir, ignore_errors=True)
                    else:
                        if messagebox.askyesno(T['DIALOG_WARNING'], T['DIALOG_SELECT_ENCRYPTED']):
                            use_pyarmor = False
                            source_file = file_path
                        else:
                            return
                else:
                    if messagebox.askyesno(T['DIALOG_WARNING'], T['DIALOG_NO_ENCRYPTED_CONTINUE']):
                        use_pyarmor = False
                        source_file = file_path
                    else:
                        return
            else:
                encrypted_file = None
                base_name = os.path.basename(file_path)
                if temp_encrypt_dir and os.path.exists(temp_encrypt_dir):
                    for root, dirs, files in os.walk(temp_encrypt_dir):
                        for f in files:
                            if f == base_name and f.endswith('.py'):
                                encrypted_file = os.path.join(root, f)
                                break
                        if encrypted_file:
                            break
                if not encrypted_file:
                    possible = os.path.join(os.path.dirname(file_path), base_name)
                    if os.path.exists(possible) and os.path.getmtime(possible) > os.path.getmtime(file_path):
                        encrypted_file = possible
                if encrypted_file:
                    source_file = encrypted_file
                    self.log(f"🔐 Encrypted file: {source_file}")
                else:
                    self.log("⚠️ Encrypted file not found, using original.")
                    source_file = file_path

        cmd = [sys.executable, "-m", "PyInstaller"]
        if self.onefile_var.get():
            cmd.append("--onefile")
        if self.noconsole_var.get():
            cmd.append("--noconsole")
        if self.windowed_var.get():
            cmd.append("--windowed")

        name = self.output_name_entry.get().strip()
        if name:
            cmd.extend(["--name", name])

        icon = self.icon_path_var.get().strip()
        if icon and os.path.exists(icon):
            cmd.extend(["--icon", icon])

        cmd.append(source_file)

        self.log(T['LOG_BUILD_CMD'].format(cmd=' '.join(cmd)))
        self.start_progress(T['BTN_BUILD'])

        build_cwd = os.path.dirname(source_file) if os.path.dirname(source_file) else "."

        def build_thread():
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1,
                    cwd=build_cwd
                )
                for line in proc.stdout:
                    self.log(f"  {line.strip()}")
                proc.wait()
                if proc.returncode == 0:
                    self.log(T['LOG_BUILD_SUCCESS'])
                    self.after(0, lambda: self.stop_progress(True))
                    self.after(0, lambda: messagebox.showinfo(T['DIALOG_INFO'], "File created in 'dist' folder."))
                else:
                    self.log(T['LOG_BUILD_FAIL'].format(code=proc.returncode))
                    self.after(0, lambda: self.stop_progress(False))
            except Exception as e:
                self.log(T['LOG_BUILD_EXCEPTION'].format(error=e))
                self.after(0, lambda: self.stop_progress(False))
            finally:
                if use_pyarmor and temp_encrypt_dir and os.path.exists(temp_encrypt_dir):
                    try:
                        shutil.rmtree(temp_encrypt_dir, ignore_errors=True)
                        self.log(T['LOG_PYARMOR_TEMP_CLEAN'])
                    except:
                        pass

        threading.Thread(target=build_thread, daemon=True).start()

    def extract_pyc_from_exe(self):
        file_path = filedialog.askopenfilename(
            title="Select EXE (PyInstaller)",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        self.log(T['LOG_EXTRACT_SELECTED'].format(path=file_path))
        self.start_progress(T['BTN_EXTRACT_PYC'])
        threading.Thread(target=self._extract_thread, args=(file_path,), daemon=True).start()

    def _extract_thread(self, file_path):
        base_dir = os.path.dirname(file_path)
        exe_name = os.path.basename(file_path).replace('.exe', '')

        work_dir = os.path.join(base_dir, f"temp_extract_{int(time.time())}")
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        os.makedirs(work_dir)

        try:
            self.log(T['LOG_EXTRACT_START'])
            arch = PyInstArchive(file_path, logger=self.log)
            if not arch.open():
                raise Exception("Failed to open file")
            if not arch.checkFile():
                raise Exception("Not a valid PyInstaller archive")
            if not arch.getCArchiveInfo():
                raise Exception("Failed to read archive info")
            arch.parseTOC()
            extracted_path = arch.extractFiles(work_dir)
            arch.close()
            self.log(T['LOG_EXTRACT_SUCCESS'])

            self.log(T['LOG_EXTRACT_CLEANING'])
            main_pyc = self._cleanup_extracted_folder(extracted_path)
            if not main_pyc:
                raise Exception("No main .pyc file found")

            self.log(T['LOG_EXTRACT_MAIN'].format(path=main_pyc))

            dest_pyc = os.path.join(base_dir, exe_name + '.pyc')
            if os.path.exists(dest_pyc):
                base, ext = os.path.splitext(dest_pyc)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dest_pyc = f"{base}_{counter}{ext}"
            shutil.copy2(main_pyc, dest_pyc)
            self.log(T['LOG_EXTRACT_COPIED'].format(path=dest_pyc))

            self._force_remove_dir(work_dir)
            self.log(T['LOG_EXTRACT_DELETED'])

            self.after(0, lambda: self._show_pyc_ready(dest_pyc))
            self.after(0, lambda: self.stop_progress(True))

        except Exception as e:
            self.log(T['LOG_EXTRACT_FAIL'].format(error=e))
            self.after(0, lambda: self.stop_progress(False))
            self.after(0, lambda: messagebox.showerror(T['DIALOG_ERROR'], str(e)))

    def _cleanup_extracted_folder(self, extracted_path):
        prefixes_to_delete = ('pyi', 'pyimod', 'pyiboot')
        valid_pyc = []
        for root, dirs, files in os.walk(extracted_path):
            for f in files:
                if f.endswith('.pyc'):
                    full_path = os.path.join(root, f)
                    name = os.path.basename(f)
                    if not name.startswith(prefixes_to_delete):
                        valid_pyc.append(full_path)

        if not valid_pyc:
            all_pyc = []
            for root, dirs, files in os.walk(extracted_path):
                for f in files:
                    if f.endswith('.pyc'):
                        all_pyc.append(os.path.join(root, f))
            if all_pyc:
                valid_pyc = [max(all_pyc, key=os.path.getsize)]
            else:
                return None

        main_pyc = max(valid_pyc, key=os.path.getsize) if len(valid_pyc) > 1 else valid_pyc[0]

        for root, dirs, files in os.walk(extracted_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                if file_path != main_pyc:
                    try:
                        os.remove(file_path)
                    except:
                        pass
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                except OSError:
                    pass

        if os.path.dirname(main_pyc) != extracted_path:
            new_path = os.path.join(extracted_path, os.path.basename(main_pyc))
            shutil.move(main_pyc, new_path)
            main_pyc = new_path

        for item in os.listdir(extracted_path):
            item_path = os.path.join(extracted_path, item)
            if os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)
                except:
                    pass

        return main_pyc

    def _force_remove_dir(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    os.chmod(file_path, 0o777)
                    os.remove(file_path)
                except:
                    pass
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.chmod(dir_path, 0o777)
                    os.rmdir(dir_path)
                except:
                    pass
        try:
            os.chmod(path, 0o777)
            shutil.rmtree(path)
        except:
            pass

    def _show_pyc_ready(self, pyc_path):
        result = messagebox.askyesno(T['EXTRACT_TITLE_DONE'], T['EXTRACT_ASK'].format(path=pyc_path))
        if result:
            webbrowser.open("https://pylingual.io/")

    def start_progress(self, text="⏳ Working..."):
        self.progress_running = True
        self.progress_label.configure(text=text)
        self._animate_progress(0)

    def _animate_progress(self, step):
        if not self.progress_running:
            return
        import math
        value = (math.sin(step) + 1) / 2
        self.progress_bar.set(value)
        self.after(50, lambda: self._animate_progress(step + 0.1))

    def stop_progress(self, success=True):
        self.progress_running = False
        if success:
            self.progress_bar.set(1)
            self.progress_label.configure(text="✅ Done")
        else:
            self.progress_bar.set(0)
            self.progress_label.configure(text="❌ Failed")
        self.after(3000, lambda: self.progress_bar.set(0))
        self.after(3000, lambda: self.progress_label.configure(text=T['PROGRESS_WAITING']))

    def select_icon(self):
        icon_path = filedialog.askopenfilename(
            title="Select .ico icon",
            filetypes=[("Icon Files", "*.ico")]
        )
        if icon_path:
            self.icon_path_var.set(icon_path)
            self.log(T['ICON_SELECTED'].format(path=icon_path))

    def log(self, message):
        self.after(0, self._log_impl, message)

    def _log_impl(self, message):
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{time_str}] {message}\n")
        self.log_text.see("end")

if __name__ == "__main__":
    app = PyManagerPro()
    app.mainloop()
