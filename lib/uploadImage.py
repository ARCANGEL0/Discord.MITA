import aiohttp
import filetype
import mimetypes


async def upload_image(buffer: bytes) -> str:
    # detecta tipo da imagem pelo buffer aqui
    kind = filetype.guess(buffer)
    if kind:
        ext = kind.extension
        mime = kind.mime
    else:
        # fallback padrão
        ext = "png"
        mime = "image/png"

    # ---------------------------
    # 1️⃣ Upload pra qu.ax
    # ---------------------------
    form = aiohttp.FormData()
    form.add_field(
        "files[]",
        buffer,
        filename=f"upload.{ext}",
        content_type=mime
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://qu.ax/upload.php", data=form) as resp:
                data = await resp.json()

                # sucesso?
                if data.get("success"):
                    return data["files"][0]["url"]

        except Exception as e:
            print("Erro no upload qu.ax:", e)

        # ---------------------------
        # 2️⃣ Fallback: Telegraph
        # ---------------------------
        form2 = aiohttp.FormData()
        form2.add_field(
            "file",
            buffer,
            filename=f"upload.{ext}",
            content_type=mime
        )

        try:
            async with session.post("https://telegra.ph/upload", data=form2) as resp:
                data = await resp.json()

                if isinstance(data, list) and "src" in data[0]:
                    return "https://telegra.ph" + data[0]["src"]

        except Exception as e:
            print("Erro no fallback Telegraph:", e)

    # se tudo falhar, da erro aqui da excecao
    raise Exception("Upload falhou nos dois serviços.")