import dash, os, glob, json, io, requests
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import cufflinks
import pandas as pd
import numpy as np
from collections import defaultdict

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# #  SERDP-FISH-FIRE Data Explorer Tool                                 # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

mapbox_access_token = os.environ['MAPBOX_ACCESS_TOKEN']

def load_data():
    ''' simple data loader from a remote SNAP resource '''
    base_url = 'https://www.snap.uaf.edu/webshared/Michael/data/serdp_fish_fire'
    
    wrf_groups = ['ERA-Interim', 'GFDL-CM3', 'NCAR-CCSM4']
    # load WRF T2 Max
    wrf_t2_max = {group:pd.read_csv(io.StringIO(
        requests.get(
            base_url+\
            '/t2_{}_historical_MOD11A2_max_wrf_acis_chena_river_huc_stations.csv'\
            .format(group)).content.decode('utf-8')),index_col=0, parse_dates=True)\
           for group in wrf_groups }

    # load WRF T2 Min
    wrf_t2_min = {group:pd.read_csv(io.StringIO(
        requests.get(
            base_url+\
            '/t2_{}_historical_MOD11A2_min_wrf_acis_chena_river_huc_stations.csv'\
            .format(group)).content.decode('utf-8')),index_col=0, parse_dates=True)\
           for group in wrf_groups }


    # load WRF TSK Max
    wrf_tsk_max = {group:pd.read_csv(io.StringIO(
        requests.get(
            base_url+\
            '/tsk_{}_historical_MOD11A2_max_wrf_acis_chena_river_huc_stations.csv'\
            .format(group)).content.decode('utf-8')),index_col=0, parse_dates=True)\
           for group in wrf_groups }

    # load WRF TSK Min
    wrf_tsk_min = {group:pd.read_csv(io.StringIO(
        requests.get(
            base_url+\
            '/tsk_{}_historical_MOD11A2_min_wrf_acis_chena_river_huc_stations.csv'\
            .format(group)).content.decode('utf-8')),index_col=0, parse_dates=True)\
           for group in wrf_groups }

    # load MODIS
    modis_groups = ['MOD11A2', 'MYD11A2']
    modis = {group:pd.read_csv(io.StringIO(
        requests.get(
            base_url+\
            '/lst_{}_acis_chena_river_huc_stations.csv'\
            .format(group)).content.decode('utf-8')),index_col=0, parse_dates=True)\
           for group in modis_groups }

    # load stations -- ACIS
    url = base_url+'/tmax_acis_stationdata_8day.csv'
    s = requests.get(url).content
    stations = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)

    # load the station points csv for scattermapbox
    url = base_url+'/chena_river_huc_station_ids.csv'
    s = requests.get(url).content
    pts = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)

    return wrf_t2_max, wrf_t2_min, wrf_tsk_max, wrf_tsk_min, modis, stations, pts

# load data
wrf_t2_max, wrf_t2_min, wrf_tsk_max, wrf_tsk_min, modis, stations, pts = load_data()
wrf_max = {'t2':wrf_t2_max,'tsk':wrf_tsk_max } # stack the variables in a dict for lookup
wrf_min = {'t2':wrf_t2_min,'tsk':wrf_tsk_min } # stack the variables in a dict for lookup
pts = pts[pts.name2.isin(stations.columns)] # subset the points to fewer 'good' ones


# # if needed we can use these colors, but the defaults appear to be just fine.
# ms_colors = {'MOD11A2':'#FDD017',
#             'MYD11A2':'#F2BB66',
#             'GFDL-CM3':'#6AA121',
#             'ACIS':'#736F6E',
#             'NCAR-CCSM4':'#C35817',
#             'ERA-Interim':'#6F4E37'}


markdown_text = '''
These data constitute:
1. MODIS 8-Day Composite `LST` data from Aqua/Terra
2. WRF `t2`/`tsk` hourly data that were aggregated to:
    a. Daily Maximum's
    b. 8-Day Maximum from Daily Maximum that follow the same ranges/times-of-day as the MODIS LST-Day data*
     * that information derived from the metadata of the input raw WRF data.
'''

app = dash.Dash(__name__)
server = app.server
server.secret_key = os.environ['secret_key']
app.config.supress_callback_exceptions = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.title = 'SERDP-Fish-Fire'

map_traces = [
    go.Scattermapbox(
        lat=pts.loc[:, 'lat'],
        lon=pts.loc[:, 'lon'],
        mode='markers',
        marker={
            'size': 7,
            'color': 'rgb(140,86,75)'
        },
        line={
            'color': 'rgb(0, 0, 0)',
            'width': 2
        },
        text=pts.loc[:, 'name'],
        hoverinfo='text'
    )
]

map_layout = go.Layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        zoom=6.5,
        center=dict(lat=64.85, lon=-147.15),
        # layers=[
        #     dict(
        #         sourcetype='geojson',
        #         source=json.loads(open('./NorthwestTerritories_4326.geojson', 'r').read()),
        #         type='fill',
        #         color='rgba(255,0,0,0.1)'
        #     )
        # ]
    ),
    showlegend=False,
    margin=dict(l=0, r=0, t=0, b=0)
)

