import requests
import uuid
from time import sleep

# IMPORTANT: identical mobile UA used by JS
UA = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"

async def nanobanana(prompt: str, image_bytes: bytes):
    try:
        identity = str(uuid.uuid4())

        session = requests.Session()
        session.headers.update({
            "origin": "https://supawork.ai",
            "referer": "https://supawork.ai/nano-banana",
            "user-agent": UA,
            "x-identity-id": identity
        })

        # ============================================================
        # 1. GET upload URL ( /sys/oss/token )
        # ============================================================
        resp = session.get(
            "https://supawork.ai/supawork/headshot/api/sys/oss/token",
            params={"f_suffix": "png", "get_num": 1, "unsafe": 1}
        ).json()

        data_list = resp.get("data")
        if not data_list:
            raise Exception("Failed to get upload URL")

        put_url = data_list[0]["put"]
        get_url = data_list[0]["get"]

        # ============================================================
        # 2. Upload the image (PUT)
        # ============================================================
        session.put(put_url, data=image_bytes)

        # ============================================================
        # 3. BYPASS CLOUDFLARE (you already use this)
        # ============================================================
        cf_resp = requests.post(
            "https://api.nekolabs.web.id/tools/bypass/cf-turnstile",
            json={
                "url": "https://supawork.ai/nano-banana",
                "siteKey": "0x4AAAAAACBjrLhJyEE6mq1c"
            }
        ).json()

        cf_token = cf_resp.get("result")
        if not cf_token:
            raise Exception("Failed to bypass CF")

        # ============================================================
        # 4. GET challenge token (THIS WAS MISSING IN YOUR PYTHON CODE)
        # ============================================================
        chall = session.get(
            "https://supawork.ai/supawork/headshot/api/sys/challenge/token",
            headers={"x-auth-challenge": cf_token}
        ).json()

        challenge_token = chall.get("data", {}).get("token")
        if not challenge_token:
            raise Exception("Challenge token missing")

        # ============================================================
        # 5. CREATE TASK  /media/image/generator
        # ============================================================
        gen = session.post(
            "https://supawork.ai/supawork/headshot/api/media/image/generator",
            json={
                "identity_id": identity,
                "custom_prompt": prompt,
                "image_urls": [get_url]
            },
            headers={"x-auth-challenge": challenge_token}
        ).json()

        # success check?
        if gen.get("code") != 0:
            raise Exception(f"Generator error: {gen}")

        # ============================================================
        # 6. POLLING LOOP (same as JS)
        # ============================================================
        for _ in range(60):
            res = session.get(
                "https://supawork.ai/supawork/headshot/api/media/aigc/result/list/v1"
            ).json()

            lst = res.get("data", {}).get("list", [])
            if lst and lst[0].get("status") == 1:
                return lst[0].get("url")

            sleep(1)

        raise Exception("Timeout waiting for result")

    except Exception as e:
        raise Exception(str(e))
