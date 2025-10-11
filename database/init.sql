CREATE DATABASE IF NOT EXISTS biblioteca_db;
USE biblioteca_db;

-- Tabla: users
-- Almacena información de usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL COMMENT 'Nombre de usuario único',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT 'Email del usuario',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Contraseña encriptada',
    full_name VARCHAR(150) COMMENT 'Nombre completo',
    role ENUM('usuario', 'admin') DEFAULT 'usuario' COMMENT 'Rol del usuario',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Usuario activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: books
-- Almacena el catálogo de libros disponibles
CREATE TABLE IF NOT EXISTS books (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL COMMENT 'Título del libro',
    author VARCHAR(150) NOT NULL COMMENT 'Autor del libro',
    isbn VARCHAR(20) UNIQUE NOT NULL COMMENT 'ISBN único',
    description TEXT COMMENT 'Descripción del libro',
    category VARCHAR(100) COMMENT 'Categoría',
    publication_year INT COMMENT 'Año de publicación',
    total_copies INT NOT NULL DEFAULT 1 COMMENT 'Copias totales',
    available_copies INT NOT NULL DEFAULT 1 COMMENT 'Copias disponibles',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de registro'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: loans
-- Registra préstamos de libros
CREATE TABLE IF NOT EXISTS loans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT 'ID del usuario',
    book_id INT NOT NULL COMMENT 'ID del libro',
    loan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha del préstamo',
    due_date TIMESTAMP NOT NULL COMMENT 'Fecha de vencimiento',
    return_date TIMESTAMP NULL COMMENT 'Fecha de devolución',
    status ENUM('activo', 'devuelto', 'vencido') DEFAULT 'activo' COMMENT 'Estado del préstamo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices para mejorar rendimiento
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_book_isbn ON books(isbn);
CREATE INDEX idx_loan_status ON loans(status);
CREATE INDEX idx_loan_user ON loans(user_id);
CREATE INDEX idx_loan_book ON loans(book_id);

-- Datos de prueba: Usuario admin
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@biblioteca.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6F.hQwu', 'Administrador', 'admin');
-- Contraseña: admin123

-- Datos de prueba: Libros
INSERT INTO books (title, author, isbn, description, category, publication_year, total_copies, available_copies) VALUES
('Cien Años de Soledad', 'Gabriel García Márquez', '978-0060883287', 'Obra maestra del realismo mágico', 'Ficción', 1967, 3, 3),
('1984', 'George Orwell', '978-0451524935', 'Novela distópica clásica', 'Ficción', 1949, 2, 2),
('El Principito', 'Antoine de Saint-Exupéry', '978-0156012195', 'Cuento filosófico', 'Infantil', 1943, 5, 5),
('Don Quijote de la Mancha', 'Miguel de Cervantes', '978-8424926441', 'Clásico de la literatura española', 'Clásico', 1605, 2, 2);

-- Verificar datos insertados
SELECT 'Users creados:' as info;
SELECT * FROM users;

SELECT 'Libros creados:' as info;
SELECT * FROM books;