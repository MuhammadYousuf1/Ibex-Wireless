from dash import dash_table, html, dcc, Input, Output, State, callback
import pandas as pd
import plotly.express as px
from pages import STYLE_TABLE, default_data_conditional
from data.store import DF, SOURCE_COLUMNS
from data.sample_data import (
    _build_display_table,
    COL_RAW_DATE_A,
    COL_RAW_DATE_B,
    COL_RAW_STORE,
    COL_RAW_SKU,
    COL_RAW_IMEI,
    COL_RAW_ACT_ORDER_NUM,
    COL_RAW_COMM_RECEIVED,
    COL_RAW_VARIANCE,
    COL_RAW_FINAL_VARIANCE,
    COL_RAW_EXP_COMM,
    COL_RAW_VIDAPAY_SPIFF,
    COL_NORM_PRODUCT,
)

HIDDEN_COLUMNS = {
    'Fees Mrgin',
    'Device Mrgin',
    'Comments.1',
    'Device Rebate',
}

# All source-workbook fields, kept in their original order. This ensures the
# table shows the actual data even when a replacement workbook has new fields.
DISPLAY_COLUMNS = SOURCE_COLUMNS.copy()
# "Final Variance" column is used for KPIs instead).
DISPLAY_COLUMNS = [column for column in SOURCE_COLUMNS if column != COL_RAW_VARIANCE]

def _get_display_columns(df):
    return [
        column for column in DISPLAY_COLUMNS
        if column in df.columns and column not in HIDDEN_COLUMNS
    ]

