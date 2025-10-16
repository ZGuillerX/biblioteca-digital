import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AuthGuard from './components/Auth/AuthGuard';

// Layout
import Navbar from './components/Layout/Navbar';

// Páginas
import HomePage from './pages/HomePage';
import BooksPage from './pages/BooksPage';
import MyLoansPage from './pages/MyLoansPage';
import AdminPage from './pages/AdminPage';

// Autenticación
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';

// Detalles
import BookDetail from './components/Books/BookDetail';

// Estilos
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="App">
          <Navbar />
          
          <Routes>
            {/* Rutas públicas */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route path="/books" element={<BooksPage />} />
            <Route path="/books/:id" element={<BookDetail />} />

            {/* Rutas protegidas */}
            <Route 
              path="/my-loans" 
              element={
                <AuthGuard>
                  <MyLoansPage />
                </AuthGuard>
              } 
            />

            {/* Rutas de admin */}
            <Route 
              path="/admin" 
              element={
                <AuthGuard requireAdmin={true}>
                  <AdminPage />
                </AuthGuard>
              } 
            />

            {/* Ruta 404 */}
            <Route 
              path="*" 
              element={
                <div className="container mt-5 text-center">
                  <h1>404</h1>
                  <p>Página no encontrada</p>
                  <a href="/" className="btn btn-primary">Volver al Inicio</a>
                </div>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
