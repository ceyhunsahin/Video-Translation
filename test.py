
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
import whisper
import os
import base64
from transformers import pipeline
import pandas as pd
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from moviepy.editor import VideoFileClip, TextClip, concatenate_videoclips
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator
from deep_translator import DeeplTranslator,single_detection
from dotenv import load_dotenv
load_dotenv()


UPLOAD_DIRECTORY = "uploads/videos/"
UPLOAD_DIRECTORY_AUDIOS = "uploads/audios/"
UPLOAD_DIRECTORY_TEXTS = "uploads/texts/"
UPLOAD_DIRECTORY_TRANSLATED = "uploads/translated/"


DEEPL_API = os.getenv("DEEPL_API_KEY")
SINGLE_DETECTION_API = os.getenv("SINGLE_DETECTION_API_KEY")

def Video_to_Audio_to_Text(chemin_video):
    """
    Convert a video to audio
    """



    chemin_audio = chemin_video.split('/')[-1].split('.')[0] + ".mp3"
    chemin_text = chemin_video.split ('/')[-1].split ('.')[0] + ".txt"
    chemin_text_file = UPLOAD_DIRECTORY_TEXTS+chemin_text

    video = VideoFileClip (chemin_video)
    son = video.audio

    son.write_audiofile (UPLOAD_DIRECTORY_AUDIOS+chemin_audio )
    video.close ()


    used_model1 = 'large'

    model = whisper.load_model (used_model1)

    result = model.transcribe (UPLOAD_DIRECTORY_AUDIOS + chemin_audio)
    filepath_audio = os.path.join (UPLOAD_DIRECTORY_AUDIOS, chemin_audio)
    print('1. result', result)

    first_text_segments = []
    timestamps_start = []
    timestamps_end = []
    id_params = []
    for segment in result['segments']:
        first_text_segments.append (segment['text'])
        timestamps_start.append (segment['start'])
        timestamps_end.append (segment['end'])
        id_params.append (segment['id'])

        df = pd.DataFrame(list(zip(id_params, first_text_segments, timestamps_start, timestamps_end)), columns=['id','text','start', 'end'])
        #df = df.drop_duplicates(subset=['text'])
        df.to_csv(chemin_text_file, sep='\t', index=False, header=False)

    return '\n'.join(df['text']), filepath_audio



def text_to_translate(input_text_file,  text_value, radio_value="en"):
    df = pd.read_csv(input_text_file, sep='\t', header=None)
    if len(df.columns) == 4:
        df.columns = ['id', 'text','start', 'end']
    else :
        df.columns = ['text', 'start', 'end']
    print('text_value', text_value)
    texts = text_value.strip().split('\n')

    language = "fr" if radio_value == "french" else "es" if radio_value == "spanish" else "en" if radio_value == "english" else "de"
    detected_lang = single_detection(df['text'][0], api_key=SINGLE_DETECTION_API)

    new_translations = []
    print('detected_lang', detected_lang)
    print('language', language)
    for text in texts:
        result = DeeplTranslator(api_key=DEEPL_API, source=detected_lang, target=language, use_free_api=True).translate(text)
        new_translations.append (result)
    df['translated_text'] = new_translations

    output_path = input_text_file.replace ('.txt', '_translated.txt')
    df[['translated_text', 'start', 'end']].to_csv (input_text_file, sep='\t', index=False, header=False)
    return '\n'.join(df['translated_text'])



def text_to_srt(input_text_file, output_srt_file):
    df = pd.read_csv(input_text_file, sep='\t', header=None)
    df.columns = ['translated_text','start', 'end']
    with open (output_srt_file, 'w') as f:
        for index, row in df.iterrows ():
            f.write (f"{index + 1}\n")
            f.write (f"{convert_to_srt_time (row['start'])} --> {convert_to_srt_time (row['end'])}\n")
            f.write (f"{row['translated_text']}\n\n")


def add_subtitle_parallel(video_path, subtitle_path, output_path, num_workers=4):
    video = VideoFileClip(video_path)
    subtitles = SubtitlesClip(subtitle_path, lambda txt: TextClip(txt, fontsize=28, stroke_width=3, method='caption',
                                                                  align='south', size=video.size, font='Arial',
                                                                  color='yellow2'))

    # to chunks
    duration = video.duration
    chunk_size = duration / num_workers

    #  ThreadPoolExecutor for processing chunks
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        for i in range(num_workers):
            start_time = i * chunk_size
            end_time = min((i + 1) * chunk_size, duration)
            video_chunk = video.subclip(start_time, end_time)
            subtitle_chunk = subtitles.subclip(start_time, end_time)

            futures.append(executor.submit(add_subtitle_to_chunk, video_chunk, subtitle_chunk))
        results = [future.result() for future in futures]

    # chunks combination
    result = concatenate_videoclips(results)
    result = result.set_audio (video.audio)
    # result recording
    result.write_videofile(output_path, fps=video.fps, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)

def add_subtitle_to_chunk(video_chunk, subtitle_chunk):
    # adding subtitles to the video
    return CompositeVideoClip([video_chunk.set_audio(None), subtitle_chunk.set_pos(('center', 'bottom'))])
def convert_to_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