map_figure = go.Figure({
    'data': map_traces,
    'layout': map_layout
})

# # BUILD PAGE LAYOUT
app.layout = html.Div([
                    html.H2(
                        'SERDP Fish/Fire Project',
                        # className='title is-2'
                    ),
                    html.H3(
                        'Explore 8-day MODIS LST with WRF Temps and ACIS Stations',
                        # className='subtitle is-4'
                        ),
                html.Div([
                    html.Div([
                        html.Label('Choose Station', style={'font-weight':'bold'}),
                        dcc.Dropdown(
                            id='station-dropdown',
                            options=[ {'label':i, 'value':j} for i,j in zip(pts.name, pts.name2) ],
                            value='AKFAIRBANKSINTLAP',
                            multi=False
                        ),], className='three columns'),
                    html.Div([ html.Label('Choose WRF Variable', style={'font-weight':'bold'}),
                    dcc.Dropdown(
                        id='variable-dropdown',
                        options=[ {'label':i, 'value':i} for i in ['t2','tsk'] ],
                        value='t2',
                        multi=False
                    ),], className='two columns')
                ], className='row'),
                html.Div([html.Div([
                            dcc.Graph( id='my-graph' ),
                            dcc.RangeSlider(
                                id='range-slider',
                                marks={i:'{}'.format(i) for i in range(2000, 2019+1)},
                                min=2000,
                                max=2019,
                                value=[2004, 2005]
                        )], className="eight columns" ), 
                        html.Div([
                            dcc.Graph(
                                id='map-figure',
                                figure=map_figure 
                            )
                        ], className='four columns')
                ], className='row'),
            ])

@app.callback( Output('my-graph', 'figure'), 
            [Input('station-dropdown', 'value'),
            Input('variable-dropdown', 'value'),
            Input('range-slider', 'value'),])
def update_graph( station_name, wrf_variable, year_range):
    # pull data for the station we want to examine
    begin, end = year_range
    wrf_groups = wrf_max[wrf_variable].keys()
    # wrf-max
    wrf_df_max = pd.concat([wrf_max[wrf_variable][k][station_name] for k in wrf_groups], axis=1)
    wrf_df_max.columns = wrf_groups
    # wrf-min
    wrf_df_min = pd.concat([wrf_min[wrf_variable][k][station_name] for k in wrf_groups], axis=1)
    wrf_df_min.columns = wrf_groups
    # modis
    modis_df = pd.DataFrame({k:modis[k][station_name] for k in modis})
    # stations
    station_df = stations[station_name]
    station_df.name = 'ACIS'
    
    # concat
    df = pd.concat([wrf_df_max,modis_df,station_df], axis=1).loc[str(begin):str(end)]
    # df = pd.concat([modis_df,station_df], axis=1).loc[str(begin):str(end)]
    wrf_dff_max = wrf_df_max.loc[str(begin):str(end)]
    wrf_dff_min = wrf_df_min.loc[str(begin):str(end)]

    # make a plotly json object directly using cufflinks
    title = 'Compare MODIS LST with WRF {} Max\n {}'.format(wrf_variable.upper(), pts[pts.name2 == station_name].name.values[0])
    # fig_cuff = df.copy(deep=True).iplot(title=title, xTitle='8-day MODIS LST Composite', yTitle='Degrees C', asFigure=True)#, rangeslider=True)
    # return fig_cuff.copy().to_plotly_json()
    return { 'data':[ 
                go.Scatter(
                    x=wrf_dff_min['ERA-Interim'].index.tolist()+wrf_dff_max['ERA-Interim'].index.tolist()[::-1],
                    y=wrf_dff_min['ERA-Interim'].tolist()+wrf_dff_max['ERA-Interim'].tolist()[::-1],
                    name='ERA-Interim',
                    fill='tozeroy',
                    # line=dict(color=ms_colors[i[0]][i[1]], width=2),
                    mode='lines'),
                ] + [ \
                go.Scatter(
                    x=df[i].index,
                    y=df[i],
                    name=i,
                    # line=dict(color=ms_colors[i[0]][i[1]], width=2),
                    mode='lines'
                ) for i in ['MOD11A2','MYD11A2','ACIS','GFDL-CM3','NCAR-CCSM4',] ],

            'layout': {
                'title': title,
                'xaxis': dict(title='Year'),
                'yaxis': dict(title='Degrees C')
                }   
            }

@app.callback(Output('station-dropdown', 'value'),
    [Input('map-figure', 'clickData')])
def update_station_dropdown(clickData):
    if clickData is not None:
        station_name, = pts[pts.name == clickData['points'][0]['text']].name2.values
        return station_name
    
    return 'AKFAIRBANKSINTLAP'


if __name__ == '__main__':
    app.run_server( debug=True )
