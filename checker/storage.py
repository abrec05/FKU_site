import hashlib
from django.core.files.base import ContentFile
from .models import CheckedExcel

def _sha256(uploaded_file) -> str:
    h = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        h.update(chunk)
    return h.hexdigest()

def save_excel_once(uploaded_file, source: str) -> tuple[CheckedExcel, bool]:
    """
    created=True  -> добавили новый файл
    created=False -> такой файл уже был (по sha256), повторно не сохраняем
    """
    digest = _sha256(uploaded_file)

    existing = CheckedExcel.objects.filter(sha256=digest).first()
    if existing:
        return existing, False

    uploaded_file.seek(0)
    content = uploaded_file.read()

    obj = CheckedExcel(
        sha256=digest,
        original_name=uploaded_file.name,
        size=getattr(uploaded_file, "size", 0) or 0,
        source=source,
    )
    obj.file.save(uploaded_file.name, ContentFile(content), save=True)
    return obj, True
