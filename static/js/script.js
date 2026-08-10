// Normalize FastAPI error payloads: `detail` is a string for HTTPException
// but a list of error objects for 422 validation failures.
function apiError(data, fallback) {
    const detail = data && data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map(e => e.msg || String(e)).join(', ');
    }
    return fallback;
}
