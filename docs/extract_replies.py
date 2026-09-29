# import json
# import os
# import re

# # --- CẤU HÌNH ---
# JSON_FILE = 'chats/Axiom specs 1.json'
# TARGET_CHAT_TITLE = 'Axiom specs 1' # Thay bằng tên chính xác của phiên chat
# OUTPUT_DIR = 'base/specs'  # Thư mục đầu ra cho các file .md
# # ---------------

# def sanitize_filename(name):
#     return re.sub(r'[\\/*?:"<>|]', "", name)

# def export_chat(json_path, target_title, out_dir):
#     with open(json_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     os.makedirs(out_dir, exist_ok=True)

#     for chat in data.get("conversations", []):
#         if chat.get("title") == target_title:
#             mapping = chat.get("mapping", {})
#             current_node = chat.get("current_node")
            
#             # 1. Truy xuất luồng chat chính (từ node cuối ngược về root)
#             branch = []
#             curr = current_node
#             while curr:
#                 node = mapping.get(curr)
#                 if not node:
#                     break
#                 branch.append(node)
#                 curr = node.get("parent")
            
#             # Đảo ngược lại để có thứ tự thời gian chuẩn (từ trên xuống dưới)
#             branch = branch[::-1]
            
#             msg_count = 1
#             safe_title = sanitize_filename(target_title)

#             # 2. Lọc các câu trả lời của Assistant và lưu file
#             for node in branch:
#                 message = node.get("message")
#                 if message and message.get("author", {}).get("role") == "assistant":
#                     content = message.get("content", {})
#                     if content.get("content_type") == "text":
#                         parts = content.get("parts", [])
#                         text = parts[0] if parts else ""

#                         if text.strip():
#                             file_path = os.path.join(out_dir, f"{safe_title}_{msg_count:03d}.md")
#                             print(f"✏️  Tách câu trả lời {msg_count:03d}: {text.splitlines()[0][:50]}...")
#                             with open(file_path, "w", encoding="utf-8") as out_file:
#                                 out_file.write(text)
#                             msg_count += 1

#             print(f"✅ Đã tách thành công {msg_count - 1} file .md vào thư mục '{out_dir}'!")
#             return

#     print(f"❌ Không tìm thấy phiên chat nào có tên: '{target_title}'")

# if __name__ == "__main__":
#     export_chat(JSON_FILE, TARGET_CHAT_TITLE, OUTPUT_DIR)

import json
import os
import re

# --- CẤU HÌNH ---
# Khai báo danh sách các file và tên phiên chat tương ứng bên trong file đó
# Cấu trúc: ("Tên_file.json", "Tên_phiên_chat")
# Đặt theo thứ tự bạn muốn xuất (từ cũ nhất đến mới nhất)
CHAT_SOURCES = [
    ("chats/Axiom specs 1.json", "Axiom specs 1"),
    ("chats/Axiom specs 2.json", "Axiom specs 2"),
    ("chats/Axiom specs 3.json", "Axiom specs 3"),
    ("chats/Axiom specs 4.json", "Axiom specs 4")
]

BASE_DIR = 'base'
# ---------------

def sanitize_filename(name):
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    return safe_name[:150].strip()

def export_multiple_specific_chats(sources, base_dir):
    # 1. Khởi tạo cây thư mục
    specs_dir = os.path.join(base_dir, 'specs')
    tasks_dir = os.path.join(base_dir, 'tasks')
    others_dir = os.path.join(base_dir, 'others')
    
    for directory in [specs_dir, tasks_dir, others_dir]:
        os.makedirs(directory, exist_ok=True)

    msg_count = 1 
    total_found = 0

    # 2. Duyệt qua từng cặp (file, tên chat)
    for json_path, target_title in sources:
        if not os.path.exists(json_path):
            print(f"⚠️ Bỏ qua: Không tìm thấy file '{json_path}'")
            continue
            
        print(f"📂 Mở file '{json_path}' -> Tìm phiên chat: '{target_title}'...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f).get("conversations", [])

        # Hỗ trợ cả file json chuẩn của OpenAI (list) hoặc file json từ extension (dict)
        if isinstance(data, dict):
            data = [data]

        found_in_file = False
        for chat in data:
            # Tìm đúng phiên chat được chỉ định
            if chat.get("title") == target_title:
                found_in_file = True
                total_found += 1
                mapping = chat.get("mapping", {})
                current_node = chat.get("current_node")
                
                # Truy xuất luồng chat chính
                branch = []
                curr = current_node
                while curr:
                    node = mapping.get(curr)
                    if not node:
                        break
                    branch.append(node)
                    curr = node.get("parent")
                
                branch = branch[::-1]

                # Xử lý từng tin nhắn
                for node in branch:
                    message = node.get("message")
                    if message and message.get("author", {}).get("role") == "assistant":
                        content = message.get("content", {})
                        if content.get("content_type") == "text":
                            parts = content.get("parts", [])
                            text = parts[0] if parts else ""

                            if text.strip():
                                lines = text.splitlines()
                                found_heading = False
                                
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith("# "):
                                        line_content = line[2:].strip()
                                        safe_title = sanitize_filename(line_content)
                                        
                                        if line_content.startswith("BOOTSTRAP"):
                                            target_folder = tasks_dir
                                        else:
                                            target_folder = specs_dir
                                        
                                        file_name = f"{msg_count:04d} - {safe_title}.md"
                                        found_heading = True
                                        break
                                
                                if not found_heading:
                                    target_folder = others_dir
                                    file_name = f"{msg_count:04d} - untitled.md"

                                file_path = os.path.join(target_folder, file_name)
                                with open(file_path, "w", encoding="utf-8") as out_file:
                                    out_file.write(text)
                                
                                # Tăng số đếm (tiếp tục cho file kế tiếp)
                                msg_count += 1
                break # Đã tìm thấy chat trong file này thì dừng vòng lặp for chat
        
        if not found_in_file:
            print(f"   ❌ Không tìm thấy chat '{target_title}' trong file này!")

    print(f"\n✅ Hoàn tất! Đã xử lý {total_found}/{len(sources)} phiên chat. Tổng cộng xuất ra {msg_count - 1} file .md.")

if __name__ == "__main__":
    export_multiple_specific_chats(CHAT_SOURCES, BASE_DIR)