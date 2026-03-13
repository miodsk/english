import csv
from pathlib import Path
from pymilvus import DataType
from src.db.milvus_client import milvus_client
from src.services.langchain.embedding import zhipu_embeddings

client = milvus_client.get_client()
COLLECTION_NAME = "essay_rubrics"
# ============================================================
# 1. 创建 Collection
# ============================================================
if client.has_collection(COLLECTION_NAME):
    print(f"ℹ️ 集合 '{COLLECTION_NAME}' 已存在，跳过创建。")
else:
    print(f"🚀 正在创建集合 '{COLLECTION_NAME}'...")
    schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="exam_type", datatype=DataType.VARCHAR, max_length=20)
    schema.add_field(field_name="task_type", datatype=DataType.VARCHAR, max_length=50)
    schema.add_field(field_name="dimension", datatype=DataType.VARCHAR, max_length=50)  # ✅ 改成 dimension
    schema.add_field(field_name="band_score", datatype=DataType.FLOAT)  # ✅ 改成 FLOAT
    schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=2000)
    schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=2048)
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="L2",
        params={"M": 16, "efConstruction": 64}
    )
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params
    )
    client.load_collection(COLLECTION_NAME)
    print(f"✅ 集合 '{COLLECTION_NAME}' 创建成功！")


# ============================================================
# 2. 从 CSV 读取并插入数据
# ============================================================
def insert_rubrics_from_csv():
    """从 CSV 文件读取评分标准并插入"""

    csv_path = Path(__file__).parent / "ielts_essay_rubrics.csv"

    rubrics = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rubrics.append({
                "exam_type": row["exam_type"],
                "task_type": row["task_type"],
                "dimension": row["dimension"],
                "band_score": float(row["band_score"]),
                "description": row["description"]
            })

    print(f"📝 读取到 {len(rubrics)} 条评分标准")

    # ============================================================
    # 分批生成 embedding（智谱 API 限制每次最多 64 条）
    # ============================================================
    BATCH_SIZE = 50
    descriptions = [r["description"] for r in rubrics]
    all_embeddings = []
    print("🔄 正在生成 embedding...")
    for i in range(0, len(descriptions), BATCH_SIZE):
        batch = descriptions[i:i + BATCH_SIZE]
        print(f"   处理第 {i + 1}-{min(i + BATCH_SIZE, len(descriptions))} 条...")
        batch_embeddings = zhipu_embeddings.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)
    # 构建插入数据
    data = []
    for i, rubric in enumerate(rubrics):
        data.append({
            **rubric,
            "embedding": all_embeddings[i]
        })

    # 插入数据
    client.insert(collection_name=COLLECTION_NAME, data=data)
    print(f"✅ 成功插入 {len(data)} 条评分标准！")


if __name__ == "__main__":
    insert_rubrics_from_csv()