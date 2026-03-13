import pandas as pd
import ast
import time
from typing import List
from src.config.config import Config
from src.db.milvus_client import milvus_client
from langchain_community.embeddings import ZhipuAIEmbeddings

# 1. 初始化配置
COLLECTION_NAME = "sample_essays"
BATCH_SIZE = 50

# 获取封装好的客户端
client = milvus_client.get_client()

# 初始化智谱 AI 嵌入模型 (2048 维度)
embeddings_model = ZhipuAIEmbeddings(
    api_key=Config.ZHIPU_API_KEY,
    model='embedding-3',
    dimensions=2048
)

def process_and_insert():
    # 2. 读取 CSV 数据
    print("📂 正在读取 CSV 文件...")
    df = pd.read_csv('src/routers/ai/composition/ingestion/ielts_essays_processed_fixed.csv')

    # 确保集合已加载
    client.load_collection(COLLECTION_NAME)

    all_data = []
    total_rows = len(df)

    print(f"🚀 开始处理共 {total_rows} 条数据...")

    for i in range(0, total_rows, BATCH_SIZE):
        batch_df = df.iloc[i: i + BATCH_SIZE]
        batch_to_insert = []

        # 提取文本用于批量生成向量
        topics = batch_df['topic'].tolist()
        essays = batch_df['essay_text'].tolist()

        try:
            # 3. 批量生成向量 (调用智谱 AI)
            print(f"🛰️ 正在为第 {i} - {min(i + BATCH_SIZE, total_rows)} 条数据生成向量...")
            topic_vectors = embeddings_model.embed_documents(topics)
            essay_vectors = embeddings_model.embed_documents(essays)

            # 4. 构建插入数据格式
            for idx, row in batch_df.reset_index().iterrows():
                # 安全解析 tags 字符串为列表
                try:
                    tags_list = ast.literal_eval(row['tags'])
                except:
                    tags_list = []

                data_item = {
                    "topic": row['topic'],
                    "essay_text": row['essay_text'],
                    "exam_type": str(row['exam_type']),
                    "task_type": str(row['task_type']),
                    "band_score": float(row['band_score']),
                    "tags": tags_list,  # 存入 JSON 字段
                    "topic_embedding": topic_vectors[idx],
                    "essay_embedding": essay_vectors[idx]
                }
                batch_to_insert.append(data_item)

            # 5. 执行插入
            client.insert(
                collection_name=COLLECTION_NAME,
                data=batch_to_insert
            )
            print(f"✅ 已成功插入批次 {i // BATCH_SIZE + 1}")

            # 稍微停顿一下，防止请求过快
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ 处理批次 {i} 时出错: {str(e)}")
            continue

    print(f"\n✨ 数据插入完成！共计处理 {total_rows} 条记录。")


if __name__ == "__main__":
    process_and_insert()