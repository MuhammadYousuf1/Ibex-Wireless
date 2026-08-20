from dash import Dash, dcc, html, Input, Output
from data.store import DF
from pages import home, Fees_Rebates, Accessory_GP

PAGE_LAYOUTS = {
    'spiff': {'label': 'SPIFF', 'layout': home.layout},
    'fees': {'label': 'Fees & Rebates', 'layout': Fees_Rebates.layout},
    'accessory': {'label': 'Accessory GP', 'layout': Accessory_GP.layout},
}

PAGE_CONTENTS = {
    key: page['layout'](DF)
    for key, page in PAGE_LAYOUTS.items()
}

dash_app = Dash(__name__, title='EAGLE WIRELESS DASHBOARD', suppress_callback_exceptions=True)

dash_app.layout = html.Div([
    html.H1('EAGLE WIRELESS DASHBOARD', className='app-title'),
    dcc.Tabs(
        id='page-tabs',
        value='spiff',
        children=[
            dcc.Tab(label=page['label'], value=key)
            for key, page in PAGE_LAYOUTS.items()
        ],
    ),
    html.Div(id='page-content', className='page-content-wrapper'),
])


@dash_app.callback(Output('page-content', 'children'), Input('page-tabs', 'value'))
def render_tab(tab_value):
    return PAGE_CONTENTS.get(tab_value, PAGE_CONTENTS['spiff'])


# Vercel deployment entrypoint
# ---------------------------------------
# Vercel auto-detects the Flask framework (from requirements.txt) and serves a
# WSGI application exposed as the top-level `app` variable in a recognised
# entrypoint file. Dash is built on Flask, so we expose Dash's underlying Flask
# server as `app` for Vercel, while keeping `dash_app` for layouts/callbacks.
app = dash_app.server


if __name__ == '__main__':
    dash_app.run(debug=True, host='127.0.0.1', port=8050)