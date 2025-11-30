import aiohttp
import filetype

async def upload_image(buffer: bytes) -> str:
    """
    Tenta enviar a imagem para qu.ax primeiro, se falhar vai pro Telegraph como fallback.
    Retorna a URL da imagem.
    """
    # Detecta tipo de imagem
    kind = filetype.guess(buffer)
    if kind:
        ext = kind.extension
        mime = kind.mime
    else:
        ext = "png"
        mime = "image/png"

    # ---------------------------
    # 1️⃣ Upload pra qu.ax
    # ---------------------------
    form = aiohttp.FormData()
    form.add_field("files[]", buffer, filename=f"upload.{ext}", content_type=mime)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://qu.ax/upload.php", data=form) as resp:
                # qu.ax retornou HTML em vez de JSON?
                if resp.content_type != "application/json":
                    raise Exception(f"Unexpected mimetype: {resp.content_type}")
                data = await resp.json()
                if data.get("success"):
                    return data["files"][0]["url"]
        except Exception as e:
            print(f"Erro no upload qu.ax: {e}")

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
            print(f"Erro no fallback Telegraph: {e}")

    # Se tudo falhar, levanta exceção
    raise Exception("Upload falhou nos dois serviços.")
