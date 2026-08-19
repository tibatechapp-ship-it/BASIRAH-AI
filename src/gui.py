"""BASIRAH AI - professional web-based GUI using Streamlit."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.organizer import find_duplicates, organize_library

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def _count_supported_files(folder: Path) -> int:
    return sum(1 for entry in folder.rglob("*") if _is_supported_file(entry))


def main() -> None:
    """Run the BASIRAH AI web GUI."""
    st.set_page_config(
        page_title="بصيرة - BASIRAH AI",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        body { direction: rtl; }
        .stApp { direction: rtl; text-align: right; }
        h1, h2, h3, h4, h5, h6, p, div, label, span { direction: rtl; text-align: right; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📚 بصيرة - BASIRAH AI")
    st.markdown("**منصة ذكية لتنظيم وتصنيف المكتبات الرقمية والبحوث العلمية**")
    st.divider()

    mode = st.sidebar.radio(
        "اختر الوضع",
        options=["تنظيم المكتبة", "اكتشاف التكرار"],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**الملفات المدعومة:** PDF، TXT، DOCX")

    if mode == "تنظيم المكتبة":
        _render_organize_tab()
    else:
        _render_duplicates_tab()


def _render_organize_tab() -> None:
    st.header("تنظيم المكتبة")
    st.info("ارفع مجلد المكتبة مضغوطاً بصيغة ZIP، وسيتم تصنيف الملفات تلقائياً.")

    uploaded_zip = st.file_uploader("اختر ملف ZIP", type=["zip"])
    recursive = st.checkbox("مسح المجلدات الفرعية", value=True)

    if uploaded_zip is None:
        return

    if not st.button("ابدأ التنظيم", type="primary"):
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "library.zip"
        zip_path.write_bytes(uploaded_zip.getvalue())

        import zipfile

        extract_dir = temp_path / "library"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        supported_count = _count_supported_files(extract_dir)
        if supported_count == 0:
            st.warning("لم يتم العثور على ملفات PDF/TXT/DOCX داخل الأرشيف.")
            return

        progress_bar = st.progress(0, text="جاري قراءة الملفات...")

        total, classified = organize_library(str(extract_dir), recursive=recursive)

        progress_bar.progress(100, text="اكتمل التنظيم!")

        st.success(f"تمت معالجة {total} ملف(ات)، وتم تصنيف {classified} منها.")

        st.subheader("📁 هيكل المكتبة بعد التنظيم")
        for category_folder in sorted(extract_dir.iterdir()):
            if not category_folder.is_dir():
                continue
            files = [entry.name for entry in category_folder.iterdir() if entry.is_file()]
            if not files:
                continue
            with st.expander(f"📂 {category_folder.name} ({len(files)} ملف)"):
                for file_name in files:
                    st.write(f"- {file_name}")

        output_zip_path = temp_path / "organized_library.zip"
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in extract_dir.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(extract_dir))

        st.download_button(
            label="⬇️ تحميل المكتبة المنظمة (ZIP)",
            data=output_zip_path.read_bytes(),
            file_name="organized_library.zip",
            mime="application/zip",
        )


def _render_duplicates_tab() -> None:
    st.header("اكتشاف الملفات المكررة")
    st.info("ارفع مجلد المكتبة مضغوطاً بصيغة ZIP للعثور على الملفات المتطابقة.")

    uploaded_zip = st.file_uploader("اختر ملف ZIP", type=["zip"], key="dup_zip")

    if uploaded_zip is None:
        return

    if not st.button("ابدأ الفحص", type="primary", key="dup_button"):
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "library.zip"
        zip_path.write_bytes(uploaded_zip.getvalue())

        import zipfile

        extract_dir = temp_path / "library"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        duplicates = find_duplicates(str(extract_dir))

        if not duplicates:
            st.success("لم يتم العثور على ملفات مكررة.")
            return

        st.warning(f"تم العثور على {len(duplicates)} مجموعة(ات) مكررة.")
        for hash_value, paths in duplicates.items():
            with st.expander(f"🔁 مجموعة مكررة ({len(paths)} ملف)"):
                for path in paths:
                    st.write(f"- `{path}`")


if __name__ == "__main__":
    main()
