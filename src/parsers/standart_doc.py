import asyncio
import win32com.client
import os

def _blocking_read_doc_windows(file_path):
    abs_path = os.path.abspath(file_path)
    
    import pythoncom
    pythoncom.CoInitialize()
    
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        doc = word.Documents.Open(abs_path)
        text = doc.Content.Text
        
        doc.Close()
        word.Quit()
        return text
    finally:
        pythoncom.CoUninitialize()

async def read_doc_async(file_path):
    text = await asyncio.to_thread(_blocking_read_doc_windows, file_path)
    return text