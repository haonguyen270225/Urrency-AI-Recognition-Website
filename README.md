# Urrency-AI-Recognition-Website
Website phân loại tiền và mệnh giá của ba loại tiền Việt Nam (VND), Mỹ (USD) và Trung Quốc (CNY). 
# Currency AI Recognition Website

[English](#english) | [Tiếng Việt](#tiếng-việt)

---

# English

## 1. Introduction

**Currency AI Recognition Website** is a web application that uses Artificial Intelligence (AI) to recognize and classify banknotes from three currencies:

- **VND:** Vietnamese Dong.
- **USD:** United States Dollar.
- **CNY:** Chinese Yuan.

Users can upload one or multiple images from their computers. The system analyzes the uploaded images and identifies the currency type and corresponding denomination.

**Main Features:**
- Upload one or multiple banknote images.
- Recognize VND, USD, and CNY currencies.
- Identify banknote denominations.
- Display recognition results.
- Provide a simple and user-friendly interface.

**Project Information:**

| Information | Details |
|---|---|
| Project Name | Currency AI Recognition Website |
| Repository | Currency-AI-Recognition-Website |
| Live Demo | [Currency AI Recognition](https://scan-coin-intel.base44.app/) |
| Project Type | AI-Based Web Application |

**Team Members:**

| No. | Full Name | Student ID |
|---|---|---|
| 01 | [Member 1] | [Student ID] |
| 02 | [Member 2] | [Student ID] |
| 03 | [Member 3] | [Student ID] |

## 2. Commit Convention

This project follows a simple and consistent commit convention to make the development history easier to understand and maintain.

**Commit Format:**

```text
<type>(<scope>): <short description>
```

**Commit Types:**

| Type | Description |
|---|---|
| `feat` | Add a new feature |
| `fix` | Fix a bug |
| `docs` | Update documentation |
| `style` | Update code formatting or UI styles |
| `refactor` | Improve existing code |
| `test` | Add or update tests |
| `chore` | Update configuration or dependencies |

**Examples:**

```bash
feat(upload): add multiple image upload
feat(recognition): add currency classification
fix(result): fix incorrect denomination display
docs(readme): update project documentation
style(ui): improve responsive layout
refactor(api): simplify recognition logic
```

## 3. Project Structure

The following is a suggested folder structure for organizing the project source code and resources.

```text
Currency-AI-Recognition-Website/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   │   ├── custom_cnn/
│   │   │   ├── mobilenet_v2/
│   │   │   ├── resnet/
│   │   │   ├── random_forest/
│   │   │   └── yolo/
│   │   ├── services/
│   │   │   ├── prediction_service.py
│   │   │   ├── image_service.py
│   │   │   └── model_loader.py
│   │   ├── schemas/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│
├── .gitignore
└── README.md
```

---

# Tiếng Việt

## 1. Giới thiệu dự án

**Currency AI Recognition Website** là ứng dụng web sử dụng trí tuệ nhân tạo (AI) để nhận diện và phân loại tiền giấy thuộc ba loại tiền tệ:

- **VND:** Việt Nam Đồng.
- **USD:** Đô la Mỹ.
- **CNY:** Nhân dân tệ Trung Quốc.

Người dùng có thể tải lên một hoặc nhiều hình ảnh từ máy tính. Hệ thống sẽ phân tích hình ảnh và xác định loại tiền tệ cùng mệnh giá tương ứng.

**Các chức năng chính:**
- Tải lên một hoặc nhiều hình ảnh tiền giấy.
- Nhận diện ba loại tiền VND, USD và CNY.
- Phân loại mệnh giá tiền tương ứng.
- Hiển thị kết quả nhận diện.
- Giao diện đơn giản, thân thiện và dễ sử dụng.

**Thông tin dự án:**

| Thông tin | Chi tiết |
|---|---|
| Tên dự án | Currency AI Recognition Website |
| Repository | Currency-AI-Recognition-Website |
| Demo | [Currency AI Recognition](https://scan-coin-intel.base44.app/) |
| Loại dự án | Ứng dụng web tích hợp AI |

**Thành viên thực hiện:**

| STT | Họ và tên | MSSV |
|---|---|---|
| 01 | [Thành viên 1] | [Mã sinh viên] |
| 02 | [Thành viên 2] | [Mã sinh viên] |
| 03 | [Thành viên 3] | [Mã sinh viên] |

## 2. Nguyên tắc Commit

Dự án sử dụng quy tắc đặt tên Commit thống nhất nhằm giúp lịch sử phát triển mã nguồn dễ theo dõi, quản lý và bảo trì.

**Cấu trúc Commit:**

```text
<type>(<scope>): <short description>
```

**Các loại Commit:**

| Type | Ý nghĩa |
|---|---|
| `feat` | Thêm chức năng mới |
| `fix` | Sửa lỗi |
| `docs` | Cập nhật tài liệu |
| `style` | Điều chỉnh định dạng code hoặc giao diện |
| `refactor` | Cải thiện và tái cấu trúc code |
| `test` | Thêm hoặc cập nhật kiểm thử |
| `chore` | Cập nhật cấu hình hoặc thư viện |

**Ví dụ:**

```bash
feat(upload): add multiple image upload
feat(recognition): add currency classification
fix(result): fix incorrect denomination display
docs(readme): update project documentation
style(ui): improve responsive layout
refactor(api): simplify recognition logic
```

## 3. Cấu trúc thư mục

Cấu trúc thư mục đề xuất nhằm phân chia mã nguồn, mô hình AI, dữ liệu huấn luyện và tài liệu dự án một cách rõ ràng.

```text
Currency-AI-Recognition-Website/
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── styles/
│       └── App.jsx
│
├── backend/
│   ├── controllers/
│   ├── services/
│   ├── models/
│   ├── routes/
│   └── Program.cs
│
├── model/
│   ├── training/
│   ├── prediction/
│   └── weights/
│
├── dataset/
│   ├── VND/
│   ├── USD/
│   └── CNY/
│
├── docs/
│   └── project-documentation/
│
├── README.md
└── .gitignore
```

---

**Currency AI Recognition Website** – Applying Artificial Intelligence to Currency Recognition.
