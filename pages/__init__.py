# Pages package

from typing import Any


STYLE_TABLE: dict[str, Any] = {
    'style_table': {
        'overflowX': 'auto',
        'minWidth': '100%',
        'width': '100%',
    },
    'style_header': {
        'backgroundColor': '#f8f9fa',
        'color': '#495057',
        'fontWeight': '600',
        'fontSize': '14px',
        'borderBottom': '2px solid #dee2e6',
        'textAlign': 'center',
        'padding': '12px 8px',
    },
    'style_cell': {
        'padding': '10px 8px',
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'backgroundColor': 'white',
        'borderBottom': '1px solid #e9ecef',
        'color': '#212529',
        'fontSize': '13px',
        'fontFamily': "'Inter', 'Segoe UI', sans-serif",
    },
    'style_data': {
        'border': 'none',
        'color': '#212529',
        'backgroundColor': 'white',
    },
}


def default_data_conditional(total_row_index: int | None = None) -> list[dict[str, Any]]:
    """Return the base list of conditional styles for data rows."""
    cond: list[dict[str, Any]] = [
        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
        {'if': {'state': 'active'}, 'backgroundColor': '#e8f4f8', 'border': '1px solid #b8d4e3'},
    ]
    if total_row_index is not None:
        cond.append({
            'if': {'row_index': total_row_index},
            'backgroundColor': '#fff3cd',
            'color': '#856404',
            'fontWeight': '700',
        })
    return cond