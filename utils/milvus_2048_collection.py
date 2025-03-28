from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

# 连接 Milvus
connections.connect("default", host="127.0.0.1", port="19530")

# 定义集合（Collection）的 Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="goods_id", dtype=DataType.INT64),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=2048)
]
schema = CollectionSchema(fields, "High-dimensional vector collection")


# 创建集合
collection = Collection("my_collection", schema)

index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 16384}
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)