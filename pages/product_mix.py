from dash import dash_table, html, dcc
import pandas as pd
import plotly.express as px
from pages import STYLE_TABLE, default_data_conditional

from data.sample_data import (
    COL_NORM_PRODUCT,
    COL_RAW_COMM_RECEIVED,
    COL_NORM_QTY,
    _build_display_table,
)


def layout(df):
    product_sales = (
        df.groupby(COL_NORM_PRODUCT)[[COL_RAW_COMM_RECEIVED, COL_NORM_QTY]]
        .sum()
        .reset_index()
        .sort_values(by=COL_RAW_COMM_RECEIVED, ascending=False)
        if COL_NORM_PRODUCT in df.columns
        else pd.DataFrame(columns=[COL_NORM_PRODUCT, COL_RAW_COMM_RECEIVED, COL_NORM_QTY])
    )

    total_commission = pd.to_numeric(df[COL_RAW_COMM_RECEIVED], errors='coerce').fillna(0).sum() if COL_RAW_COMM_RECEIVED in df.columns else 0.0
    total_quantity = pd.to_numeric(df[COL_NORM_QTY], errors='coerce').fillna(0).sum() if COL_NORM_QTY in df.columns else 0.0
    product_count = product_sales[COL_NORM_PRODUCT].nunique() if not product_sales.empty else 0
    avg_per_product = total_commission / product_count if product_count else 0.0

    fig_bar = px.bar(
        product_sales,
        x=COL_NORM_PRODUCT,
        y=COL_RAW_COMM_RECEIVED,
        title='Sales by Product',
        color=COL_RAW_COMM_RECEIVED,
        color_continuous_scale='Cividis',
        text_auto=True,
    )
    fig_bar.update_traces(textposition='outside', texttemplate='%{text:.2s}')
    fig_scatter = px.scatter(
        product_sales,
        x=COL_NORM_QTY,
        y=COL_RAW_COMM_RECEIVED,
        size=COL_NORM_QTY,
        color=COL_NORM_PRODUCT,
        hover_name=COL_NORM_PRODUCT,
        title='Quantity vs Commission by Product',
    )

    table_df = product_sales.rename(columns={COL_RAW_COMM_RECEIVED: 'Commission'})
    _, table_df = _build_display_table(table_df, list(table_df.columns))

    return html.Div([
        html.H2('🧩 Product Mix', className='page-title'),
        html.Div(className='kpi-container', children=[
            html.Div(className='kpi-card', children=[
                html.Div('💰', className='kpi-icon'),
                html.Div([html.H4('Total Commission'), html.P(f"${total_commission:,.2f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📦', className='kpi-icon'),
                html.Div([html.H4('Units Sold'), html.P(f"{total_quantity:,.0f}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('🧩', className='kpi-icon'),
                html.Div([html.H4('Products'), html.P(f"{product_count:,}", className='kpi-value')]),
            ]),
            html.Div(className='kpi-card', children=[
                html.Div('📊', className='kpi-icon'),
                html.Div([html.H4('Avg / Product'), html.P(f"${avg_per_product:,.2f}", className='kpi-value')]),
            ]),
        ]),
        html.Div(className='chart-row', children=[
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_bar)]),
            html.Div(className='chart-container', children=[dcc.Graph(figure=fig_scatter)]),
        ]),
        html.Div(className='table-container', children=[
            html.H3('Product Breakdown'),
            dash_table.DataTable(
                data=table_df.to_dict('records'),  # type: ignore[arg-type]
                columns=[{'name': col, 'id': col} for col in table_df.columns],
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
                style_data_conditional=default_data_conditional(total_row_index=len(table_df) - 1),
            ),
        ]),
    ])