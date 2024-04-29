# coding: utf-8
import dash
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_player
import os
import base64
from test import Video_to_Audio_to_Text,text_to_srt,text_to_translate
from flask import Flask, request, jsonify
from pytube import YouTube
from test import add_subtitle_parallel

UPLOAD_DIRECTORY = "uploads/videos/"
UPLOAD_DIRECTORY_TEXTS = "uploads/texts/"
UPLOAD_DIRECTORY_SRT = "uploads/srt_files/"
DOWNLOAD_DIRECTORY = "/Users/ceyhun/Downloads"


external_stylesheets = ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css', 'assets/style.css']
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)



app.layout = html.Div([
    dcc.Store(id='video-store'),
    html.Div(id='video-uploader-container', children=[
        html.H2("Video Uploader", style={"textAlign": "center"}),
        html.Div([
            dcc.Upload(
                id='upload-video',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '50%',
                    'height': '60px',
                    'lineHeight': '40px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px',
                    'backgroundColor': '#e4dce6',
                    'fontSize': '20px',
                    'cursor': 'pointer',
                    'outline': 'none',
                    'transition': 'border.1s ease-in-out',
                    'borderColor': '#ccc',
                    'padding': '10px',
                    'position':'relative',
                    'marginLeft': '25%',
                },
                multiple=False
            ),
            html.Div([
                dcc.Input(id='url-input', type='text', placeholder='Enter URL',
                          style = {'width': 'calc(60% - 115px)', 'borderRadius': '5px',
                                   'padding': '10px', 'marginRight': '15px', 'fontSize': '20px'}),
                html.Button('Download', id='download-button', className='button-container'),
                html.Div(id='output-div', style = {'margin': '20px 10px', 'fontSize': '14px', 'color': 'green'}),
            ], style = {'display': 'flex', 'flexDirection': 'row',
                        'justifyContent':'flexStart','position':'relative',
                        'marginLeft': '27%'}),
            html.Div(id='video-upload-output'),
            html.Div(id= 'loaded-video-showing', children = [

                html.Div(
                    [
                        html.Div(
                            style={"width": "75%", "padding": "0px"},
                            children=[
                                dcc.Loading(
                                    dash_player.DashPlayer(
                                        id="player",
                                        controls=True,
                                        width="100%",
                                        height="65%",

                                    )),
                                dcc.Checklist(
                                    id="bool-props-radio",
                                    options=[
                                        {"label": val.capitalize(), "value": val}
                                        for val in [
                                            "playing",
                                            "loop",
                                            "controls",
                                            "muted",
                                        ]
                                    ],
                                    value=["controls"],
                                    inline=True,
                                    style={
                                        "display": "flex",
                                        "flexDirection": "row",
                                        "justifyContent": "space-evenly",
                                        "width": "75%",
                                        'visibility': 'hidden',
                                        "margin":"5rem"
                                    },
                                ),

                            ],
                        ),

                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "row",
                        "justifyContent": "space-between",
                        "marginLeft": "15%",

                    },
                ),

            ], style = {'margin':'1rem', 'display': 'none'}),
        ]),
    ]),
    html.Div(id='video-player-container'),

    html.Div(id='audio-uploader-container', children=[
        html.Div ([
            html.H3('Original Voice to Text : '),
            dcc.Loading(
                id = 'text-audio-loading',
                children = [
            dcc.Textarea (
                id='text-audio',
                style={ 'width': '80%', 'height': '300px' }
            )], type="circle" ),
            html.Button('Submit', id='correction-button', className='button-container'),

        ], style = {"marginLeft": "15%",}),
        html.Div([
        html.H3('Translated Text : '),
        html.Div(
        dcc.RadioItems (
            [
                { "label": html.Div (['English'], style={ 'color': '#bd4b75', 'fontSize': 20,'marginLeft': '5px' }), "value": "english" },
                { "label": html.Div (['Français'], style={ 'color': 'blue', 'fontSize': 20,'marginLeft': '5px' }), "value": "french" },
                { "label": html.Div (['Español'], style={ 'color': '#6b296b', 'fontSize': 20,'marginLeft': '5px' }),
                  "value": "spanish" },
                { "label": html.Div (['Deutsch'], style={ 'color': '#c97f34', 'fontSize': 20,'marginLeft': '5px' }), "value": "german" },
            ],
            id='language-radio',
            inline=False,
            style={'display': 'flex', 'flexDirection': 'row', 'margin': '5px', 'justifyContent': 'spaceAround','width': '80%'},
            labelStyle={"display": "flex", "alignItems": "center",'marginLeft': '5px'},
        ))
        ], style = {"marginLeft": "15%",}),
        html.Div ([

            dcc.Loading(
                id = 'translate-audio-loading',
                children =[

            dcc.Textarea (
                id='translate-audio',

                style={ 'width': '80%', 'height': '300px' }
            )], type = 'circle')
        ], style = {"marginLeft": "15%"}),
        html.Div (id = 'hidden-div', children = [], style = {'display': 'none'}),
        html.Div (id = 'hidden-div-2', children = [], style = {'display': 'none'}),
        html.Div (id = 'hidden-div-3', children = [], style = {'display': 'none'}),
        html.Div (id = 'hidden-div-4', children = [], style = {'display': 'none'}),

        html.Div([
            html.Button ('SRT Download', id='srt-download', n_clicks=0,className='button-container',
                         style = { 'backgroundColor': '#ac4baa', 'color': 'white'}
                                  ),
            html.Button ('Add Subtitle', id='adaptation', n_clicks=0,className='button-container',
                         style = {'backgroundColor': '#bb3275', 'color': 'white', }),
            html.Div(id='output-message', style = {'margin': '20px 10px', 'fontSize': '14px', 'color': 'green'}),
            html.Div (id='output-message2',
                      style={ 'margin': '20px 10px',  'fontSize': '14px', 'color': 'green' })
        ],style = {"marginLeft": "15%"})
], style= {'margin': '3rem'})], style = {'backgroundColor' : '#f1f2ed' })


