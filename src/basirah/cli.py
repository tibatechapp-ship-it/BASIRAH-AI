#!/usr/bin/env python3
"""نقطة الدخول الرئيسية لبرنامج BASIRAH AI."""

from basirah.organizer import organize_library


def main() -> None:
    """تشغيل برنامج تنظيم المكتبة."""
    print("\nBASIRAH AI v0.1\n")
    library = input("أدخل مسار المكتبة: ").strip()
    total, classified = organize_library(library)
    print("\n" + "=" * 40)
    print("انتهى التصنيف")
    print("=" * 40)
    print(f"عدد الملفات: {total}")
    print(f"عدد الملفات المصنفة: {classified}")


if __name__ == "__main__":
    main()
