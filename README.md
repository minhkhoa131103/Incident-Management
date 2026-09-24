# Hệ Thống Quản Lý và Phân Loại Sự Cố (Incident Management System)

Một hệ thống quản lý sự cố nội bộ mạnh mẽ được xây dựng bằng **Flask**, **SQLAlchemy**, và **Flask-Login**. Hệ thống được thiết kế để báo cáo, theo dõi, và phân loại các lỗi hoặc yêu cầu hỗ trợ với cơ chế phân quyền (RBAC) chi tiết, thông báo theo thời gian thực và ghi log kiểm toán đầy đủ.

## 🚀 Các Tính Năng Nổi Bật

* **Custom Role-Based Access Control (RBAC):** Quản lý quyền truy cập động, cho phép tạo các Role tùy chỉnh với các Permissions cụ thể (VD: `VIEW_INCIDENT`, `MANAGE_USERS`, v.v.). Các System Roles được bảo vệ nghiêm ngặt khỏi việc xóa sửa quyền.
* **Quản Lý User (User Management):** Admin có thể thêm mới, phân quyền, và vô hiệu hóa (disable) tài khoản một cách an toàn. Ngăn chặn tự khóa tài khoản Admin.
* **Theo Dõi Sự Cố (Incident Tracking):** Báo cáo, phân công, bình luận, và cập nhật trạng thái sự cố theo một quy trình chuẩn (Open → In Progress → Resolved → Closed).
* **Dashboard Nâng Cao:** Thống kê trực quan các sự cố, theo dõi sự cố quá hạn (Aging Incidents), phân bổ khối lượng công việc (Workload Distribution) và lọc theo phạm vi thời gian.
* **Hệ Thống Thông Báo (Notifications):** Tự động gửi thông báo khi một sự cố được phân công, có bình luận mới hoặc thay đổi trạng thái.
* **Nhật Ký Kiểm Toán (Audit Logs):** Mọi hành động quan trọng (tạo/sửa/xóa User, Role, Incident) đều được hệ thống tự động ghi lại với độ chính xác tuyệt đối, hỗ trợ phân trang và tìm kiếm.
* **Bảo Mật Cao (Security):** Tích hợp chống tấn công CSRF (Cross-Site Request Forgery) trên toàn cầu, băm mật khẩu, chống rò rỉ dữ liệu (IDOR), và ngăn chặn cache dữ liệu nhạy cảm trên trình duyệt (BFCache prevention).

## 🛠 Công Nghệ Sử Dụng

* **Backend:** Python 3, Flask, Flask-SQLAlchemy (ORM), Flask-Login, Flask-WTF, Flask-Migrate (Alembic).
* **Database:** SQLite (có thể dễ dàng chuyển đổi sang PostgreSQL/MySQL thông qua cấu hình URL).
* **Frontend:** HTML5, CSS3, Jinja2 Templates (Giao diện đơn giản, tốc độ tải nhanh, responsive cơ bản).

## 📦 Hướng Dẫn Cài Đặt

**1. Clone mã nguồn về máy**
```bash
git clone <repository-url>
cd CS466-Project
```

**2. Tạo và kích hoạt môi trường ảo (Virtual Environment)**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

**3. Cài đặt các thư viện cần thiết**
```bash
pip install -r requirements.txt
```

**4. Thiết lập biến môi trường**
Copy file `.env.example` thành `.env` và tùy chỉnh nếu cần thiết:
```bash
cp .env.example .env
```

**5. Khởi tạo Cơ sở dữ liệu**
Chạy các file migration để tạo bảng trong DB:
```bash
flask db upgrade
```

**6. Khởi tạo dữ liệu RBAC cốt lõi**
Do hệ thống sử dụng Custom RBAC, bạn bắt buộc phải chạy script này để tạo các Quyền (Permissions) và System Roles đầu tiên:
```bash
python migrate_rbac.py
```

**7. Tạo dữ liệu mẫu (Seed Data)**
Tạo các Categories và các tài khoản demo (nếu DB chưa có users):
```bash
python seed.py
```

**8. Chạy server**
```bash
flask run --debug
```

Hệ thống sẽ chạy ở địa chỉ: `http://127.0.0.1:5000/`

## 🔑 Tài Khoản Mặc Định (Từ seed.py)

Nếu bạn chạy `seed.py`, các tài khoản mặc định sau sẽ được tạo:
* **Admin:** `admin` / `admin123`
* **Agent:** `agent` / `agent123`
* **Reporter:** `reporter` / `reporter123`

## 📂 Cấu Trúc Thư Mục Chính

```
├── app/
│   ├── forms/          # Các class định nghĩa form và validate (Flask-WTF)
│   ├── models/         # Database Models (User, Incident, Role, AuditLog, v.v.)
│   ├── static/         # File tĩnh (CSS, JS, Images)
│   ├── templates/      # Giao diện HTML (Jinja2)
│   ├── utils/          # Các tiện ích (Decorator quyền, Ghi log, Thông báo)
│   └── views/          # Các Controllers / Routers (Blueprints)
├── migrations/         # Thư mục chứa các script nâng cấp DB (Alembic)
├── config.py           # Cấu hình dự án (Dev, Test, Prod)
├── migrate_rbac.py     # Script khởi tạo phân quyền
└── seed.py             # Script tạo dữ liệu mẫu
```
