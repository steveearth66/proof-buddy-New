import Pagination from 'react-bootstrap/Pagination';

export default function NumberedPagination({
    currentPage,
    totalPages,
    onPageChange
}) {
    return (
        <Pagination>
            <Pagination.First onClick={() => onPageChange({ page: 1 })} />
            <Pagination.Prev onClick={() => onPageChange({ page: currentPage - 1 })} />
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <Pagination.Item
                    key={page}
                    active={page === currentPage}
                    onClick={() => onPageChange({ page })}
                >
                    {page}
                </Pagination.Item>
            ))}
            <Pagination.Next onClick={() => onPageChange({ page: currentPage + 1 > totalPages ? totalPages : currentPage + 1 })} />
            <Pagination.Last onClick={() => onPageChange({ page: totalPages })} />
        </Pagination>
    );
}

export function SimplePagination({ currentPage, totalPages, onPageChange }) {
    return (
        <Pagination>
            <Pagination.Prev onClick={() => onPageChange({ page: currentPage - 1 })} />
            <Pagination.Next onClick={() => onPageChange({ page: currentPage + 1 > totalPages ? totalPages : currentPage + 1 })} />
        </Pagination>
    );
}
