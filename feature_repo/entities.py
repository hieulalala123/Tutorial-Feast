"""
Entity definitions.

Entity = Đối tượng mà feature gắn vào. Ví dụ: User, product, transaction, store.
Mỗi entity có join_key - khoá duy nhất để query feature

"""

from feast import Entity, ValueType

# Khởi tạo Entity chính cho Churn

user = Entity(
    name="KhachHang",
    join_keys=["user_id"],
    value_type=ValueType.INT64,
    description="Khách hàng của hệ thống - join_key là user_id",
    tags={"team":"ml_platform","owner":"hieu@abc.com","stage":"development",}
)
