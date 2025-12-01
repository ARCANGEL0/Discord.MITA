import aiohttp
import uuid
import asyncio

UA = "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"

async def nanobanana(prompt: str, image_bytes: bytes):
    identity = str(uuid.uuid4())
    async with aiohttp.ClientSession(headers={
        "origin": "https://supawork.ai",
        "referer": "https://supawork.ai/nano-banana",
        "user-agent": UA,
        "x-identity-id": identity
    }) as session:
        try:
            # 1. GET upload URL
            async with session.get(
                "https://supawork.ai/supawork/headshot/api/sys/oss/token",
                params={"f_suffix": "png", "get_num": 1, "unsafe": 1}
            ) as resp:
                data = await resp.json()
            if not data.get("data"):
                raise Exception("Failed to get upload URL")
            put_url = data["data"][0]["put"]
            get_url = data["data"][0]["get"]

            # 2. Upload image
            async with session.put(put_url, data=image_bytes) as r:
                if r.status != 200:
                    raise Exception(f"Failed to upload image, status {r.status}")

            # 3. Bypass Cloudflare
            async with session.post(
                "https://api.nekolabs.web.id/tools/bypass/cf-turnstile",
                json={
                    "url": "https://supawork.ai/nano-banana",
                    "siteKey": "0x4AAAAAACBjrLhJyEE6mq1c"
                }
            ) as cf_resp:
                cf_data = await cf_resp.json()
            cf_token = cf_data.get("result")
            if not cf_token:
                raise Exception("Failed to bypass CF")

            # 4. GET challenge token
            async with session.get(
                "https://supawork.ai/supawork/headshot/api/sys/challenge/token",
                headers={"x-auth-challenge": cf_token}
            ) as chall_resp:
                chall_data = await chall_resp.json()
            challenge_token = chall_data.get("data", {}).get("token")
            if not challenge_token:
                raise Exception("Challenge token missing")

            # 5. CREATE TASK
            async with session.post(
                "https://supawork.ai/supawork/headshot/api/media/image/generator",
                json={
                    "identity_id": identity,
                    "custom_prompt": prompt,
                    "image_urls": [get_url]
                },
                headers={"x-auth-challenge": challenge_token}
            ) as gen_resp:
                gen_data = await gen_resp.json()
            if gen_data.get("code") != 0:
                raise Exception(f"Generator error: {gen_data}")

            # 6. POLLING LOOP
            for _ in range(60):
                await asyncio.sleep(1)
                async with session.get(
                    "https://supawork.ai/supawork/headshot/api/media/aigc/result/list/v1"
                ) as res_resp:
                    res = await res_resp.json()
                lst = res.get("data", {}).get("list", [])
                if lst and lst[0].get("status") == 1:
                    return lst[0].get("url")

            raise Exception("Timeout waiting for result")

        except Exception as e:
            raise Exception(f"Nanobanana error: {e}")
