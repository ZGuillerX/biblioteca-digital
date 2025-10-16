import { useState } from "react";
import apiClient from "../../services/apiClient";

const BulkUploadPage = () => {
  const [file, setFile] = useState(null);
  const [enrichWithGoogle, setEnrichWithGoogle] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const fileName = selectedFile.name.toLowerCase();
      if (!fileName.endsWith(".xlsx") && !fileName.endsWith(".xls")) {
        setError("Solo se aceptan archivos Excel (.xlsx, .xls)");
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError("");
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Por favor selecciona un archivo Excel");
      return;
    }

    try {
      setUploading(true);
      setProgress(0);
      setError("");
      setResult(null);

      const formData = new FormData();
      formData.append("file", file);

      const url = enrichWithGoogle
        ? "/api/books/bulk-upload?enrich_with_google=true"
        : "/api/books/bulk-upload";

      const response = await apiClient.post(url, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      setResult(response.data);
      setFile(null);
      document.getElementById("fileInput").value = "";
    } catch (err) {
      setError(err.response?.data?.detail || "Error al cargar el archivo");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const downloadTemplate = () => {
    const csvContent = `title,author,isbn,description,category,publication_year,total_copies,available_copies
El Quijote,Miguel de Cervantes,9788424934484,Novela clásica española,Ficción,1605,5,5
Cien Años de Soledad,Gabriel García Márquez,9788497592208,Realismo mágico,Ficción,1967,3,3`;

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "plantilla_libros.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="container mt-4">
      <h2 className="mb-4">Carga Masiva de Libros</h2>

      {error && (
        <div className="alert alert-danger alert-dismissible">
          {error}
          <button className="btn-close" onClick={() => setError("")}></button>
        </div>
      )}

      {/* Instrucciones */}
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">Instrucciones</h5>
        </div>
        <div className="card-body">
          <h6>Formato del archivo Excel:</h6>
          <p>El archivo debe contener las siguientes columnas obligatorias:</p>
          <ul>
            <li>
              <strong>title</strong> - Título del libro
            </li>
            <li>
              <strong>author</strong> - Autor del libro
            </li>
            <li>
              <strong>isbn</strong> - ISBN del libro (10 o 13 dígitos)
            </li>
          </ul>

          <h6 className="mt-3">Columnas opcionales:</h6>
          <ul>
            <li>
              <strong>description</strong> - Descripción del libro
            </li>
            <li>
              <strong>category</strong> - Categoría
            </li>
            <li>
              <strong>publication_year</strong> - Año de publicación
            </li>
            <li>
              <strong>total_copies</strong> - Total de copias (default: 1)
            </li>
            <li>
              <strong>available_copies</strong> - Copias disponibles (default:
              1)
            </li>
          </ul>

          <button
            className="btn btn-outline-primary btn-sm"
            onClick={downloadTemplate}
          >
            Descargar Plantilla CSV
          </button>
        </div>
      </div>

      {/* Formulario de carga */}
      <div className="card">
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Seleccionar archivo Excel</label>
            <input
              id="fileInput"
              type="file"
              className="form-control"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <div className="form-text">Formatos aceptados: .xlsx, .xls</div>
          </div>

          <div className="mb-3">
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id="enrichCheckbox"
                checked={enrichWithGoogle}
                onChange={(e) => setEnrichWithGoogle(e.target.checked)}
                disabled={uploading}
              />
              <label className="form-check-label" htmlFor="enrichCheckbox">
                Enriquecer datos con Google Books API (más lento pero completa
                información)
              </label>
            </div>
          </div>

          {uploading && (
            <div className="mb-3">
              <div className="progress">
                <div
                  className="progress-bar progress-bar-striped progress-bar-animated"
                  style={{ width: `${progress}%` }}
                >
                  {progress}%
                </div>
              </div>
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? "Cargando..." : "Subir Archivo"}
          </button>
        </div>
      </div>

      {/* Resultados */}
      {result && (
        <div className="card mt-4 border-success">
          <div className="card-header bg-success text-white">
            <h5 className="mb-0">Resultado de la Carga</h5>
          </div>
          <div className="card-body">
            <h6>Resumen:</h6>
            <ul className="list-group mb-3">
              <li className="list-group-item">
                <strong>Total de filas:</strong> {result.summary.total_rows}
              </li>
              <li className="list-group-item text-success">
                <strong>✓ Exitosos:</strong> {result.summary.successful}
              </li>
              {result.summary.enriched > 0 && (
                <li className="list-group-item text-info">
                  <strong>Enriquecidos:</strong> {result.summary.enriched}
                </li>
              )}
              <li className="list-group-item text-warning">
                <strong>⚠ Omitidos:</strong> {result.summary.skipped}
              </li>
              <li className="list-group-item text-danger">
                <strong>✗ Errores:</strong> {result.summary.errors}
              </li>
            </ul>

            {result.details.success?.length > 0 && (
              <div className="mb-3">
                <h6 className="text-success">Libros creados exitosamente:</h6>
                <ul className="list-group">
                  {result.details.success.slice(0, 5).map((item, idx) => (
                    <li key={idx} className="list-group-item">
                      <span className="badge bg-success me-2">
                        Fila {item.row}
                      </span>
                      {item.title} - ISBN: {item.isbn}
                    </li>
                  ))}
                  {result.details.success.length > 5 && (
                    <li className="list-group-item text-muted">
                      ... y {result.details.success.length - 5} más
                    </li>
                  )}
                </ul>
              </div>
            )}

            {result.details.skipped?.length > 0 && (
              <div className="mb-3">
                <h6 className="text-warning">Filas omitidas:</h6>
                <ul className="list-group">
                  {result.details.skipped.map((item, idx) => (
                    <li key={idx} className="list-group-item">
                      <span className="badge bg-warning me-2">
                        Fila {item.row}
                      </span>
                      {item.isbn && `ISBN: ${item.isbn} - `}
                      {item.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.details.errors?.length > 0 && (
              <div>
                <h6 className="text-danger">Errores:</h6>
                <ul className="list-group">
                  {result.details.errors.map((item, idx) => (
                    <li
                      key={idx}
                      className="list-group-item list-group-item-danger"
                    >
                      <span className="badge bg-danger me-2">
                        Fila {item.row}
                      </span>
                      {item.isbn && `ISBN: ${item.isbn} - `}
                      {item.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkUploadPage;
