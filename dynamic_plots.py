############
# IMPORTS
############


import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from mapvbvd import mapVBVD

from copy import copy
import argparse
import numpy as np

from utils.twix_dataframe import get_concat_dataframe, table
from utils.sequence_info import is_3D


############
# LAYOUT
############

def create_layout(app, list_twix):
    tags_available = [x for x in ['refscan', 'rtfeedback'] 
                      if x in list_twix[-1].keys()]    
    additional_cols = [
        'Ave','Eco','Set', 'Phs', 'Rep', 'Ida', 'Idb', 'Idc', 'Idd', 'Ide'
    ]
    max_slider=len(list_twix[-1]['image'].timestamp)
    # Layout of the app with controls aligned to the left
    app.layout = html.Div([
        # Main container with graph and left-aligned control panel
        html.Div([
            # Control panel on the left
            html.Div([
                # Marker size slider
                html.Label("Marker Size"),
                dcc.Slider(
                    id='marker-size-slider',
                    min=2,
                    max=10,
                    step=1,
                    value=6,  # Default size
                    marks={2:'2', 10:'10'},
                ),
                html.Label("Speed rate"),
                dcc.Slider(                    
                    id='speed-slider',
                    min=10,
                    max=1000,
                    step=1,
                    value=200,  # Default size
                    marks={10:'10ms', 1000:'1s'},#{i: str(i) for i in range(5, 21, 5)}  

                ),
                html.Label("Data displayed"),
                dcc.Checklist(
                    id='tags',
                    options=tags_available,
                    value=tags_available,
                )
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '15px',
                'width': '200px',
                'marginRight': '20px',
                'flex': 0.3,
            }),
            
            html.Div([
                # Scatter plot on the right
                dcc.Graph(id='scatter-plot'),
                dcc.Interval(id="animate", disabled=True, max_intervals=max_slider),
                html.Label("Animation Frame"),
                html.Button("Play | Stop", id="play", style={"width": "10%"}),
                dcc.Slider(
                    id='animation-slider',
                    min=0,
                    max=len(list_twix[-1]['image'].timestamp),
                    step=1,
                    value=0,  # Initial slider value
                    marks={0: 'start', max_slider: 'end'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                        # Buttons in the same row below the slider
                html.Div(
                    [
                        html.Button('Previous', id='previous-frame', n_clicks=0, style={"width": "8%"}),
                        html.Button('Next', id='next-frame', n_clicks=0, style={"width": "8%"}),
                    ],
                    style={"display": "flex", "justify-content": "flex-start", "margin-top": "10px"},
                ),
                
            ],style={
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '15px',
                'width': '200px',
                'marginRight': '20px',
                'flex': 1,
            }),
            html.Div([
            dcc.Graph(id='dataframe-plot'),
            dcc.Checklist(
                id='add_cols', 
                options=additional_cols, 
                value=[''],
                style={
                    'padding-left':200,
                    'display': 'grid',
                    'grid-template-columns': 'repeat(5, 1fr)',  # 3 columns
                    'grid-auto-rows': 'min-content',  # Adjust row height based on content
                    'gap': '10px',  # Spacing between items
                    'max-width': '300px',  # Adjust container width for spacing
                },
                inputStyle={'margin-right': '5px'},
                labelStyle={'display': 'block'}  # Ensures label and checkbox stay together
            )
            ],style={
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '10px',
                'width': '200px',
                'marginRight': '20px',
                'flex': 1,
                'paddingBottom': '50rem',
            })
        ], style={'display': 'flex', 'alignItems': 'flex-start'}),
    ])



#############
# CALLBACKS
#############


def set_speed_callback(app):
    @app.callback(
        Output('animate', 'interval'),
        Input('speed-slider', 'value')
    )
    def set_animation_speed(speed):
        return speed


def current_time_callbacks(app):
    @app.callback(
        Output('animation-slider', 'value'),
        Output('next-frame', 'n_clicks'),
        Output('previous-frame', 'n_clicks'),
        Input('next-frame', 'n_clicks'),
        Input('previous-frame', 'n_clicks'),
        Input('animation-slider', 'drag_value'),
        Input("animate", "n_intervals"),
        Input("animate", "disabled"),
        prevent_initial_call=True,
    )
    def next_frame(click_forward, click_before, slider_value, n, asleep):
        if not asleep and n:
            slider_value=n
        if click_forward!=0:
            slider_value+=1
        if click_before!=0:
            slider_value-=1
        return slider_value, 0, 0

    @app.callback(
        Output("animate", "n_intervals"),
        Input("play", "n_clicks"),
        Input("animate", "disabled"),
        Input('animation-slider', 'drag_value'),
        prevent_initial_call=True,
    )
    def keep_up(n, playing, slider):
        if playing and n:
            return n+1
        return slider

    @app.callback(
        Output("animate", "disabled"),
        Input("play", "n_clicks"),
        State("animate", "disabled"),
        prevent_initial_call=True,
    )
    def toggle(n, playing):
        if n:
            return not playing
        return playing


def graph_callback(app, is3D, template='simple_white'):
    # Callback to update the graph based on slider, marker size, and interval progression
    @app.callback(
        Output('scatter-plot', 'figure'),
        Output('dataframe-plot', 'figure'),
        Input('animation-slider', 'drag_value'),  # Update continuously
        Input('marker-size-slider', 'value'),
        Input('tags', 'value'),
        Input('add_cols', 'value'),
        prevent_initial_call=True,
    )
    def update_graph(n, marker_size, tags, add_cols):
        rtfeedback = 'rtfeedback' in tags
        refscan = 'refscan' in tags
        add_cols.remove('')
        df = get_concat_dataframe(
            list_twix, 
            rtfeedback=rtfeedback, 
            refscan=refscan,
            additional_cols=add_cols,
        )
        y = df.Par if is3D else df.Sli
        # Determine which points to display
        pts_displayed = df.index<n-2
        df_shown = df[pts_displayed]
        new_pt = df.index==n-1
        ylabel = 'Partition' if is3D else 'Slice'
        # Set color scale based on checkbox value
        cmin = df_shown.Time.min()
        cmax = df_shown.Time.max()
        # Create the scatter plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_shown.Lin,  # Current x data
            y=y[pts_displayed],  # Current y data
            mode='markers',
            textposition="top center",
            marker=dict(
                size=marker_size,  # Dynamic marker size
                color=df_shown.Time,
                colorscale='jet',
                colorbar=dict(title='Times (s)'),
                cmin=cmin,
                cmax=cmax,
            ),
            customdata=np.vstack([
                [ylabel]*len(df_shown), 
                df_shown.Time, 
                df_shown.tag,
            ]).T,
            hovertemplate=' Line: %{x}<br> %{customdata[0]}: %{y} \
            <br> Time: %{customdata[1]} seconds <br> type: %{customdata[2]}<extra></extra>',
            showlegend=False,
        ))
        fig.add_trace(
            go.Scatter(
                x=df.Lin[new_pt], 
                y=y[new_pt], 
                mode='markers', 
                marker=dict(size=marker_size+5, color='#E13AAE', symbol='square'),
                showlegend=False,
                customdata=np.vstack([
                    [ylabel]*len(df[new_pt]), 
                    df.Time[new_pt], 
                    df.tag[new_pt],
                ]).T,
                hovertemplate=' Line: %{x}<br> %{customdata[0]}: %{y} \
                <br> Time: %{customdata[1]} seconds <br> type: %{customdata[2]}<extra></extra>',
        ))
        margin_lin = (df.Lin.max()-df.Lin.min())*0.05
        margin_y = (y.max()-y.min())*0.05
        # Update layout
        fig.update_layout(
            template=template,
            title="Dynamic lines read map",
            title_x=0.5,
            xaxis=dict(title="Line", range=[-margin_lin + df.Lin.min(), margin_lin + df.Lin.max()]),
            yaxis=dict(title=ylabel, range=[-margin_y + np.min(y), margin_y + np.max(y)]),
            showlegend=False,
            height=800,  # Set figure height in pixels
            width=800,    # Set figure width in pixels
        )
        figure_table = table(df_shown.copy().iloc[::-1], title='Raw data', height=800)
        return fig, figure_table


############
# DASH APP
############

def create_dash_app(list_twix):
    is3D = is_3D(list_twix)
    # Retreive and copy data
    # Initialize the Dash app
    app = dash.Dash(__name__)
    # define layouts
    create_layout(app, list_twix)
    # callbacks
    set_speed_callback(app)
    current_time_callbacks(app)
    graph_callback(app, is3D)
    return app


# Run the app
if __name__ == '__main__':
    parser = argparse.ArgumentParser('Show the dynamic line maps of a sequence')
    parser.add_argument('-f', '--file', type=str, required=True, 
                        help='Siemens input twix file (.dat)')
    args = parser.parse_args()
    
    list_twix = mapVBVD(args.file, quiet=True)
    twix_df = get_concat_dataframe(list_twix, rtfeedback=True, refscan=True) # get sequence data
    app = create_dash_app(list_twix)
    app.run_server(debug=True)

    

