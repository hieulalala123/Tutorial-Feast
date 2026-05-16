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

### 2.3: Example_repo.py:  File định nghĩa các Feature (Feature Definitions)  : là bước bạn khai báo cấu trúc dữ liệu cho hệ thống hiểu  

#### Bước 1:   
Đây là bước xác định "Entity" mà các đặc trưng sẽ xoay quanh. Entity đóng vai trò là gốc để bạn tra cứu dữ liệu.  
Nhiệm vụ: Khai báo tên thực thể và các khóa nối (join_keys) - chính là các khóa chính/composite key.

```python
from feast import Entity

driver = Entity(
    name="driver", 
    join_keys=["driver_id"], 
    description="Định danh cho tài xế"
)
```

#### Bước 2:  Định nghĩa Nguồn dữ liệu (Source Definition)  

Feature Store không trực tiếp lưu trữ dữ liệu gốc, **nó chỉ đứng ra quản lý**. Vì vậy, bạn phải chỉ cho nó biết dữ liệu gốc đang nằm ở đâu. 

**Nhiệm vụ:** Kết nối với File (Parquet, CSV), Kho dữ liệu (BigQuery, Snowflake) hoặc các luồng trực tuyến (Kafka, Kenesis). Bạn cần định nghĩa cả nguồn cho Offline (để train model) và Online (để phục vụ Real time).  

```python
from feast import FileSource

driver_stats_source = FileSource(
    path="data/driver_stats.parquet",
    event_timestamp_column="datetime",  # Cột mốc thời gian cực kỳ quan trọng
    created_timestamp_column="created"
)
```

### Bước 3: Định nghĩa Nhóm Đặc trưng (Feature View Definition)
Đây là bước quan trọng nhất. **Feature View** là nơi bạn kết dính 2 thứ ở trên lại với nhau: Gắn các cột dữ liệu cụ thể (Features) vào một Thực thể (Entity) dựa trên một Nguồn dữ liệu (Source).

**Nhiệm vụ:** 
    *   Đặt tên cho nhóm đặc trưng.
    *   Gắn nó với Entity nào.
    *   Chỉ định nguồn dữ liệu (`source`).
    *   Khai báo danh sách các cột dữ liệu (`features`) và kiểu dữ liệu của chúng (Int, Float, String...).
    *   Thiết lập thời gian tồn tại của dữ liệu (`ttl` - Time To Live).  
**Ví dụ Code:**
    
```python
from feast import FeatureView, Field
from feast.types import Float32, Int64

driver_stats_view = FeatureView(
    name="driver_hourly_stats",
    entities=[driver], # Gắn với Entity ở Step 1
    ttl=timedelta(days=365),
    schema=[
        Field(name="conv_rate", dtype=Float32),
        Field(name="acc_rate", dtype=Float32),
        Field(name="avg_daily_trips", dtype=Int64),
    ],
    online=True,
    source=driver_stats_source # Gắn với Source ở Step 2
)
    ```

### Step 4: Định nghĩa Dịch vụ Đặc trưng (Feature Service Definition - Tùy chọn nhưng khuyến khích)
Khi làm dự án thực tế, bạn sẽ có hàng trăm features, nhưng Model A chỉ cần 5 features, Model B lại cần 10 features khác. Feature Service giúp bạn nhóm các đặc trưng cụ thể lại thành một "gói dịch vụ" riêng cho từng Model.

*   **Nhiệm vụ:** Tạo ra một cổng endpoints (gói tính năng) để Model gọi trực tiếp khi deploy production. Giúp kiểm soát phiên bản (versioning) của các tập đặc trưng.
*   **Ví dụ Code:**
    
```python
    from feast import FeatureService

    driver_activity_service = FeatureService(
        name="driver_activity_v1",
        features=[driver_stats_view] # Gọi toàn bộ hoặc một phần features từ Feature View
    )
    ```

---

### Tổng kết luồng đi của Feature Definition

Sau khi bạn viết xong file định nghĩa (thường đặt tên là `feature_definition.py`), bạn sẽ chạy lệnh `feast apply` trong terminal. 



Hệ thống sẽ quét qua 4 bước bạn vừa định nghĩa để:
1.  **Ghi nhận Metadata:** Lưu cấu trúc này vào một file trung tâm (Registry).
2.  **Sẵn sàng kết nối:** Khi bạn cần lấy dữ liệu train model, nó mở `Source` ra đọc.
3.  **Sẵn sàng đồng bộ:** Khi bạn chạy lệnh `materialize`, nó sẽ tự động bốc dữ liệu từ `Source`, lọc đúng các `Fields` trong `Feature View` để đẩy vào cơ sở dữ liệu Online (như Redis) để phục vụ realtime.