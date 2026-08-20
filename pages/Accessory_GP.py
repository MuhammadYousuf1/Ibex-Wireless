from dash import dash_table, html, dcc, Input, Output, State, callback
import pandas as pd
import plotly.express as px
from pages import STYLE_TABLE, default_data_conditional
from data.store import ACCESSORY_DF
from data.sample_data import _build_display_table


COL_DATE = 'Trans Date Time'
COL_PRODUCT = 'Product Desc'
COL_QTY = 'Qty'
COL_UNIT_PRICE = 'Unit Price'
COL_DISCOUNTS = 'Discounts'
COL_EXT_PRICE = 'Ext Price'
COL_EXT_COST = 'Ext Cost'
COL_GP = 'GP'
COL_SALESPERSON = 'Salesperson'
COL_CUSTOMER = 'Customer'
COL_CATEGORY = 'Category'
COL_TOTAL_SALES = 'Total Sales'
COL_MONTH = 'Month'


def _currency_columns():
    return {COL_UNIT_PRICE, COL_EXT_PRICE, COL_EXT_COST, COL_GP, COL_TOTAL_SALES}


def _format_dollars(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _get_display_columns(df):
    return [col for col in [
        COL_DATE, COL_MONTH, COL_SALESPERSON, COL_CUSTOMER, COL_PRODUCT,
        COL_CATEGORY, COL_QTY, COL_UNIT_PRICE, COL_DISCOUNTS, COL_EXT_PRICE, COL_EXT_COST,
        COL_TOTAL_SALES, COL_GP
    ] if col in df.columns]


def _filtered_df(start_date, end_date):
    """Return ACCESSORY_DF filtered by the optional date range."""
    df = ACCESSORY_DF.copy()
    if COL_DATE in df.columns and start_date and end_date:
        date_series = pd.to_datetime(df[COL_DATE], errors='coerce')
        df = df.loc[
            (date_series >= pd.to_datetime(start_date)) &
            (date_series <= pd.to_datetime(end_date))
        ].copy()
    return df


def _date_bounds(df):
    if COL_DATE in df.columns:
        date_series = pd.to_datetime(df[COL_DATE], errors='coerce').dropna()
        if not date_series.empty:
            return date_series.min(), date_series.max()
    return None, None


def _build_table_frame(df):
    display_columns = _get_display_columns(df)
    sort_col = COL_DATE if COL_DATE in df.columns else None
    # Format dates to a sortable string before building the display table
    # (matches the original page behavior and avoids mixed-type sorts).
    frame = df.copy()
    if COL_DATE in frame.columns:
        frame[COL_DATE] = pd.to_datetime(frame[COL_DATE], errors='coerce').dt.strftime('%Y-%m-%d')
    _, display_df = _build_display_table(frame, display_columns, sort_by=sort_col, include_total_row=True)
    return display_columns, display_df


def _build_content(df):
    """Build the KPI cards, charts, and table for the accessory data."""
    # --- KPIs ---
    total_sales = pd.to_numeric(df[COL_TOTAL_SALES], errors='coerce').fillna(0).sum() if COL_TOTAL_SALES in df.columns else 0.0
    total_gp = pd.to_numeric(df[COL_GP], errors='coerce').fillna(0).sum() if COL_GP in df.columns else 0.0
    total_qty = pd.to_numeric(df[COL_QTY], errors='coerce').fillna(0).sum() if COL_QTY in df.columns else 0
    gp_margin = (total_gp / total_sales * 100) if total_sales else 0.0
    unique_products = df[COL_PRODUCT].nunique() if COL_PRODUCT in df.columns else 0

    # --- Chart 2: GP by Product (highest to lowest) ---
    gp_by_product = (
        df.groupby(COL_PRODUCT)[COL_GP].sum()
        .reset_index()
        .sort_values(by=COL_GP, ascending=False)
    )
    fig_bar_product = px.bar(
        gp_by_product,
        x=COL_PRODUCT,
        y=COL_GP,
        title='GP by Product',
        color=COL_GP,
        color_continuous_scale='Viridis',
        text_auto=True,
    )
    fig_bar_product.update_traces(textposition='inside', texttemplate='%{y:$,.2f}', showlegend=False)
    fig_bar_product.update_xaxes(showticklabels=False, title='')
    fig_bar_product.update_layout(coloraxis_showscale=False)

    # --- Chart 3: GP by Salesperson ---
    gp_by_salesperson = df.groupby(COL_SALESPERSON)[COL_GP].sum().reset_index().sort_values(COL_GP, ascending=False)
    fig_bar_sp = px.bar(
        gp_by_salesperson,
        x=COL_SALESPERSON,
        y=COL_GP,
        title='GP by Salesperson',
        color=COL_GP,
        color_continuous_scale='Greens',
        text_auto=True,
    )
    fig_bar_sp.update_traces(textposition='outside', texttemplate='$%{y:,.2f}')

    # --- Monthly GP Trend ---
    if COL_MONTH in df.columns:
        gp_by_month = df.groupby(COL_MONTH)[COL_GP].sum().reset_index()
        month_order = ['May', 'Jun', 'Jul']
        gp_by_month[COL_MONTH] = pd.Categorical(gp_by_month[COL_MONTH], categories=month_order, ordered=True)
        gp_by_month = gp_by_month.sort_values(COL_MONTH)
        fig_line = px.line(
            gp_by_month,
            x=COL_MONTH,
            y=COL_GP,
            title='Monthly GP Trend',
            markers=True,
            line_shape='spline'
        )
        fig_line.update_traces(line_color='#2ca02c', marker=dict(size=8))
    else:
        fig_line = px.line(title='Monthly GP Trend')

    # --- Data Table ---
    display_columns, table_df = _build_table_frame(df)

    # Download date-range bounds based on the current (filtered) data
    min_date, max_date = _date_bounds(df)

    return html.Div([

        # KPI Cards
        html.Div(className='kpi-container', children=[
            html.Div(className='kpi-card', children=[
                html.Div('💰', className='kpi-icon'),
                html.Div([html.H4('Total Sales'), html.P(f"${total_sales:,.2f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📈', className='kpi-icon'),
                html.Div([html.H4('Total GP'), html.P(f"${total_gp:,.2f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('🎯', className='kpi-icon'),
                html.Div([html.H4('GP Margin'), html.P(f"{gp_margin:.1f}%", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📦', className='kpi-icon'),
                html.Div([html.H4('Units Sold'), html.P(f"{total_qty:,.0f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('🏷️', className='kpi-icon'),
                html.Div([html.H4('Unique Products'), html.P(f"{unique_products:,}", className='kpi-value')]),
            ]),
        ]),

        # Charts Row 1 - GP by Product (full width)
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container full-width', children=[dcc.Graph(figure=fig_bar_product)]),
        ]),

        # Charts Row 3
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_bar_sp)]),
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_line)]),
        ]),

        # Data Table
        html.Div(className='table-container', children=[
            html.Div(
                className='table-section-header',
                children=[
                    html.H3('📋 Accessory Transactions'),
                    html.Div(
                        className='table-section-actions',
                        children=[
                            html.Div(className='filter-container', children=[
                                html.Div(className='filter-label', children='📅 Download Range:'),
                                dcc.DatePickerRange(
                                    id='accessory-download-date-range',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    start_date=min_date,
                                    end_date=max_date,
                                    display_format='MM-DD-YYYY',
                                    className='filter-date-picker',
                                ),
                            ]),
                            html.Button(
                                'Download CSV',
                                id='accessory-download-csv-btn',
                                n_clicks=0,
                                className='download-btn',
                            ),
                            dcc.Download(id='accessory-download-csv-data'),
                        ],
                    ),
                ],
            ),
            dash_table.DataTable(
                id='accessory-table',
                columns=[{'name': col, 'id': col} for col in table_df.columns],
                data=table_df.to_dict('records'),  # type: ignore[arg-type]
                virtualization=False,
                page_action='native',
                page_size=10,
                filter_action='native',
                fixed_rows={'headers': True},
                sort_action='native',
                sort_mode='multi',
                style_table=STYLE_TABLE['style_table'],
                style_header=STYLE_TABLE['style_header'],
                style_cell=STYLE_TABLE['style_cell'],
                style_data=STYLE_TABLE['style_data'],
                style_data_conditional=default_data_conditional(total_row_index=len(table_df) - 1) + [
                    {
                        'if': {'column_id': COL_GP},
                        'backgroundColor': '#fff9c4',
                        'color': '#856404 !important',
                        'fontWeight': '600',
                    },
                ],
                style_header_conditional=[
                    {
                        'if': {'column_id': COL_GP},
                        'backgroundColor': '#fff9c4 !important',
                        'color': '#856404 !important',
                        'fontWeight': '600',
                    },
                ],
                style_cell_conditional=[
                    {'if': {'column_id': col}, 'textAlign': 'right'}
                    for col in display_columns if col in _currency_columns()
                ],
            ),
        ]),
    ])


def layout(_df=None):
    """Layout for the Accessory GP page with a top date-range filter."""
    df = ACCESSORY_DF.copy()
    min_date, max_date = _date_bounds(df)

    return html.Div([
        html.H2('🔌 Accessory GP Dashboard', className='page-title'),
        html.Div(
            className='filter-container',
            children=[
                html.Div(className='filter-label', children='📅 Date Range:'),
                dcc.DatePickerRange(
                    id='accessory-dashboard-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format='MM-DD-YYYY',
                    className='filter-date-picker',
                ),
            ],
        ),
        html.Div(id='accessory-dynamic-content'),
    ])


@callback(
    Output('accessory-dynamic-content', 'children'),
    Input('accessory-dashboard-date-range', 'start_date'),
    Input('accessory-dashboard-date-range', 'end_date'),
)
def _update_accessory_content(start_date, end_date):
    df = _filtered_df(start_date, end_date)
    return _build_content(df)


@callback(
    Output('accessory-table', 'data'),
    Input('accessory-download-date-range', 'start_date'),
    Input('accessory-download-date-range', 'end_date'),
)
def _update_accessory_table(start_date, end_date):
    df = _filtered_df(start_date, end_date)
    _, display_df = _build_table_frame(df)
    return display_df.to_dict('records')


@callback(
    Output('accessory-download-csv-data', 'data'),
    Input('accessory-download-csv-btn', 'n_clicks'),
    State('accessory-download-date-range', 'start_date'),
    State('accessory-download-date-range', 'end_date'),
    prevent_initial_call=True,
)
def _download_accessory_csv(_n_clicks, start_date, end_date):
    export_df = _filtered_df(start_date, end_date)
    display_columns = _get_display_columns(export_df)
    filtered_df = export_df.loc[:, display_columns]
    return dcc.send_data_frame(filtered_df.to_csv, 'accessory_transactions.csv', index=False)