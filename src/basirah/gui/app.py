"""واجهة رسومية بسيطة لـ BASIRAH-AI باستخدام Tkinter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional
import threading

from basirah.organizer import organize_library
from basirah.reports.generator import ReportGenerator, FileStats
from basirah.models.categories import CategoryType


class BasirahGUI:
    """واجهة رسومية لبرنامج BASIRAH-AI."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BASIRAH-AI - منظم المكتبات الإسلامية")
        self.root.geometry("900x700")
        
        self.report_generator = ReportGenerator()
        self.is_processing = False
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """إعداد واجهة المستخدم."""
        # الإطار العلوي - اختيار المجلد
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="مسار المكتبة:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_var, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="تصفح...", command=self._browse_folder).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="تنظيم", command=self._start_organize).pack(side=tk.LEFT, padx=5)
        
        # شريط التقدم
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill=tk.X)
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="جاهز")
        ttk.Label(progress_frame, textvariable=self.status_var).pack()
        
        # منطقة عرض النتائج
        results_frame = ttk.LabelFrame(self.root, text="النتائج", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Courier New", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # أزرار التصدير
        export_frame = ttk.Frame(self.root, padding="10")
        export_frame.pack(fill=tk.X)
        
        ttk.Button(export_frame, text="تصدير JSON", command=self._export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="تصدير نصي", command=self._export_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="مسح النتائج", command=self._clear_results).pack(side=tk.RIGHT, padx=5)

    def _browse_folder(self) -> None:
        """تصفح واختيار مجلد."""
        folder = filedialog.askdirectory(title="اختر مجلد المكتبة")
        if folder:
            self.path_var.set(folder)

    def _start_organize(self) -> None:
        """بدء عملية التنظيم في خيط منفصل."""
        library_path = self.path_var.get().strip()
        
        if not library_path:
            messagebox.showerror("خطأ", "يرجى اختيار مسار المكتبة")
            return
        
        if not Path(library_path).exists():
            messagebox.showerror("خطأ", "المسار غير موجود")
            return
        
        if self.is_processing:
            messagebox.showwarning("تحذير", "جاري معالجة طلب سابق")
            return
        
        self.is_processing = True
        self.progress.start()
        self.status_var.set("جاري المعالجة...")
        self.results_text.delete(1.0, tk.END)
        
        # تشغيل في خيط منفصل لعدم تجميد الواجهة
        thread = threading.Thread(target=self._organize_thread, args=(library_path,))
        thread.daemon = True
        thread.start()

    def _organize_thread(self, library_path: str) -> None:
        """خيط المعالجة."""
        try:
            self.report_generator.start_processing()
            
            total, classified = organize_library(library_path, self.report_generator)
            
            self.report_generator.end_processing()
            
            # تحديث الواجهة في الخيط الرئيسي
            self.root.after(0, self._update_results, total, classified)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.root.after(0, self._processing_complete)

    def _update_results(self, total: int, classified: int) -> None:
        """تحديث عرض النتائج."""
        self.results_text.insert(tk.END, f"✅ اكتملت العملية بنجاح!\n\n")
        self.results_text.insert(tk.END, f"📊 الإحصائيات:\n")
        self.results_text.insert(tk.END, f"   إجمالي الملفات: {total}\n")
        self.results_text.insert(tk.END, f"   الملفات المصنفة: {classified}\n")
        self.results_text.insert(tk.END, f"   نسبة التصنيف: {classified/max(total, 1)*100:.1f}%\n\n")
        
        self.report_generator.print_summary()
        self.results_text.insert(tk.END, "=" * 60 + "\n")

    def _processing_complete(self) -> None:
        """اكتمال المعالجة."""
        self.is_processing = False
        self.progress.stop()
        self.status_var.set("اكتملت العملية")

    def _export_json(self) -> None:
        """تصدير التقرير كـ JSON."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="حفظ تقرير JSON"
        )
        
        if file_path:
            if self.report_generator.save_report_json(file_path):
                messagebox.showinfo("نجاح", f"تم حفظ التقرير في: {file_path}")
            else:
                messagebox.showerror("خطأ", "فشل حفظ التقرير")

    def _export_text(self) -> None:
        """تصدير التقرير كنص."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="حفظ تقرير نصي"
        )
        
        if file_path:
            if self.report_generator.save_report_text(file_path):
                messagebox.showinfo("نجاح", f"تم حفظ التقرير في: {file_path}")
            else:
                messagebox.showerror("خطأ", "فشل حفظ التقرير")

    def _clear_results(self) -> None:
        """مسح النتائج."""
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("جاهز")


def run_gui() -> None:
    """تشغيل الواجهة الرسومية."""
    root = tk.Tk()
    
    # إعداد الخطوط العربية
    try:
        root.option_add("*Font", "Arial 10")
    except:
        pass
    
    app = BasirahGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
