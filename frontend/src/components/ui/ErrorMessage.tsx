interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-container">
      <p className="error-text">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-primary">
          Reintentar
        </button>
      )}
    </div>
  );
}
