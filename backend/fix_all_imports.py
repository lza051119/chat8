#!/usr/bin/env python3
import os
import re

def fix_imports_in_file(file_path):
    """修复单个文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 定义需要修复的导入模式
        patterns = [
            (r'^from (db)\.(\w+)', r'from app.\1.\2'),
            (r'^from (db) import', r'from app.\1 import'),
            (r'^from (schemas)\.(\w+)', r'from app.\1.\2'),
            (r'^from (services)\.(\w+)', r'from app.\1.\2'),
            (r'^from (services) import', r'from app.\1 import'),
            (r'^from (core)\.(\w+)', r'from app.\1.\2'),
            (r'^from (websocket)\.(\w+)', r'from app.\1.\2'),
        ]
        
        # 应用所有模式
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """批量修复所有Python文件的导入语句"""
    app_dir = '/Users/tsuki/Desktop/大二下/chat8/backend/app'
    fixed_count = 0
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()