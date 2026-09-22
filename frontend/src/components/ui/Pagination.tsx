interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const getPages = (): (number | "...")[] => {
    const pages: (number | "...")[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push("...");
      const start = Math.max(2, page - 1);
      const end = Math.min(totalPages - 1, page + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (page < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div className="pagination">
      <button
        className="btn btn-sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        &lsaquo;
      </button>
      {getPages().map((p, i) =>
        p === "..." ? (
          <span key={`e${i}`} className="pagination-ellipsis">...</span>
        ) : (
          <button
            key={p}
            className={`btn btn-sm ${p === page ? "pagination-active" : ""}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        )
      )}
      <button
        className="btn btn-sm"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        &rsaquo;
      </button>
    </div>
  );
}