@app.callback(
    [Output('video-store', 'data'),
    Output("loaded-video-showing", "style"),
    Output("bool-props-radio", "style")],

    [Input('upload-video', 'contents')],
    [State('upload-video', 'filename')]
)
def update_uploaded_video(contents, filename):
    if contents is not None:
        return contents, {'display': 'flex', 'flexDirection': 'row', 'margin': '1rem'}, {'visibility': 'visible'}
    else:
        raise PreventUpdate


@app.callback(
     [Output('text-audio', 'value'),
      Output('hidden-div', 'children')],
      Input('upload-video', 'filename'),
     [State('upload-video', 'contents'),
     ]
)
def display_video_upload_message(filename, contents ):

    if contents is not None :
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIRECTORY, filename)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(contents.split(',')[1]))
        result_subs, filepath = Video_to_Audio_to_Text(filepath)
        print("filepath_text", filepath)

        return result_subs, filepath
    else:
        return "", ""





@app.callback(
    Output ('translate-audio', 'value'),
    [
     Input('correction-button', 'n_clicks'),
     Input('language-radio', 'value'),
     State('hidden-div', 'children'),
     State('text-audio', 'value')]
)
def txt_to_translate( nclick, radio_value, filepath, text_value):
    if filepath == [] or nclick == None:
        raise PreventUpdate
    chemin_text_txt = filepath.split ('/')[-1].split ('.')[0] + ".txt"

    chemin_text_file_txt = UPLOAD_DIRECTORY_TEXTS + chemin_text_txt

    if nclick > 0 or radio_value == "english" or radio_value == "french" or \
            radio_value == "spanish" or radio_value == "german":
        return text_to_translate(chemin_text_file_txt, text_value, radio_value)

@app.callback(
    Output('hidden-div-3', 'children'),
    [Input('srt-download', 'n_clicks'),
     Input('hidden-div', 'children')],
)
def txt_to_srt_download(nclicks, filepath):
    if filepath == "":
        raise PreventUpdate
    chemin_text_txt = filepath.split ('/')[-1].split ('.')[0] + ".txt"
    chemin_text_srt = filepath.split ('/')[-1].split ('.')[0] + ".srt"
    chemin_text_file_txt = UPLOAD_DIRECTORY_TEXTS + chemin_text_txt
    chemin_text_file_srt = UPLOAD_DIRECTORY_SRT + chemin_text_srt

    if nclicks > 0 :
        return text_to_srt(chemin_text_file_txt, chemin_text_file_srt)

@app.callback(
    Output('output-message2', 'children'),
    [Input('adaptation', 'n_clicks')],
     [State('hidden-div', 'children'),
     State('language-radio', 'value')]
)
def process_video(n_clicks, filepath, language):

    if filepath == []:
        raise PreventUpdate
    filepath = UPLOAD_DIRECTORY + filepath.split ('/')[-1].split ('.')[0] + ".mp4"
    output_path = UPLOAD_DIRECTORY + filepath.split ('/')[-1].split ('.')[0]+ "_translated"+f"_{language}" + ".mp4"
    if filepath is not None:
        print("filepath", filepath)

        chemin_text_srt = filepath.split ('/')[-1].split ('.')[0] + ".srt"
        chemin_text_file_srt = UPLOAD_DIRECTORY_SRT + chemin_text_srt
    if n_clicks > 0:
        video_path = filepath
        subtitle_path = chemin_text_file_srt
        add_subtitle_parallel(video_path, subtitle_path, output_path)
        return  html.H4('Subtitle has added succesfully!')
    else:
        return ''

@app.callback(
    Output('player', 'url'),
    [Input('video-store', 'data')]
)
def display_video_player(data):
    if data:
        video_url = 'data:video/mp4;base64,{}'.format(data.split(',')[1])
        return video_url


@app.callback(
    Output("player", "playing"),
    Output("player", "loop"),
    Output("player", "controls"),
    Output("player", "muted"),
    Input("bool-props-radio", "value"),
)
def update_bool_props(values):
    playing = "playing" in values
    loop = "loop" in values
    controls = "controls" in values
    muted = "muted" in values
    return playing, loop, controls, muted

@app.callback(
    Output('output-div', 'children'),
    [Input('download-button', 'n_clicks')],
    [State('url-input', 'value')]
)
def download_video(n_clicks, video_url):
    if n_clicks:
        video = YouTube (video_url)
        video = video.streams.get_highest_resolution ()
        try:
            video.download (DOWNLOAD_DIRECTORY)
            return html.H4("Video downloaded successfully")
        except:
            print ("Failed to download video")

    else :
        return None

if __name__ == '__main__':
    app.run_server(debug=True)