# ==========================================
# 4. DASHBOARD VIEW LAYOUT
# ==========================================
def layout(df):
    # Date bounds for the date-range picker
    date_series = pd.to_datetime(df[COL_RAW_DATE_A])
    min_date = date_series.min()
    max_date = date_series.max()

    # Build unique options for dropdown filters
    store_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_STORE].dropna().unique())] if COL_RAW_STORE in df.columns else []
    imei_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_IMEI].dropna().unique())] if COL_RAW_IMEI in df.columns else []
    act_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_ACT_ORDER_NUM].dropna().unique())] if COL_RAW_ACT_ORDER_NUM in df.columns else []
    sku_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_SKU].dropna().unique())] if COL_RAW_SKU in df.columns else []

    return html.Div([
        html.H2('🏠 IMEI SPIFF', className='page-title'),

        # Filters Row
        html.Div(
            className='filter-container',
            children=[
                html.Div(className='filter-label', children='📅 Date Range:'),
                dcc.DatePickerRange(
                    id='dashboard-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format='MM-DD-YYYY',
                    className='filter-date-picker',
                ),
                html.Div(className='filter-label', children='🏪 Store:'),
                dcc.Dropdown(
                    id='filter-store',
                    options=store_options,
                    placeholder='All Stores',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='📦 SKU:'),
                dcc.Dropdown(
                    id='filter-sku',
                    options=sku_options,
                    placeholder='All SKUs',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='🔢 IMEI:'),
                dcc.Dropdown(
                    id='filter-imei',
                    options=imei_options,
                    placeholder='All IMEIs',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='📄 Act Order:'),
                dcc.Dropdown(
                    id='filter-act-order',
                    options=act_options,
                    placeholder='All Orders',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
            ]
        ),

        # Dynamic content updated by callback
        html.Div(id='home-dynamic-content')
    ])


# ==========================================
# 5. HELPER: BUILD DASHBOARD CONTENT FROM A DATAFRAME
# ==========================================
def _build_dashboard_content(df):
    """Given a filtered DataFrame, return the KPI cards, charts, and table."""
    total_sales = (
        pd.to_numeric(df[COL_RAW_COMM_RECEIVED], errors='coerce').fillna(0).sum()
        if COL_RAW_COMM_RECEIVED in df.columns
        else 0.0
    )
    total_variance = (
        pd.to_numeric(df[COL_RAW_FINAL_VARIANCE], errors='coerce').fillna(0).sum()
        if COL_RAW_FINAL_VARIANCE in df.columns
        else 0.0
    )
    total_imei_count = (
        df[COL_RAW_IMEI].dropna().nunique()
        if COL_RAW_IMEI in df.columns
        else 0
    )
    total_expected = (
        pd.to_numeric(df[COL_RAW_EXP_COMM], errors='coerce').fillna(0).sum()
        if COL_RAW_EXP_COMM in df.columns
        else 0.0
    )
    total_vidapay = (
        pd.to_numeric(df[COL_RAW_VIDAPAY_SPIFF], errors='coerce').fillna(0).sum()
        if COL_RAW_VIDAPAY_SPIFF in df.columns
        else 0.0
    )

    display_columns = _get_display_columns(df)

    # Date bounds for the download date picker
    date_series = pd.to_datetime(df[COL_RAW_DATE_A])
    min_date = date_series.min()
    max_date = date_series.max()

    # Sort by Date descending (newest first) then format for the table
    _, display_df = _build_display_table(df, display_columns, sort_by=COL_RAW_DATE_A)

    # --- PIE CHART: Sales by Region ---
    region_field = COL_RAW_DATE_B if COL_RAW_DATE_B in df.columns else COL_RAW_STORE
    sales_by_region = df.groupby(region_field)[COL_RAW_COMM_RECEIVED].sum().reset_index()
    fig_pie = px.pie(
        sales_by_region,
        values=COL_RAW_COMM_RECEIVED,
        names=region_field,
        title='Commission Received by Month',
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')

    # --- LINE CHART: Daily Sales Trend ---
    daily_sales = df.groupby(COL_RAW_DATE_A)[COL_RAW_COMM_RECEIVED].sum().reset_index()
    fig_line = px.line(
        daily_sales,
        x=COL_RAW_DATE_A,
        y=COL_RAW_COMM_RECEIVED,
        title='Daily Commission Trend',
        markers=True,
        line_shape='spline'
    )
    fig_line.update_traces(line_color='#1f77b4', marker=dict(size=4))
    fig_line.update_xaxes(title_text='Date')
    fig_line.update_yaxes(title_text='Sales ($)')

    # --- BAR CHART: Sales by Product (highest to lowest) ---
    product_field = COL_NORM_PRODUCT if COL_NORM_PRODUCT in df.columns else COL_RAW_SKU
    sales_by_product = (
        df.groupby(product_field)[COL_RAW_COMM_RECEIVED].sum()
        .reset_index()
        .sort_values(by=COL_RAW_COMM_RECEIVED, ascending=False)
    )
    fig_bar = px.bar(
        sales_by_product,
        x=product_field,
        y=COL_RAW_COMM_RECEIVED,
        title='Sales by Product',
        color=COL_RAW_COMM_RECEIVED,
        color_continuous_scale='Viridis',
        text_auto=True,
    )
    fig_bar.update_traces(textposition='outside', texttemplate='%{y:$,.2f}')

    return html.Div([
        # KPI Cards
        html.Div(
            className='kpi-container',
            children=[
                html.Div(className='kpi-card', children=[
                    html.Div('💰', className='kpi-icon'),
                    html.Div([
                        html.H4('Total Comm Received'),
                        html.P(f"${total_sales:,.2f}", className='kpi-value'),
                    ])
                ]),
                html.Div(className='kpi-card', children=[
                    html.Div('💵', className='kpi-icon'),
                    html.Div([
                        html.H4('Final Variance'),
                        html.P(f"${total_variance:,.2f}", className='kpi-value')
                    ])
                ]),
                html.Div(className='kpi-card', children=[
                    html.Div('🛒', className='kpi-icon'),
                    html.Div([
                        html.H4('Activated IMEI'),
                        html.P(f"{total_imei_count:,}", className='kpi-value'),
                    ])
                ]),
                html.Div(className='kpi-card', children=[
                    html.Div('⭐', className='kpi-icon'),
                    html.Div([
                        html.H4('Expected Amount'),
                        html.P(f"{total_expected:.2f}", className='kpi-value'),
                    ])
                ]),
                html.Div(className='kpi-card', children=[
                    html.Div('🛒', className='kpi-icon'),
                    html.Div([
                        html.H4('Vidapay Amount'),
                        html.P(f"{total_vidapay:.2f}", className='kpi-value'),
                    ])
                ])
            ]
        ),

        # Charts Row 1
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_pie)]),
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_line)])
        ]),

        # Charts Row 2
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container full-width', children=[dcc.Graph(figure=fig_bar)])
        ]),

        # Data Table
        html.Div(
            className="table-container",
            children=[
                html.Div(
                    className='table-section-header',
                    children=[
                        html.H3("📋 Recent Transactions"),
                        html.Div(
                            className='table-section-actions',
                            children=[
                                html.Span(
                                    "Download range:",
                                    className='download-label',
                                ),
                                dcc.DatePickerRange(
                                    id="download-date-range",
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    start_date=min_date,
                                    end_date=max_date,
                                    display_format="MM-DD-YYYY",
                                ),
                                html.Button(
                                    "Download CSV",
                                    id="download-csv-btn",
                                    n_clicks=0,
                                    className='download-btn',
                                ),
                                dcc.Download(id="download-csv-data"),
                            ],
                        ),
                    ],
                ),

                dash_table.DataTable(
                    id='workbook-data-table',
                    columns=[{'name': column, 'id': column} for column in display_columns],
                    data=display_df.to_dict('records'),  # type: ignore[arg-type]
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
                    style_data_conditional=default_data_conditional(total_row_index=len(display_df) - 1),
                ),
            ],
        )
    ])


