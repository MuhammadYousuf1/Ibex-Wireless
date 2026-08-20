from dash import dash_table, html, dcc, Input, Output, State, callback
import pandas as pd
import plotly.express as px
from pages import STYLE_TABLE, default_data_conditional

from data.store import DF, SOURCE_COLUMNS
from data.sample_data import (
    COL_RAW_DEVICE_MARGIN,
    COL_RAW_DEVICE_REBATE,
    _build_display_table,
    COL_RAW_DATE_A,
    COL_RAW_FEES_MARGIN,
    COL_RAW_STORE,
    COL_RAW_COMM_RECEIVED,
    COL_RAW_VARIANCE,
    COL_RAW_SKU,
    COL_RAW_IMEI,
    COL_RAW_ACT_ORDER_NUM,
)

HIDDEN_COLUMNS = {
    'VidaPaySpiff',
    'Comm Received',
    'Final Variance',
    'Invoice Verification',
    'Comments',
    'Exp Comm',
}

DISPLAY_COLUMNS = SOURCE_COLUMNS.copy()
DISPLAY_COLUMNS = [column for column in SOURCE_COLUMNS if column != COL_RAW_VARIANCE]


def _get_display_columns(df):
    return [
        column for column in DISPLAY_COLUMNS
        if column in df.columns and column not in HIDDEN_COLUMNS
    ]


def _build_table_frame(df):
    display_columns = _get_display_columns(df)
    _, display_df = _build_display_table(df.loc[:, display_columns], display_columns, sort_by=COL_RAW_DATE_A)
    return display_columns, display_df


