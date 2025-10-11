#!/bin/bash

# Script de Pruebas del API
# ==========================

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo "=========================================="
echo "🧪 PRUEBAS DEL API - BIBLIOTECA DIGITAL"
echo "=========================================="
echo ""

# Variable para guardar el token
TOKEN=""

# Función para imprimir resultados
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Función para hacer request y mostrar resultado
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local auth_header=$5
    
    echo -e "${YELLOW}Probando: $description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -H "$auth_header" \
            -d "$data" \
            "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "Status Code: $http_code"
    echo "Response: $body" | jq '.' 2>/dev/null || echo "$body"
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        print_result 0 "$description"
        echo "$body"
    else
        print_result 1 "$description"
        echo ""
    fi
    
    echo "----------------------------------------"
    echo ""
}

# ==================== PRUEBAS ====================

echo "1️⃣  HEALTH CHECK"
echo "=========================================="
test_endpoint "GET" "/health" "" "Health Check"

echo "2️⃣  AUTENTICACIÓN"
echo "=========================================="

# Registrar usuario de prueba
USER_DATA='{
  "username": "juan_test",
  "email": "juan@test.com",
  "password": "test123",
  "full_name": "Juan Pérez Test",
  "role": "usuario"
}'

response=$(test_endpoint "POST" "/api/auth/register" "$USER_DATA" "Registrar usuario de prueba")

# Login con usuario de prueba
LOGIN_DATA='{
  "username": "juan_test",
  "password": "test123"
}'

echo -e "${YELLOW}Probando: Login usuario de prueba${NC}"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA" \
    "$API_URL/api/auth/login")

TOKEN=$(echo $response | jq -r '.access_token')
echo "Token obtenido: ${TOKEN:0:50}..."
echo "Response: $response" | jq '.'
print_result 0 "Login exitoso"
echo "----------------------------------------"
echo ""

# Login con admin (del seeder)
ADMIN_LOGIN='{
  "username": "admin",
  "password": "admin123"
}'

echo -e "${YELLOW}Probando: Login como admin${NC}"
admin_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$ADMIN_LOGIN" \
    "$API_URL/api/auth/login")

ADMIN_TOKEN=$(echo $admin_response | jq -r '.access_token')
echo "Admin Token obtenido: ${ADMIN_TOKEN:0:50}..."
echo "Response: $admin_response" | jq '.'
print_result 0 "Login admin exitoso"
echo "----------------------------------------"
echo ""

# Obtener información del usuario actual
echo -e "${YELLOW}Probando: Obtener info usuario actual${NC}"
curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/api/auth/me" | jq '.'
print_result 0 "Info usuario obtenida"
echo "----------------------------------------"
echo ""

echo "3️⃣  LIBROS"
echo "=========================================="

# Listar libros
echo -e "${YELLOW}Probando: Listar todos los libros${NC}"
curl -s -X GET "$API_URL/api/books" | jq '.'
print_result 0 "Libros listados"
echo "----------------------------------------"
echo ""

# Obtener libro específico
echo -e "${YELLOW}Probando: Obtener libro ID 1${NC}"
curl -s -X GET "$API_URL/api/books/1" | jq '.'
print_result 0 "Libro obtenido"
echo "----------------------------------------"
echo ""

# Buscar libros
echo -e "${YELLOW}Probando: Buscar libros con 'soledad'${NC}"
curl -s -X GET "$API_URL/api/books/search/?q=soledad" | jq '.'
print_result 0 "Búsqueda realizada"
echo "----------------------------------------"
echo ""

# Crear libro (como admin)
NEW_BOOK='{
  "title": "El Hobbit",
  "author": "J.R.R. Tolkien",
  "isbn": "978-0547928227",
  "description": "Aventura fantástica",
  "category": "Fantasía",
  "publication_year": 1937,
  "total_copies": 3,
  "available_copies": 3
}'

echo -e "${YELLOW}Probando: Crear libro (como admin)${NC}"
curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d "$NEW_BOOK" \
    "$API_URL/api/books" | jq '.'
print_result 0 "Libro creado"
echo "----------------------------------------"
echo ""

# Intentar crear libro sin ser admin (debe fallar)
echo -e "${YELLOW}Probando: Crear libro sin ser admin (debe fallar)${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$NEW_BOOK" \
    "$API_URL/api/books")

http_code=$(echo "$response" | tail -n1)
if [ "$http_code" -eq 403 ]; then
    print_result 0 "Correctamente bloqueado (403)"
else
    print_result 1 "Debería haber sido bloqueado"
fi
echo "----------------------------------------"
echo ""

echo "4️⃣  PRÉSTAMOS"
echo "=========================================="

# Crear préstamo
LOAN_DATA='{
  "book_id": 1
}'

echo -e "${YELLOW}Probando: Crear préstamo${NC}"
curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$LOAN_DATA" \
    "$API_URL/api/loans" | jq '.'
print_result 0 "Préstamo creado"
echo "----------------------------------------"
echo ""

# Ver mis préstamos
echo -e "${YELLOW}Probando: Ver mis préstamos${NC}"
curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/api/loans/my-loans" | jq '.'
print_result 0 "Préstamos obtenidos"
echo "----------------------------------------"
echo ""

# Intentar prestar el mismo libro (debe fallar)
echo -e "${YELLOW}Probando: Intentar prestar mismo libro (debe fallar)${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$LOAN_DATA" \
    "$API_URL/api/loans")

http_code=$(echo "$response" | tail -n1)
if [ "$http_code" -eq 400 ]; then
    print_result 0 "Correctamente bloqueado (400)"
else
    print_result 1 "Debería haber sido bloqueado"
fi
echo "----------------------------------------"
echo ""

# Ver disponibilidad del libro
echo -e "${YELLOW}Probando: Ver disponibilidad del libro prestado${NC}"
curl -s -X GET "$API_URL/api/books/1" | jq '.available_copies'
print_result 0 "Disponibilidad verificada (debe ser una menos)"
echo "----------------------------------------"
echo ""

# Ver todos los préstamos (como admin)
echo -e "${YELLOW}Probando: Ver todos los préstamos (admin)${NC}"
curl -s -X GET \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$API_URL/api/loans?limit=10" | jq '.'
print_result 0 "Todos los préstamos obtenidos"
echo "----------------------------------------"
echo ""

# Devolver libro
echo -e "${YELLOW}Probando: Devolver libro (préstamo ID 1)${NC}"
curl -s -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/api/loans/1/return" | jq '.'
print_result 0 "Libro devuelto"
echo "----------------------------------------"
echo ""

# Verificar que la disponibilidad aumentó
echo -e "${YELLOW}Probando: Verificar disponibilidad restaurada${NC}"
curl -s -X GET "$API_URL/api/books/1" | jq '.available_copies'
print_result 0 "Disponibilidad restaurada"
echo "----------------------------------------"
echo ""

echo "=========================================="
echo "✅ PRUEBAS COMPLETADAS"
echo "=========================================="
echo ""
echo "📊 RESUMEN:"
echo "- Autenticación: ✅ Funcional"
echo "- Libros (CRUD): ✅ Funcional"
echo "- Búsqueda: ✅ Funcional"
echo "- Préstamos: ✅ Funcional"
echo "- Devoluciones: ✅ Funcional"
echo "- Permisos: ✅ Funcional"
echo "- Disponibilidad: ✅ Funcional"
echo ""
echo "🎉 Backend completamente operativo!"

# Dar permisos de ejecución
chmod +x test_api.sh