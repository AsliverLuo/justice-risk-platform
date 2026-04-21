from openai import OpenAI

client = OpenAI(
    api_key="sk-aurnpotflyqmpsnzofguxkdolrqkshvobqrgefegjeahaizy",
    base_url="https://api.siliconflow.cn/v1",
)

resp = client.chat.completions.create(
    model="Qwen/Qwen3.5-397B-A17B",
    messages=[
        {"role": "system", "content": "你是法律AI助手，只输出JSON。"},
        {"role": "user", "content": "请输出 {\"status\":\"ok\"}"},
    ],
    temperature=0.1,
    response_format={"type": "json_object"},
    extra_body={"enable_thinking": False},
)

print(resp.choices[0].message.content)