def _build_sales_content(df):
    sales_by_store = (
        df.groupby(COL_RAW_STORE)[COL_RAW_COMM_RECEIVED]
        .sum()
        .reset_index()
        .sort_values(by=COL_RAW_COMM_RECEIVED, ascending=False)
        if COL_RAW_STORE in df.columns
        else pd.DataFrame(columns=[COL_RAW_STORE, COL_RAW_COMM_RECEIVED])
    )

    daily_sales = df.copy()
    if COL_RAW_DATE_A in daily_sales.columns:
        daily_sales[COL_RAW_DATE_A] = pd.to_datetime(daily_sales[COL_RAW_DATE_A], errors='coerce')
        daily_sales = (
            daily_sales.groupby(COL_RAW_DATE_A, as_index=False)[COL_RAW_COMM_RECEIVED]
            .sum()
            .sort_values(by=COL_RAW_DATE_A)
        )
    else:
        daily_sales = pd.DataFrame(columns=[COL_RAW_DATE_A, COL_RAW_COMM_RECEIVED])

    total_commission = pd.to_numeric(df[COL_RAW_FEES_MARGIN], errors='coerce').fillna(0).sum() if COL_RAW_FEES_MARGIN in df.columns else 0.0
    device_margin = pd.to_numeric(df[COL_RAW_DEVICE_MARGIN], errors='coerce').fillna(0).sum() if COL_RAW_DEVICE_MARGIN in df.columns else 0.0
    rebates = pd.to_numeric(df[COL_RAW_DEVICE_REBATE], errors='coerce').fillna(0).sum() if COL_RAW_DEVICE_REBATE in df.columns else 0.0

    fig_store = px.bar(
        sales_by_store,
        x=COL_RAW_STORE,
        y=COL_RAW_COMM_RECEIVED,
        title='Commission by Store',
        color=COL_RAW_COMM_RECEIVED,
        color_continuous_scale='Blues',
        text_auto=True,
    )
    fig_store.update_traces(textposition='outside', texttemplate='%{text:.2s}')

    fig_trend = px.line(
        daily_sales,
        x=COL_RAW_DATE_A,
        y=COL_RAW_COMM_RECEIVED,
        title='Daily Commission Trend',
        markers=True,
    )

    display_columns, display_df = _build_table_frame(df)

    date_series = pd.to_datetime(df[COL_RAW_DATE_A], errors='coerce')
    min_date = date_series.min()
    max_date = date_series.max()

    return html.Div([
        html.Div(className='kpi-container', children=[
            html.Div(className='kpi-card', children=[
                html.Div('💰', className='kpi-icon'),
                html.Div([html.H4('Fees Margin'), html.P(f"${total_commission:,.2f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📦', className='kpi-icon'),
                html.Div([html.H4('Device Rebates'), html.P(f"${rebates:,.2f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📦', className='kpi-icon'),
                html.Div([html.H4('Device Margin'), html.P(f"${device_margin:,.2f}", className='kpi-value')]),
            ]),
        ]),
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_store)]),
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_trend)]),
        ]),
        html.Div(className='table-container', children=[
            html.Div(
                className='table-section-header',
                children=[
                    html.H3('📋 Recent Transactions'),
                    html.Div(
                        className='table-section-actions',
                        children=[
                            html.Div(className='filter-container', children=[
                                html.Div(className='filter-label', children='📅 Date Range:'),
                                dcc.DatePickerRange(
                                    id='sales-download-date-range',
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
                                id='sales-download-csv-btn',
                                n_clicks=0,
                                className='download-btn',
                            ),
                            dcc.Download(id='sales-download-csv-data'),
                        ],
                    ),
                ],
            ),
            dash_table.DataTable(
                id='sales-data-table',
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
        ]),
    ])


def layout(df):
    date_series = pd.to_datetime(df[COL_RAW_DATE_A], errors='coerce')
    min_date = date_series.min()
    max_date = date_series.max()

    store_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_STORE].dropna().unique())] if COL_RAW_STORE in df.columns else []
    sku_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_SKU].dropna().unique())] if COL_RAW_SKU in df.columns else []
    imei_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_IMEI].dropna().unique())] if COL_RAW_IMEI in df.columns else []
    act_options = [{'label': str(s), 'value': str(s)} for s in sorted(df[COL_RAW_ACT_ORDER_NUM].dropna().unique())] if COL_RAW_ACT_ORDER_NUM in df.columns else []

    return html.Div([
        html.H2('📈 Fees & Rebates', className='page-title'),
        html.Div(
            className='filter-container',
            children=[
                html.Div(className='filter-label', children='📅 Date Range:'),
                dcc.DatePickerRange(
                    id='sales-dashboard-date-range',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format='MM-DD-YYYY',
                    className='filter-date-picker',
                ),
                html.Div(className='filter-label', children='🏪 Store:'),
                dcc.Dropdown(
                    id='sales-filter-store',
                    options=store_options,
                    placeholder='All Stores',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='📦 SKU:'),
                dcc.Dropdown(
                    id='sales-filter-sku',
                    options=sku_options,
                    placeholder='All SKUs',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='🔢 IMEI:'),
                dcc.Dropdown(
                    id='sales-filter-imei',
                    options=imei_options,
                    placeholder='All IMEIs',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
                html.Div(className='filter-label', children='📄 Act Order:'),
                dcc.Dropdown(
                    id='sales-filter-act-order',
                    options=act_options,
                    placeholder='All Orders',
                    multi=False,
                    clearable=True,
                    className='filter-dropdown',
                ),
            ],
        ),
        html.Div(id='sales-dynamic-content'),
    ])


@callback(
    Output('sales-dynamic-content', 'children'),
    Input('sales-dashboard-date-range', 'start_date'),
    Input('sales-dashboard-date-range', 'end_date'),
    Input('sales-filter-store', 'value'),
    Input('sales-filter-sku', 'value'),
    Input('sales-filter-imei', 'value'),
    Input('sales-filter-act-order', 'value'),
)
def update_sales_content(start_date, end_date, store, sku, imei, act_order):
    df = DF.copy()

    if start_date and end_date:
        date_series = pd.to_datetime(df[COL_RAW_DATE_A], errors='coerce')
        df = df.loc[(date_series >= pd.to_datetime(start_date)) & (date_series <= pd.to_datetime(end_date))]

    if store and COL_RAW_STORE in df.columns:
        df = df[df[COL_RAW_STORE].astype(str) == str(store)]
    if sku and COL_RAW_SKU in df.columns:
        df = df[df[COL_RAW_SKU].astype(str) == str(sku)]
    if imei and COL_RAW_IMEI in df.columns:
        df = df[df[COL_RAW_IMEI].astype(str) == str(imei)]
    if act_order and COL_RAW_ACT_ORDER_NUM in df.columns:
        df = df[df[COL_RAW_ACT_ORDER_NUM].astype(str) == str(act_order)]

    return _build_sales_content(df)


@callback(
    Output('sales-data-table', 'data'),
    Input('sales-download-date-range', 'start_date'),
    Input('sales-download-date-range', 'end_date'),
)
def update_sales_table(start_date, end_date):
    table_df = DF.copy()
    if start_date and end_date:
        date_series = pd.to_datetime(table_df[COL_RAW_DATE_A], errors='coerce')
        table_df = table_df.loc[
            (date_series >= pd.to_datetime(start_date)) &
            (date_series <= pd.to_datetime(end_date))
        ]
    _, display_df = _build_table_frame(table_df)
    return display_df.to_dict('records')


@callback(
    Output('sales-download-csv-data', 'data'),
    Input('sales-download-csv-btn', 'n_clicks'),
    State('sales-download-date-range', 'start_date'),
    State('sales-download-date-range', 'end_date'),
    State('sales-filter-store', 'value'),
    State('sales-filter-sku', 'value'),
    State('sales-filter-imei', 'value'),
    State('sales-filter-act-order', 'value'),
    prevent_initial_call=True,
)
def download_sales_csv(_n_clicks, start_date, end_date, store, sku, imei, act_order):
    export_df = DF.copy()
    if start_date and end_date:
        date_series = pd.to_datetime(export_df[COL_RAW_DATE_A])
        export_df = export_df.loc[
            (date_series >= pd.to_datetime(start_date)) &
            (date_series <= pd.to_datetime(end_date))
        ]

    if store and COL_RAW_STORE in export_df.columns:
        export_df = export_df[export_df[COL_RAW_STORE].astype(str) == str(store)]
    if sku and COL_RAW_SKU in export_df.columns:
        export_df = export_df[export_df[COL_RAW_SKU].astype(str) == str(sku)]
    if imei and COL_RAW_IMEI in export_df.columns:
        export_df = export_df[export_df[COL_RAW_IMEI].astype(str) == str(imei)]
    if act_order and COL_RAW_ACT_ORDER_NUM in export_df.columns:
        export_df = export_df[export_df[COL_RAW_ACT_ORDER_NUM].astype(str) == str(act_order)]

    display_columns = _get_display_columns(export_df)
    filtered_df = export_df.loc[:, display_columns]
    return dcc.send_data_frame(filtered_df.to_csv, 'sales_transactions.csv', index=False)