from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

# 连接 Milvus
connections.connect("default", host="127.0.0.1", port="19530")

# 定义集合（Collection）的 Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="goods_id", dtype=DataType.INT64),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=960)
]
schema = CollectionSchema(fields, "960d_image_vectors")


# 创建集合
collection = Collection("dims_960_goods", schema)

index_params = {
    "metric_type": "COSINE",  # 图片相似性推荐使用余弦相似度
    "index_type": "HNSW",  # HNSW索引（推荐高召回场景） IVF_FLAT索引（平衡性能与资源）
    "params": {"M": 32, "efConstruction": 500}  # 960维需增大连接数和构建精度
    # "index_type": "IVF_FLAT",
    # "params": {"nlist": 1024}
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)