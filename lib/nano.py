import aiohttp
import asyncio
import uuid

UA = "Mozilla/5.0 (Linux; Android 15; SM-F958 Build/AP3A.240905.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.86 Mobile Safari/537.36"

async def nanobanana(prompt: str, image_bytes: bytes):
    if not prompt:
        raise Exception("Prompt is required.")
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise Exception("Image must be a buffer.")

    identity = str(uuid.uuid4())

    # axios.create equivalent
    base_headers = {
        "authorization": "null",
        "origin": "https://supawork.ai/",
        "referer": "https://supawork.ai/nano-banana",
        "user-agent": UA,
        "x-auth-challenge": "",
        "x-identity-id": identity
    }

    async with aiohttp.ClientSession(headers=base_headers) as session:
        # ======================================
        # 1. GET /sys/oss/token
        # ======================================
        async with session.get(
            "https://supawork.ai/supawork/headshot/api/sys/oss/token",
            params={"f_suffix": "png", "get_num": 1, "unsafe": 1}
        ) as resp:
            up = await resp.json()

        if not up.get("data"):
            raise Exception("Upload url not found.")

        img = up["data"][0]

        # ======================================
        # 2. PUT upload
        # ======================================
        async with aiohttp.ClientSession() as raw:
            async with raw.put(img["put"], data=image_bytes) as r:
                if r.status != 200:
                    raise Exception("Failed to upload image.")

        # ======================================
        # 3. Bypass CF
        # ======================================
        async with aiohttp.ClientSession() as s2:
            async with s2.post(
                "https://api.nekolabs.web.id/tools/bypass/cf-turnstile",
                json={
                    "url": "https://supawork.ai/nano-banana",
                    "siteKey": "0x4AAAAAACBjrLhJyEE6mq1c"
                }
            ) as cf_resp:
                cf = await cf_resp.json()

        if not cf.get("result"):
            raise Exception("Failed to get cf token.")

        # ======================================
        # 4. GET /sys/challenge/token
        # ======================================
        async with session.get(
            "https://supawork.ai/supawork/headshot/api/sys/challenge/token",
            headers={"x-auth-challenge": cf["result"]}
        ) as resp:
            t = await resp.json()

        token = t.get("data", {}).get("challenge_token")
        if not token:
            raise Exception("Failed to get token.")

        # ======================================
        # 5. POST /media/image/generator
        # ======================================
        payload = {
            "identity_id": identity,
            "aigc_app_code": "image_to_image_generator",
            "aspect_ratio": "match_input_image",
            "currency_type": "silver",
            "custom_prompt": prompt,
            "image_urls": [img["get"]],
            "model_code": "google_nano_banana"
        }

        async with session.post(
            "https://supawork.ai/supawork/headshot/api/media/image/generator",
            json=payload,
            headers={"x-auth-challenge": token}
        ) as gen_resp:
            task = await gen_resp.json()

        if not task.get("data", {}).get("creation_id"):
            raise Exception("Failed to create task.")

        # ======================================
        # 6. POLLING /media/aigc/result/list/v1
        # ======================================
        attempts = 0
        while attempts < 60:
            async with session.get(
                "https://supawork.ai/supawork/headshot/api/media/aigc/result/list/v1",
                params={"page_no": 1, "page_size": 10, "identity_id": identity}
            ) as rr:
                data = await rr.json()

            list_item = (
                data.get("data", {})
                .get("list", [{}])[0]
                .get("list", [{}])[0]
            )

            if list_item and list_item.get("status") == 1:
                return list_item.get("url")

            attempts += 1
            await asyncio.sleep(1)

        raise Exception("Timeout - Process took too long.")
