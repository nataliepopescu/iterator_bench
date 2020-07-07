# Python 3
#
# Natalie Popescu
# July 6, 2020
#
# Present results in HTML

import argparse
import os
import json
import re
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go


path_to_compiler_types = "./results"

switcher = {
    "pre-may-3": {
        "label": "Rustc Before May 3",
        "color": "#FFA500"
    },
    "pre-may-3-nobc": {
        "label": "Rustc Before May 3 [No Bounds Checks]",
        "color": "#FF4500"
    },
    "post-may-3": {
        "label": "Rustc After May 3",
        "color": "#0571B0"
    },
    "post-may-3-nobc": {
        "label": "Rustc After May 3 [No Bounds Checks]",
        "color": "#DDA0DD"
    }
}

value_pattern = "bench:\s+([0-9,]*)\D+([0-9,]*)"
name_pattern = "(?<=test\s).*(?=\s+[.]{3}\s+bench)"


# Geometric mean helper
def geo_mean_overflow(iterable):
    a = np.log(iterable)
    return np.exp(a.sum() / len(a))


#class ResultProvider:
#
#    def __init__(self, path):
#        self._path = path


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--root_path", type=str, required=True,
                        help="Root path of CPF benchmark directory")
    parser.add_argument("--port", type=str, default="8050",
                        help="Port for Dash server to run, 8050 or 8060 on AWS")
    args = parser.parse_args()

    return args.root_path, args.port


# some setting for plot
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True


def create_options():
    options = []
    global switcher
    compiler_types = switcher.keys()
    for comp_type in compiler_types:
        label = switcher.get(comp_type, "Invalid Compiler Type").get("label")
        options.append({'label': label, 'value': comp_type})
    return options


def getPerfIterLayout():

    layout = html.Div([
#        html.Br(),
#        html.Div(children='''
#            Crate Performance when built with four Rustc Variants (Average of at least 36 runs)
#        '''),

        html.Br(),
        html.Label('Select compiler types:'),
        dcc.Checklist(id='comp_type_names',
            options=create_options(),
            value=[],
            style={'width': '50%'}
        ),

        html.Br(),
        html.Div([
            html.Label('Pick a view:'),
            dcc.RadioItems(id='comp_type_view',
                options=[
                    {'label': 'Absolute', 'value': 'abs'},
#                    {'label': 'Relative', 'value': 'rel'},
                ],
                value='abs',
                labelStyle={'display': 'inline-block'}
            ),
        ], style={'columnCount': 2, 'width': '33%'}),

        html.Br(),
        html.Label('Lower is better!'),
        html.Div(id='comp_type-content')
    ])

    return layout


@app.callback(dash.dependencies.Output('comp_type-content', 'children'),
              [dash.dependencies.Input('comp_type_names', 'value'),
               dash.dependencies.Input('comp_type_view', 'value')])
def display_comp_type_info(comp_type_names, comp_type_view):

    if comp_type_view == 'rel':
        return display_rel(comp_type_names)
    elif comp_type_view == 'abs':
        return display_abs(comp_type_names)


def display_rel(comp_type_names):
    return false


def display_abs(comp_type_names):

    def get_one_bar_abs(comp_type, bar_name, color):
        one_bmark_list = []
        one_perf_list = []

        filepath = path_to_compiler_types + "/" + comp_type

        # open file for reading
        handle = open(filepath, 'r')

        for line in handle:
            if line[:1] == '#':
                continue

            # get benchmark names for this comp_type
            name = re.search(name_pattern, line)
            if name:
                format_name = name.group(0).split("::")[0]
                one_bmark_list.append(format_name)

            # get benchmark times for this comp_type
            time = re.search(value_pattern, line)
            if time: 
                format_time = time.group(0).split()[1]
                one_perf_list.append(format_time)

        bar_one = {'x': one_bmark_list, 'y': one_perf_list, 
                   'type': 'bar', 'name': bar_name, 'marker_color': color}
        return bar_one

    bar_list = []
    for comp_type in comp_type_names:
        label = switcher.get(comp_type).get("label")
        color = switcher.get(comp_type).get("color")
        bar = get_one_bar_abs(comp_type, label, color)
        bar_list.append(bar)

    fig = go.Figure({
                    'data': bar_list,
                    'layout': {
                        'legend': {'orientation': 'h', 'x': 0.2, 'y': 1.3},
                        'yaxis': {
                            'showline': True, 
                            'linewidth': 2,
                            'ticks': "outside",
                            'mirror': 'all',
                            'linecolor': 'black',
                            'gridcolor':'rgb(200,200,200)', 
                            'nticks': 20,
                            'title': {'text': " Performance [ns/iter]"},
                        },
                        'xaxis': {
                            'linecolor': 'black',
                            'showline': True, 
                            'linewidth': 2,
                            'mirror': 'all',
                            'nticks': 10,
                            'showticklabels': True,
                            'title': {'text': "Benchmarks"},
                        },
                        'font': {'family': 'Helvetica', 'color': "Black"},
                        'plot_bgcolor': 'white',
                        'autosize': False,
                        'width': 1450, 
                        'height': 700}
                    })

    fig.update_yaxes(type="log")

    return html.Div(
        dcc.Graph(
            id='rustc-compare-graph-abs',
            figure=fig
        )
    )


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if not pathname:
        return 404

    if pathname == '/':
        pathname = '/compare_iter'

    if pathname == '/compare_iter':
        layout = getPerfIterLayout()
        return layout
    else:
        return 404


if __name__ == '__main__':
    cpf_root, port = parseArgs()
    # I'm not actually using this...
    result_path = os.path.join(cpf_root, "./results")
    #app._resultProvider = ResultProvider(result_path)

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        #dcc.Link('Performance in the Wild', href='/compareCrates'),
        #html.Br(),
        html.Div(id='page-content')
    ])

    app.run_server(debug=False, host='0.0.0.0', port=port)
