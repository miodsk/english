from pymilvus import connections, Collection, utility

# 连接 Milvus
connections.connect(host="127.0.0.1", port="19530")

# 检查集合
collection_name = "sample_essays"
if not utility.has_collection(collection_name):
    print(f"❌ 集合 {collection_name} 不存在")
    exit(1)

collection = Collection(collection_name)

# 统计信息
print(f"✅ 集合名称: {collection_name}")
print(f"📊 总数据量: {collection.num_entities}")
print(f"📋 字段列表:")
for field in collection.schema.fields:
    print(f"  - {field.name}: {field.dtype}")

# 加载到内存
collection.load()

# 查询前 3 条数据
print("\n📄 前 3 条数据样本:")
results = collection.query(
    expr="",
    output_fields=["topic", "band_score", "exam_type", "task_type", "tags"],
    limit=3
)

for i, result in enumerate(results, 1):
    print(f"\n{i}. Topic: {result['topic'][:80]}...")
    print(f"   Score: {result['band_score']}")
    print(f"   Type: {result['exam_type']} - {result['task_type']}")
    print(f"   Tags: {result['tags']}")