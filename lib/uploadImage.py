import aiohttp
import filetype

async def upload_image(buffer: bytes) -> str:
    """Faz upload de imagem para qu.ax ou Telegraph como fallback."""
    # detecta tipo da imagem pelo buffer
    kind = filetype.guess(buffer)
    if kind:
        ext = kind.extension
        mime = kind.mime
    else:
        ext = "png"
        mime = "image/png"

    # ---------------------------
    # 1️⃣ Tenta qu.ax
    # ---------------------------
    form = aiohttp.FormData()
    form.add_field("files[]", buffer, filename=f"upload.{ext}", content_type=mime)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://qu.ax/upload.php", data=form) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = await resp.json()
                    if data.get("success"):
                        return data["files"][0]["url"]
                else:
                    print(f"⚠️ qu.ax retornou mimetype inesperado: {content_type}")
        except Exception as e:
            print("Erro no upload qu.ax:", e)

        # ---------------------------
        # 2️⃣ Fallback: Telegraph
        # ---------------------------
        form2 = aiohttp.FormData()
        form2.add_field("file", buffer, filename=f"upload.{ext}", content_type=mime)

        try:
            async with session.post("https://telegra.ph/upload", data=form2) as resp:
                data = await resp.json()
                if isinstance(data, list) and "src" in data[0]:
                    return "https://telegra.ph" + data[0]["src"]
        except Exception as e:
            print("Erro no fallback Telegraph:", e)

    # se tudo falhar
    raise Exception("Upload falhou nos dois serviços.")
