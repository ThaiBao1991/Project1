#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
sync_skills_rules.py - Công Cụ Quản Lý & Đồng Bộ Kỹ Năng / Quy Chuẩn 2 Chiều Toàn Cục
Hệ thống Hub kép:
  1. Project 1 Hub: C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\SKILL_RULE
  2. Project 2 Hub: C:\Users\games\Desktop\Project\Python\Python MyWork\Project2\SettingAILocal
Đích phân phối:
  - C:\Users\<User>\.gemini\config\ (Global User Configuration)
  - Workspaces (.agents): Project 1 (.agents & GravityCode\.agents), Project 2 (.agents)
"""

import os
import sys
import shutil
import argparse
from datetime import datetime

# Thiết lập UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

USER_HOME = os.path.expanduser("~")

# Định nghĩa các đường dẫn chuẩn xác
PROJECT1_BASE = os.path.normpath(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project1")
PROJECT1_GRAVITY = os.path.join(PROJECT1_BASE, "GravityCode")
PROJECT1_HUB = os.path.join(PROJECT1_GRAVITY, "SKILL_RULE")
PROJECT1_HUB_SKILLS = os.path.join(PROJECT1_HUB, "skills")
PROJECT1_HUB_RULES = os.path.join(PROJECT1_HUB, "rules")
PROJECT1_GRAVITY_AGENTS = os.path.join(PROJECT1_GRAVITY, ".agents")
PROJECT1_ROOT_AGENTS = os.path.join(PROJECT1_BASE, ".agents")

PROJECT2_BASE = os.path.normpath(r"C:\Users\games\Desktop\Project\Python\Python MyWork\Project2")
PROJECT2_HUB = os.path.join(PROJECT2_BASE, "SettingAILocal")
PROJECT2_HUB_SKILLS = os.path.join(PROJECT2_HUB, "skills")
PROJECT2_HUB_RULES = os.path.join(PROJECT2_HUB, "rules")
PROJECT2_AGENTS = os.path.join(PROJECT2_HUB, ".agents")

GEMINI_CONFIG_DIR = os.path.join(USER_HOME, ".gemini", "config")
GEMINI_SKILLS = os.path.join(GEMINI_CONFIG_DIR, "skills")
GEMINI_RULES = os.path.join(GEMINI_CONFIG_DIR, "rules")


def clean_nested_directories(target_dir):
    """Dọn dẹp thư mục lồng nhau lỗi như skills/skills hoặc rules/rules."""
    if not os.path.exists(target_dir):
        return
    for item in ["skills", "rules"]:
        nested = os.path.join(target_dir, item, item)
        if os.path.exists(nested) and os.path.isdir(nested):
            print(f"🧹 Dọn dẹp thư mục lồng nhau lỗi: {nested}")
            shutil.rmtree(nested, ignore_errors=True)


def sync_directory_bidirectional(dir_a, dir_b, label_a="Project 1", label_b="Project 2"):
    """
    Đồng bộ 2 chiều hoàn toàn giữa 2 thư mục A và B:
    - Mục chỉ có ở A -> sao chép sang B
    - Mục chỉ có ở B -> sao chép sang A
    - Mục có ở cả 2 -> file có thời gian mtime mới hơn sẽ ghi đè file cũ hơn
    """
    if not os.path.exists(dir_a) and not os.path.exists(dir_b):
        return 0, 0

    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)

    items_a = set(os.listdir(dir_a)) if os.path.exists(dir_a) else set()
    items_b = set(os.listdir(dir_b)) if os.path.exists(dir_b) else set()
    all_items = items_a | items_b

    copied_a_to_b = 0
    copied_b_to_a = 0

    for item in all_items:
        if item in [".git", "__pycache__", "node_modules", "skills", "rules"] and os.path.isdir(os.path.join(dir_a, item)):
            continue

        path_a = os.path.join(dir_a, item)
        path_b = os.path.join(dir_b, item)

        # 1. Chỉ có ở A
        if os.path.exists(path_a) and not os.path.exists(path_b):
            if os.path.isdir(path_a):
                shutil.copytree(path_a, path_b)
            else:
                shutil.copy2(path_a, path_b)
            print(f"   [+ {label_a} -> {label_b}] {item}")
            copied_a_to_b += 1

        # 2. Chỉ có ở B
        elif os.path.exists(path_b) and not os.path.exists(path_a):
            if os.path.isdir(path_b):
                shutil.copytree(path_b, path_a)
            else:
                shutil.copy2(path_b, path_a)
            print(f"   [+ {label_b} -> {label_a}] {item}")
            copied_b_to_a += 1

        # 3. Có ở cả 2 bên
        else:
            if os.path.isdir(path_a) and os.path.isdir(path_b):
                sub_a_to_b, sub_b_to_a = sync_directory_bidirectional(path_a, path_b, label_a, label_b)
                copied_a_to_b += sub_a_to_b
                copied_b_to_a += sub_b_to_a
            elif os.path.isfile(path_a) and os.path.isfile(path_b):
                mtime_a = os.path.getmtime(path_a)
                mtime_b = os.path.getmtime(path_b)

                # Chênh lệch > 1 giây khi mtime lệch
                if mtime_a > mtime_b + 1:
                    shutil.copy2(path_a, path_b)
                    print(f"   [^ {label_a} cập nhật {label_b}] {item}")
                    copied_a_to_b += 1
                elif mtime_b > mtime_a + 1:
                    shutil.copy2(path_b, path_a)
                    print(f"   [^ {label_b} cập nhật {label_a}] {item}")
                    copied_b_to_a += 1

    return copied_a_to_b, copied_b_to_a


def push_to_destination(source_skills, source_rules, dest_name, target_skills, target_rules):
    """Đẩy từ kho nguồn chuẩn tới một đích phân phối."""
    os.makedirs(target_skills, exist_ok=True)
    os.makedirs(target_rules, exist_ok=True)

    # Skills
    skill_count = 0
    if os.path.exists(source_skills):
        for item in os.listdir(source_skills):
            if item in [".git", "__pycache__", "skills"]:
                continue
            src = os.path.join(source_skills, item)
            dst = os.path.join(target_skills, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                skill_count += 1
            elif os.path.isfile(src):
                shutil.copy2(src, dst)
                skill_count += 1

    # Rules
    rule_count = 0
    if os.path.exists(source_rules):
        for item in os.listdir(source_rules):
            if item in [".git", "__pycache__", "rules"]:
                continue
            src = os.path.join(source_rules, item)
            dst = os.path.join(target_rules, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                rule_count += 1
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                rule_count += 1

    print(f"   ✅ Đã đẩy tới {dest_name}: {skill_count} skills, {rule_count} rules")


def harvest_from_projects():
    """Quét các dự án con ở Project 1 và Project 2 để thu hoạch kỹ năng/quy tắc chưa gom."""
    print("\n🔍 Đang rà soát (harvest) kỹ năng / quy tắc mới từ các dự án...")
    harvested = 0

    scan_roots = [PROJECT1_GRAVITY, PROJECT2_BASE]
    for scan_root in scan_roots:
        if not os.path.exists(scan_root):
            continue
        for root, dirs, files in os.walk(scan_root):
            if any(skip in root for skip in ["SKILL_RULE", ".git", "node_modules", "__pycache__", "SettingAILocal\\skills", "SettingAILocal\\rules"]):
                continue

            # Thu hoạch SKILL.md
            if "SKILL.md" in files:
                skill_name = os.path.basename(root)
                target1 = os.path.join(PROJECT1_HUB_SKILLS, skill_name)
                target2 = os.path.join(PROJECT2_HUB_SKILLS, skill_name)
                if not os.path.exists(target1) and not os.path.exists(target2):
                    print(f"   ✨ Thu hoạch Skill mới: {skill_name} từ {root}")
                    shutil.copytree(root, target1)
                    harvested += 1

            # Thu hoạch Rule *.md
            for f in files:
                if ("rule" in f.lower() or f.endswith("_standards.md")) and f.endswith(".md"):
                    if f in ["AGENTS.md", "GEMINI.md", "README.md", "ProjectLog.md", "projectLog.md"]:
                        continue
                    t1 = os.path.join(PROJECT1_HUB_RULES, f)
                    t2 = os.path.join(PROJECT2_HUB_RULES, f)
                    if not os.path.exists(t1) and not os.path.exists(t2):
                        src = os.path.join(root, f)
                        print(f"   ✨ Thu hoạch Rule mới: {f} từ {src}")
                        shutil.copy2(src, t1)
                        harvested += 1

    if harvested == 0:
        print("   👍 Không có kỹ năng hay quy tắc nào bị bỏ sót.")
    else:
        print(f"   🎉 Đã thu hoạch {harvested} mục mới!")


def perform_sync_all():
    """Thực hiện đồng bộ 2 chiều toàn diện giữa Project 1, Project 2 và Global."""
    print("=" * 70)
    print("🚀 BẮT ĐẦU ĐỒNG BỘ 2 CHIỀU TOÀN DIỆN (Project 1 <-> Project 2 <-> Global)")
    print("=" * 70)

    # 1. Đồng bộ 2 chiều Skills giữa Project 1 và Project 2
    print("\n[Bước 1] Đồng bộ 2 chiều SKILLS giữa Project 1 & Project 2:")
    s_p1_to_p2, s_p2_to_p1 = sync_directory_bidirectional(
        PROJECT1_HUB_SKILLS, PROJECT2_HUB_SKILLS, "Project 1", "Project 2"
    )
    print(f"   -> Kết quả: {s_p1_to_p2} skills đẩy sang Project 2 | {s_p2_to_p1} skills kéo về Project 1")

    # 2. Đồng bộ 2 chiều Rules giữa Project 1 và Project 2
    print("\n[Bước 2] Đồng bộ 2 chiều RULES giữa Project 1 & Project 2:")
    r_p1_to_p2, r_p2_to_p1 = sync_directory_bidirectional(
        PROJECT1_HUB_RULES, PROJECT2_HUB_RULES, "Project 1", "Project 2"
    )
    print(f"   -> Kết quả: {r_p1_to_p2} rules đẩy sang Project 2 | {r_p2_to_p1} rules kéo về Project 1")

    # 3. Đẩy đồng nhất ra Toàn Cục (.gemini/config)
    print("\n[Bước 3] Đẩy ra Toàn Cục (~/.gemini/config):")
    push_to_destination(PROJECT2_HUB_SKILLS, PROJECT2_HUB_RULES, "Global (~/.gemini/config)", GEMINI_SKILLS, GEMINI_RULES)

    # 4. Đẩy ra các Workspace Runtime (.agents)
    print("\n[Bước 4] Đẩy ra Workspace Runtimes (.agents):")
    # Project 2 Workspace
    p2_agents_skills = os.path.join(PROJECT2_AGENTS, "skills")
    p2_agents_rules = os.path.join(PROJECT2_AGENTS, "rules")
    push_to_destination(PROJECT2_HUB_SKILLS, PROJECT2_HUB_RULES, "Project 2 Workspace (.agents)", p2_agents_skills, p2_agents_rules)

    # Project 1 Workspaces
    p1_grav_skills = os.path.join(PROJECT1_GRAVITY_AGENTS, "skills")
    p1_grav_rules = os.path.join(PROJECT1_GRAVITY_AGENTS, "rules")
    push_to_destination(PROJECT1_HUB_SKILLS, PROJECT1_HUB_RULES, "Project 1 GravityCode (.agents)", p1_grav_skills, p1_grav_rules)

    p1_root_skills = os.path.join(PROJECT1_ROOT_AGENTS, "skills")
    p1_root_rules = os.path.join(PROJECT1_ROOT_AGENTS, "rules")
    push_to_destination(PROJECT1_HUB_SKILLS, PROJECT1_HUB_RULES, "Project 1 Root (.agents)", p1_root_skills, p1_root_rules)

    # 5. Dọn dẹp thư mục lồng nhau lỗi nếu có
    for target in [PROJECT1_GRAVITY_AGENTS, PROJECT1_ROOT_AGENTS, PROJECT2_AGENTS, GEMINI_CONFIG_DIR]:
        clean_nested_directories(target)

    print("\n✨ ĐỒNG BỘ 2 CHIỀU HOÀN TẤT 100%! HỆ THỐNG ĐÃ NHẤT QUÁN TOÀN DIỆN ✨\n")


def check_status():
    """Kiểm tra và báo cáo tổng quan tình trạng đồng bộ 3 tầng."""
    print("=" * 70)
    print("📋 BÁO CÁO TÌNH TRẠNG KỸ NĂNG & QUY TẮC TOÀN CỤC")
    print("=" * 70)

    p1_skills = sorted(os.listdir(PROJECT1_HUB_SKILLS)) if os.path.exists(PROJECT1_HUB_SKILLS) else []
    p1_rules = sorted(os.listdir(PROJECT1_HUB_RULES)) if os.path.exists(PROJECT1_HUB_RULES) else []

    p2_skills = sorted(os.listdir(PROJECT2_HUB_SKILLS)) if os.path.exists(PROJECT2_HUB_SKILLS) else []
    p2_rules = sorted(os.listdir(PROJECT2_HUB_RULES)) if os.path.exists(PROJECT2_HUB_RULES) else []

    gemini_skills = sorted(os.listdir(GEMINI_SKILLS)) if os.path.exists(GEMINI_SKILLS) else []
    gemini_rules = sorted(os.listdir(GEMINI_RULES)) if os.path.exists(GEMINI_RULES) else []

    print(f"1. Project 1 Hub (GravityCode/SKILL_RULE) : {len(p1_skills)} Skills | {len(p1_rules)} Rules")
    print(f"2. Project 2 Hub (SettingAILocal)         : {len(p2_skills)} Skills | {len(p2_rules)} Rules")
    print(f"3. Toàn Cục Máy Tính (~/.gemini/config)   : {len(gemini_skills)} Skills | {len(gemini_rules)} Rules")

    # Kiểm tra lệch pha nếu có
    diff_skills = set(p1_skills) ^ set(p2_skills)
    diff_rules = set(p1_rules) ^ set(p2_rules)

    if not diff_skills and not diff_rules:
        print("\n✅ TẤT CẢ SKILLS VÀ RULES ĐÃ ĐỒNG BỘ ĐỒNG NHẤT 100% GIỮA PROJECT 1 VÀ PROJECT 2!")
    else:
        if diff_skills:
            print(f"\n⚠️ Skills chênh lệch: {diff_skills}")
        if diff_rules:
            print(f"⚠️ Rules chênh lệch: {diff_rules}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Công cụ quản lý & đồng bộ kỹ năng / quy chuẩn 2 chiều toàn cục")
    parser.add_argument("--sync-all", "--push-all", dest="sync_all", action="store_true", help="Đồng bộ 2 chiều toàn diện giữa Project 1, Project 2 và Global")
    parser.add_argument("--harvest", action="store_true", help="Quét thu hoạch kỹ năng mới từ mọi subproject")
    parser.add_argument("--check", action="store_true", help="Kiểm tra trạng thái đồng bộ hiện tại")

    args = parser.parse_args()

    if args.harvest:
        harvest_from_projects()

    if args.sync_all:
        perform_sync_all()

    # Luôn kiểm tra trạng thái
    check_status()


if __name__ == "__main__":
    main()
