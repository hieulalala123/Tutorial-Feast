*** Hướng dẫn sử dụng FEAST ***

## 1. Khởi tạo thư mục dự án - tự tải bộ biker về 

feast init my_feature_store  
cd my_feature_store/feature_repository
 
## 2. Cấu trúc thư mục  
### 2.1: data/ : Nơi chứa file .parquet - là nơi Offline store mẫu

###  2.2: feature_store.yaml: File cấu hình kết nối (mặc định dùng SQL cho cả Registry và Online Store để làm demo)

feature_store.yaml :  
1. Offline Store: Cung cấp layer để tính toán và xử lý dữ liệu lịch sử (để generate training data và các features để serving mô hình)  
2. Online Store: Low-latency storage, chứa các latest features (để phục vụ real-time inference)  

### 2.3: Example_repo.py:  File định nghĩa các Feature (Feature Definitions)