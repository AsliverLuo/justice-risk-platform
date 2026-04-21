from app.infra.embedding import HashEmbeddingClient
from app.infra.vector_store import cosine_similarity


def test_hash_embedding_similarity():
    client = HashEmbeddingClient(dim=64)
    v1 = client.embed_text("农民工欠薪 发包方责任")
    v2 = client.embed_text("发包方拖欠农民工工资责任")
    v3 = client.embed_text("婚姻家庭纠纷")

    assert cosine_similarity(v1, v2) > cosine_similarity(v1, v3)