# ==========================================
# 6. CALLBACKS
# ==========================================
@callback(
    Output('home-dynamic-content', 'children'),
    Input('dashboard-date-range', 'start_date'),
    Input('dashboard-date-range', 'end_date'),
    Input('filter-store', 'value'),
    Input('filter-sku', 'value'),
    Input('filter-imei', 'value'),
    Input('filter-act-order', 'value'),
)
def _update_dashboard(start_date, end_date, store, sku, imei, act_order):
    df = DF.copy()

    # Apply date filter
    if start_date and end_date:
        date_series = pd.to_datetime(df[COL_RAW_DATE_A])
        df = df.loc[
            (date_series >= pd.to_datetime(start_date)) &
            (date_series <= pd.to_datetime(end_date))
        ]

    # Apply dropdown filters
    if store and COL_RAW_STORE in df.columns:
        df = df[df[COL_RAW_STORE].astype(str) == str(store)]
    if sku and COL_RAW_SKU in df.columns:
        df = df[df[COL_RAW_SKU].astype(str) == str(sku)]
    if imei and COL_RAW_IMEI in df.columns:
        df = df[df[COL_RAW_IMEI].astype(str) == str(imei)]
    if act_order and COL_RAW_ACT_ORDER_NUM in df.columns:
        df = df[df[COL_RAW_ACT_ORDER_NUM].astype(str) == str(act_order)]

    return _build_dashboard_content(df)


@callback(
    Output('download-csv-data', 'data'),
    Input('download-csv-btn', 'n_clicks'),
    State('download-date-range', 'start_date'),
    State('download-date-range', 'end_date'),
    State('filter-store', 'value'),
    State('filter-sku', 'value'),
    State('filter-imei', 'value'),
    State('filter-act-order', 'value'),
    prevent_initial_call=True
)
def _download_filtered_csv(_, start_date, end_date, store, sku, imei, act_order):
    df = DF.copy()
    display_columns = _get_display_columns(df)

    if start_date and end_date:
        date_series = pd.to_datetime(df[COL_RAW_DATE_A])
        mask = (date_series >= pd.to_datetime(start_date)) & (date_series <= pd.to_datetime(end_date))
        df = df.loc[mask]

    if store and COL_RAW_STORE in df.columns:
        df = df[df[COL_RAW_STORE].astype(str) == str(store)]
    if sku and COL_RAW_SKU in df.columns:
        df = df[df[COL_RAW_SKU].astype(str) == str(sku)]
    if imei and COL_RAW_IMEI in df.columns:
        df = df[df[COL_RAW_IMEI].astype(str) == str(imei)]
    if act_order and COL_RAW_ACT_ORDER_NUM in df.columns:
        df = df[df[COL_RAW_ACT_ORDER_NUM].astype(str) == str(act_order)]

    filtered_df = df.loc[:, display_columns]
    return dcc.send_data_frame(filtered_df.to_csv, 'transactions.csv', index=False)