from .client import LOClient
from app.settings import cfg


async def to_pdf(file):
    async with LOClient(cfg.office_url) as client:
        file_data = await file.read()
        return await client.convert_pdf(file.filename, file_data)
