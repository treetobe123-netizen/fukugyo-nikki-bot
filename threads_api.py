"""Threads API 投稿・インサイト取得モジュール"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time

BASE = "https://graph.threads.net/v1.0"


def _post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode())


def _get(url):
    with urllib.request.urlopen(url, timeout=20) as res:
        return json.loads(res.read().decode())


def create_text_post(env, text, image_url=None, topic_tag=None):
    """投稿用のコンテナを作成し、コンテナIDを返す。image_url指定時は画像付き投稿になる。
    topic_tag指定時はThreadsのトピックタグ（例:「楽天スーパーセール」）を付与する(1〜50文字、
    ピリオド・アンパサンド不可)"""
    user_id = env["THREADS_USER_ID"]
    data = {
        "text": text,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    }
    if image_url:
        data["media_type"] = "IMAGE"
        data["image_url"] = image_url
    else:
        data["media_type"] = "TEXT"
    if topic_tag:
        data["topic_tag"] = topic_tag
    result = _post(f"{BASE}/{user_id}/threads", data)
    return result["id"]


def publish_post(env, creation_id):
    """コンテナIDから実際に投稿を公開し、投稿IDを返す"""
    user_id = env["THREADS_USER_ID"]
    data = {
        "creation_id": creation_id,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    }
    result = _post(f"{BASE}/{user_id}/threads_publish", data)
    return result["id"]


def post_text(env, text, image_url=None, topic_tag=None, wait_seconds=5):
    """投稿の作成〜公開までを一括実行。image_url指定時は画像付き投稿になる"""
    creation_id = create_text_post(env, text, image_url=image_url, topic_tag=topic_tag)
    time.sleep(wait_seconds)  # コンテナ処理待ち(公式推奨)
    return publish_post(env, creation_id)


def reply_text(env, reply_to_id, text, wait_seconds=5):
    """既存の投稿に対して自分でリンク付きリプライを投稿する"""
    user_id = env["THREADS_USER_ID"]
    data = {
        "media_type": "TEXT",
        "text": text,
        "reply_to_id": reply_to_id,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    }
    creation = _post(f"{BASE}/{user_id}/threads", data)
    time.sleep(wait_seconds)
    return publish_post(env, creation["id"])


def get_insights(env, media_id):
    """投稿のインサイト（閲覧数・いいね等）を取得"""
    params = urllib.parse.urlencode({
        "metric": "views,likes,replies,reposts,quotes",
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    data = _get(f"{BASE}/{media_id}/insights?{params}")
    metrics = {}
    for m in data.get("data", []):
        values = m.get("values", [{}])
        metrics[m["name"]] = values[0].get("value") if values else None
    return metrics


def keyword_search(env, query, search_type="TOP"):
    """キーワードで人気投稿を検索する。Meta側の提供状況次第で失敗する
    （HTTP 500等）ことがあるため、呼び出し側は失敗を許容し、黙ってスキップすること"""
    params = urllib.parse.urlencode({
        "q": query,
        "search_type": search_type,
        "access_token": env["THREADS_ACCESS_TOKEN"],
    })
    return _get(f"{BASE}/keyword_search?{params}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    from load_env import load_env
    env = load_env()

    test_text = "Threads自動投稿botのテスト投稿です。設定確認中です。"
    post_id = post_text(env, test_text)
    print(f"投稿成功: post_id={post_id}")
