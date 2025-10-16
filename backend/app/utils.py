import json
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi.responses import JSONResponse
import re as regex


# Serializador por defecto para datetime y otros tipos no serializables
def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # convierte datetime a string ISO 8601
    raise TypeError(f"Type {type(obj)} not serializable")


# respuesta JSON uniforme para todos los endpoints.
def create_response(
    status_code: int,
    message: str,
    data: Any = None,
    detail: Optional[str] = None
) -> JSONResponse:
    
    content: Dict[str, Any] = {"message": message}
    
    if data is not None:
        # Serializa data para convertir datetime a string y otros tipos no serializables
        data_json = json.loads(json.dumps(data, default=default_serializer))
        content["data"] = data_json
    
    if detail is not None:
        content["detail"] = detail
    
    return JSONResponse(
    status_code=status_code, 
    content=content,
    media_type="application/json; charset=utf-8"
)



# Valida formato de ISBN (10 o 13 dígitos). 
def validate_isbn(isbn: str) -> bool:
    isbn_clean = isbn.replace('-', '').replace(' ', '')
    if not isbn_clean.isdigit():
        return False
    return len(isbn_clean) in [10, 13]

# Formatea una fecha a string.
def format_date(date: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    if date is None:
        return None
    return date.strftime(format_str)

# Limpia y sanitiza un string.
def sanitize_string(text: str, max_length: int = 255) -> str:
    text = ' '.join(text.split())
    if len(text) > max_length:
        text = text[:max_length]
    return text.strip()

# Valida formato de email.
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return regex.match(pattern, email) is not None

# Calcula diferencia en días entre dos fechas.
def calculate_days_difference(date1: datetime, date2: datetime) -> int:
    delta = date2 - date1
    return delta.days
