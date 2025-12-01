import requests
import uuid
from time import sleep

async def nanobanana(prompt, image):
    try:
        identity = str(uuid.uuid4())
        session = requests.Session()
        session.headers.update({
            'origin': 'https://supawork.ai/',
            'referer': 'https://supawork.ai/nano-banana',
            'x-identity-id': identity
        })

        # 1. Get upload URL
        upload_data = session.get('https://supawork.ai/supawork/headshot/api/sys/oss/token', params={
            'f_suffix': 'png',
            'get_num': 1,
            'unsafe': 1
        }).json()

        # 2. Upload image
        if not upload_data.get('data'):
            raise Exception('Upload URL not found')
        
        put_url = upload_data['data'][0]['put']
        session.put(put_url, data=image)

        # 3. Bypass Cloudflare
        cf_token = requests.post('https://api.nekolabs.web.id/tools/bypass/cf-turnstile', json={
            'url': 'https://supawork.ai/nano-banana',
            'siteKey': '0x4AAAAAACBjrLhJyEE6mq1c'
        }).json().get('result')

        # 4. Process image
        task = session.post('https://supawork.ai/supawork/headshot/api/media/image/generator', json={
            'identity_id': identity,
            'custom_prompt': prompt,
            'image_urls': [upload_data['data'][0]['get']]
        }, headers={'x-auth-challenge': cf_token}).json()

        # 5. Wait for result
        for _ in range(60):
            result = session.get('https://supawork.ai/supawork/headshot/api/media/aigc/result/list/v1').json()
            if result.get('data', {}).get('list', [{}])[0].get('status') == 1:
                return result['data']['list'][0]['url']
            sleep(1)

        raise Exception('Timeout')

    except Exception as e:
        raise Exception(str(e))