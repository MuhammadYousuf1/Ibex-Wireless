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

app = Dash(__name__, title='EAGLE WIRELESS DASHBOARD', suppress_callback_exceptions=True)

app.layout = html.Div([
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


@app.callback(Output('page-content', 'children'), Input('page-tabs', 'value'))
def render_tab(tab_value):
    return PAGE_CONTENTS.get(tab_value, PAGE_CONTENTS['spiff'])


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)