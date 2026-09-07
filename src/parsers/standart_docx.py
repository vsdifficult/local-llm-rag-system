import asyncio
import docx

def _blocking_read_docx(file_path):
    doc = docx.Document(file_path)
    full_text = [paragraph.text for paragraph in doc.paragraphs]
    return '\n'.join(full_text)

async def read_docx_async(file_path):
    text = await asyncio.to_thread(_blocking_read_docx, file_path)
    return text

