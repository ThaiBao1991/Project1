#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
sync_skills_rules.py - Công Cụ Quản Lý & Đồng Bộ Kỹ Năng / Quy Chuẩn Toàn Cục
Kho trung tâm: GravityCode/SKILL_RULE
Đích đồng bộ:
  1. C:\Users\<User>\.gemini\config\ (Global User Configuration)
  2. GravityCode\.agents\ (Local Workspace Configuration)
"""

import os
import sys
import shutil
import argparse

# Thiết lập UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAVITY_CODE_DIR = os.path.dirname(CURRENT_DIR)
USER_HOME = os.path.expanduser("~")
GEMINI_CONFIG_DIR = os.path.join(USER_HOME, ".gemini", "config")
WORKSPACE_AGENTS_DIR = os.path.join(GRAVITY_CODE_DIR, ".agents")

SOURCE_SKILLS = os.path.join(CURRENT_DIR, "skills")
SOURCE_RULES = os.path.join(CURRENT_DIR, "rules")

GEMINI_SKILLS = os.path.join(GEMINI_CONFIG_DIR, "skills")
GEMINI_RULES = os.path.join(GEMINI_CONFIG_DIR, "rules")

WORKSPACE_SKILLS = os.path.join(WORKSPACE_AGENTS_DIR, "skills")
WORKSPACE_RULES = os.path.join(WORKSPACE_AGENTS_DIR, "rules")


def clean_nested_skills():
    """Dọn dẹp thư mục lồng nhau lỗi .agents/skills/skills nếu có."""
    nested_dir = os.path.join(WORKSPACE_SKILLS, "skills")
    if os.path.exists(nested_dir) and os.path.isdir(nested_dir):
        print(f"🧹 Dọn dẹp thư mục lồng nhau lỗi: {nested_dir}")
        shutil.rmtree(nested_dir, ignore_errors=True)
    
    nested_rules = os.path.join(WORKSPACE_RULES, "rules")
    if os.path.exists(nested_rules) and os.path.isdir(nested_rules):
        print(f"🧹 Dọn dẹp thư mục rules lồng nhau lỗi: {nested_rules}")
        shutil.rmtree(nested_rules, ignore_errors=True)


def push_to_destination(dest_name, target_skills, target_rules):
    """Sao chép toàn bộ kỹ năng và quy tắc từ SKILL_RULE tới đích chỉ định."""
    print(f"\n🚀 Đang đồng bộ tới: {dest_name}")
    os.makedirs(target_skills, exist_ok=True)
    os.makedirs(target_rules, exist_ok=True)

    # 1. Đồng bộ Skills
    skill_count = 0
    if os.path.exists(SOURCE_SKILLS):
        for item in os.listdir(SOURCE_SKILLS):
            src_item = os.path.join(SOURCE_SKILLS, item)
            dst_item = os.path.join(target_skills, item)
            if os.path.isdir(src_item):
                if os.path.exists(dst_item):
                    shutil.rmtree(dst_item)
                shutil.copytree(src_item, dst_item)
                skill_count += 1
            elif os.path.isfile(src_item):
                shutil.copy2(src_item, dst_item)
                skill_count += 1
    print(f"   ✅ Đã cập nhật {skill_count} kỹ năng vào {target_skills}")

    # 2. Đồng bộ Rules
    rule_count = 0
    if os.path.exists(SOURCE_RULES):
        for item in os.listdir(SOURCE_RULES):
            src_item = os.path.join(SOURCE_RULES, item)
            dst_item = os.path.join(target_rules, item)
            if os.path.isfile(src_item):
                shutil.copy2(src_item, dst_item)
                rule_count += 1
            elif os.path.isdir(src_item):
                if os.path.exists(dst_item):
                    shutil.rmtree(dst_item)
                shutil.copytree(src_item, dst_item)
                rule_count += 1
    print(f"   ✅ Đã cập nhật {rule_count} quy tắc vào {target_rules}")


def harvest_from_projects():
    """Quét toàn bộ dự án con trong GravityCode để tìm skill hoặc rule chưa có trong SKILL_RULE."""
    print("\n🔍 Đang rà soát (harvest) các kỹ năng/quy tắc mới từ các dự án con...")
    harvested_skills = 0
    harvested_rules = 0

    for root, dirs, files in os.walk(GRAVITY_CODE_DIR):
        # Bỏ qua chính SKILL_RULE và .git
        if "SKILL_RULE" in root or ".git" in root or "node_modules" in root or "__pycache__" in root:
            continue

        # Tìm SKILL.md
        if "SKILL.md" in files:
            skill_folder_name = os.path.basename(root)
            target_folder = os.path.join(SOURCE_SKILLS, skill_folder_name)
            if not os.path.exists(target_folder):
                print(f"   ✨ Phát hiện kỹ năng mới: {skill_folder_name} tại {os.path.relpath(root, GRAVITY_CODE_DIR)}")
                shutil.copytree(root, target_folder)
                harvested_skills += 1

        # Tìm các file rule *.md
        for f in files:
            if ("rule" in f.lower() or f.endswith("_standards.md")) and f.endswith(".md"):
                if f in ["AGENTS.md", "GEMINI.md", "README.md", "ProjectLog.md", "projectLog.md"]:
                    continue
                target_file = os.path.join(SOURCE_RULES, f)
                if not os.path.exists(target_file):
                    src_file = os.path.join(root, f)
                    print(f"   ✨ Phát hiện quy tắc mới: {f} tại {os.path.relpath(src_file, GRAVITY_CODE_DIR)}")
                    shutil.copy2(src_file, target_file)
                    harvested_rules += 1

    if harvested_skills == 0 and harvested_rules == 0:
        print("   👍 Không có kỹ năng hay quy tắc nào bị bỏ sót trong các dự án con.")
    else:
        print(f"   🎉 Đã thu hoạch thành công: {harvested_skills} kỹ năng, {harvested_rules} quy tắc vào SKILL_RULE.")


def check_status():
    """Kiểm tra và báo cáo tổng quan tình trạng đồng bộ."""
    print("=" * 60)
    print("📋 BÁO CÁO TÌNH TRẠNG KỸ NĂNG & QUY TẮC")
    print("=" * 60)

    skills_source = sorted(os.listdir(SOURCE_SKILLS)) if os.path.exists(SOURCE_SKILLS) else []
    rules_source = sorted(os.listdir(SOURCE_RULES)) if os.path.exists(SOURCE_RULES) else []

    skills_gemini = sorted(os.listdir(GEMINI_SKILLS)) if os.path.exists(GEMINI_SKILLS) else []
    rules_gemini = sorted(os.listdir(GEMINI_RULES)) if os.path.exists(GEMINI_RULES) else []

    skills_workspace = sorted(os.listdir(WORKSPACE_SKILLS)) if os.path.exists(WORKSPACE_SKILLS) else []
    rules_workspace = sorted(os.listdir(WORKSPACE_RULES)) if os.path.exists(WORKSPACE_RULES) else []

    # Loại bỏ thư mục con rác khi đếm
    skills_workspace = [s for s in skills_workspace if s != "skills"]
    rules_workspace = [r for r in rules_workspace if r != "rules"]

    print(f"1. Kho Gốc (SKILL_RULE)         : {len(skills_source)} Skills | {len(rules_source)} Rules")
    print(f"2. Toàn Cục (.gemini/config)    : {len(skills_gemini)} Skills | {len(rules_gemini)} Rules")
    print(f"3. Workspace (GravityCode/.agents): {len(skills_workspace)} Skills | {len(rules_workspace)} Rules")

    print("\nChi tiết danh mục tại SKILL_RULE:")
    print("  --- SKILLS ---")
    for s in skills_source:
        status_gemini = "✓" if s in skills_gemini else "✗ (.gemini thiếu)"
        status_ws = "✓" if s in skills_workspace else "✗ (workspace thiếu)"
        print(f"    * {s:<30} [Global: {status_gemini}] [WS: {status_ws}]")

    print("  --- RULES ---")
    for r in rules_source:
        status_gemini = "✓" if r in rules_gemini else "✗ (.gemini thiếu)"
        status_ws = "✓" if r in rules_workspace else "✗ (workspace thiếu)"
        print(f"    * {r:<30} [Global: {status_gemini}] [WS: {status_ws}]")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Công cụ đồng bộ Skill & Rule toàn cục cho Antigravity")
    parser.add_argument("--push-all", action="store_true", help="Đẩy tất cả từ SKILL_RULE ra .gemini/config và .agents")
    parser.add_argument("--harvest", action="store_true", help="Quét thu hoạch kỹ năng mới từ mọi subproject")
    parser.add_argument("--check", action="store_true", help="Kiểm tra trạng thái đồng bộ hiện tại")

    args = parser.parse_args()

    if args.harvest:
        harvest_from_projects()

    if args.push_all:
        clean_nested_skills()
        push_to_destination("Toàn Cục (~/.gemini/config)", GEMINI_SKILLS, GEMINI_RULES)
        push_to_destination("Workspace Cục Bộ (.agents)", WORKSPACE_SKILLS, WORKSPACE_RULES)
        clean_nested_skills()
        print("\n✨ ĐỒNG BỘ HOÀN TẤT THÀNH CÔNG 100%! ✨\n")

    # Luôn hiển thị trạng thái
    check_status()


if __name__ == "__main__":
    main()
