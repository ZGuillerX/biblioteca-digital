"""
Módulo de Modelos Pydantic
===========================
Define los esquemas de validación de datos para requests y responses.
Utiliza Pydantic para validación automática.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re


# ==================== MODELOS DE USUARIO ====================

class UserBase(BaseModel):
    """
    Modelo base de usuario con campos comunes.
    """
    username: str = Field(..., min_length=3, max_length=100, description="Nombre de usuario único")
    email: EmailStr = Field(..., description="Email válido del usuario")
    full_name: Optional[str] = Field(None, max_length=150, description="Nombre completo")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """
        Valida que el username solo contenga letras, números y guiones bajos.
        """
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('El username solo puede contener letras, números y guiones bajos')
        return v


class UserCreate(UserBase):
    """
    Modelo para crear un nuevo usuario.
    Incluye contraseña en texto plano (será encriptada).
    """
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    role: Literal['usuario', 'admin'] = Field(default='usuario', description="Rol del usuario")
    
    @validator('password')
    def password_strength(cls, v):
        """
        Valida que la contraseña tenga al menos una letra y un número.
        """
        if not re.search(r'[A-Za-z]', v) or not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos una letra y un número')
        return v


class UserLogin(BaseModel):
    """
    Modelo para login de usuario.
    """
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")


class UserResponse(UserBase):
    """
    Modelo de respuesta de usuario (sin contraseña).
    """
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """
    Modelo para actualizar datos de usuario.
    Todos los campos son opcionales.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== MODELOS DE AUTENTICACIÓN ====================

class Token(BaseModel):
    """
    Modelo de respuesta de token JWT.
    """
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")


class TokenData(BaseModel):
    """
    Modelo de datos contenidos en el token.
    """
    username: Optional[str] = None
    role: Optional[str] = None


# ==================== MODELOS DE LIBRO ====================

class BookBase(BaseModel):
    """
    Modelo base de libro.
    """
    title: str = Field(..., min_length=1, max_length=255, description="Título del libro")
    author: str = Field(..., min_length=1, max_length=150, description="Autor del libro")
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN del libro")
    description: Optional[str] = Field(None, description="Descripción del libro")
    category: Optional[str] = Field(None, max_length=100, description="Categoría")
    publication_year: Optional[int] = Field(None, ge=1000, le=2100, description="Año de publicación")
    
    @validator('isbn')
    def validate_isbn(cls, v):
        """
        Valida formato básico de ISBN (solo números y guiones).
        """
        isbn_clean = v.replace('-', '').replace(' ', '')
        if not isbn_clean.isdigit() or len(isbn_clean) not in [10, 13]:
            raise ValueError('ISBN debe tener 10 o 13 dígitos')
        return v


class BookCreate(BookBase):
    """
    Modelo para crear un nuevo libro.
    """
    total_copies: int = Field(default=1, ge=1, description="Número total de copias")
    available_copies: int = Field(default=1, ge=0, description="Copias disponibles")
    
    @validator('available_copies')
    def validate_available_copies(cls, v, values):
        """
        Valida que las copias disponibles no excedan el total.
        """
        if 'total_copies' in values and v > values['total_copies']:
            raise ValueError('Las copias disponibles no pueden exceder el total')
        return v


class BookUpdate(BaseModel):
    """
    Modelo para actualizar un libro.
    Todos los campos son opcionales.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    total_copies: Optional[int] = Field(None, ge=1)
    available_copies: Optional[int] = Field(None, ge=0)


class BookResponse(BookBase):
    """
    Modelo de respuesta de libro.
    """
    id: int
    total_copies: int
    available_copies: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE PRÉSTAMO ====================

class LoanCreate(BaseModel):
    """
    Modelo para crear un nuevo préstamo.
    """
    book_id: int = Field(..., gt=0, description="ID del libro a prestar")


class LoanResponse(BaseModel):
    """
    Modelo de respuesta de préstamo.
    """
    id: int
    user_id: int
    book_id: int
    loan_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoanWithDetails(LoanResponse):
    """
    Modelo de préstamo con detalles del libro.
    """
    book_title: str
    book_author: str
    user_username: str


# ==================== MODELOS DE RESPUESTA GENÉRICOS ====================

class MessageResponse(BaseModel):
    """
    Modelo de respuesta genérica con mensaje.
    """
    message: str = Field(..., description="Mensaje de respuesta")
    detail: Optional[str] = Field(None, description="Detalle adicional")


class ErrorResponse(BaseModel):
    """
    Modelo de respuesta de error.
    """
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle técnico")
