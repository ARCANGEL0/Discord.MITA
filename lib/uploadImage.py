import aiohttp
import filetype

async def upload_image(buffer: bytes) -> str:
    """
    Faz upload de uma imagem a partir de um buffer de bytes.
    Tenta usar Telegraph diretamente (mais confiável atualmente).
    Retorna a URL da imagem hospedada.
    """
    # Detecta o tipo de arquivo
    kind = filetype.guess(buffer)
    if kind:
        ext = kind.extension
        mime = kind.mime
    else:
        ext = "png"
        mime = "image/png"

    # ---------------------------
    # Upload para Telegraph
    # ---------------------------
    form = aiohttp.FormData()
    form.add_field(
        "file",
        buffer,
        filename=f"upload.{ext}",
        content_type=mime
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://telegra.ph/upload", data=form) as resp:
                # Checa status antes de tentar decodificar
                if resp.status != 200:
                    raise Exception(f"Falha no upload Telegraph, status: {resp.status}")

                data = await resp.json()
                if isinstance(data, list) and "src" in data[0]:
                    return "https://telegra.ph" + data[0]["src"]
                else:
                    raise Exception(f"Resposta inesperada do Telegraph: {data}")
        except Exception as e:
            print("Erro no upload Telegraph:", e)
            raise Exception("Upload falhou.")
