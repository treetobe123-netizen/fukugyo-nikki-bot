"""投稿CLI: 投稿文を受け取り、ログ記録→Threads投稿までを実行する

使い方:
  echo '{"text": "..."}' | python publish.py
  echo '{"text": "...", "reply_text": "..."}' | python publish.py       # コメント欄に続きを書く場合
  echo '{"text": "...", "topic_tag": "..."}' | python publish.py         # トピックタグを付ける場合
"""
import sys
import json
import datetime
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

from load_env import load_env
from threads_api import post_text, reply_text

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.jsonl")


def append_log(record):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    payload = json.loads(sys.stdin.read())
    text = payload["text"]
    topic_tag = payload.get("topic_tag")

    env = load_env()
    post_id = post_text(env, text, topic_tag=topic_tag)

    reply_id = None
    reply_msg = payload.get("reply_text", "")
    if reply_msg:
        reply_id = reply_text(env, post_id, reply_msg)

    append_log({
        "date": datetime.date.today().isoformat(),
        "text": text,
        "post_id": post_id,
        "reply_id": reply_id,
    })

    print(json.dumps({"status": "posted", "post_id": post_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
