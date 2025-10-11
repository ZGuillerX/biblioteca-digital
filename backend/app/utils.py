"""
Utilidades
==========
Funciones auxiliares y utilidades generales.
"""

from datetime import datetime
from typing import Optional
import re


def validate_isbn(isbn: str) -> bool:
    """
    Valida formato de ISBN (10 o 13 dígitos).
    
    Args:
        isbn (str): ISBN a validar
        
    Returns:
        bool: True si es válido, False si no
        
    Example:
        >>> validate_isbn("978-3-16-148410-0")
        True
    """
    # Remover guiones y espacios
    isbn_clean = isbn.replace('-', '').replace(' ', '')
    
    # Verificar que solo contenga dígitos y tenga longitud correcta
    if not isbn_clean.isdigit():
        return False
    
    return len(isbn_clean) in [10, 13]


def format_date(date: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    Formatea una fecha a string.
    
    Args:
        date (datetime): Fecha a formatear
        format_str (str): Formato de salida
        
    Returns:
        str | None: Fecha formateada o None
    """
    if date is None:
        return None
    
    return date.strftime(format_str)


def sanitize_string(text: str, max_length: int = 255) -> str:
    """
    Limpia y sanitiza un string.
    
    Args:
        text (str): Texto a limpiar
        max_length (int): Longitud máxima
        
    Returns:
        str: Texto sanitizado
    """
    # Remover espacios extras
    text = ' '.join(text.split())
    
    # Truncar si es muy largo
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email (str): Email a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def calculate_days_difference(date1: datetime, date2: datetime) -> int:
    """
    Calcula diferencia en días entre dos fechas.
    
    Args:
        date1 (datetime): Primera fecha
        date2 (datetime): Segunda fecha
        
    Returns:
        int: Diferencia en días
    """
    delta = date2 - date1
    return delta.days
