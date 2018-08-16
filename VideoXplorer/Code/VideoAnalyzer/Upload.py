
from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import os
import sys
# from wordcloud import WordCloud
from Models import *
from Utility import *
from Analyzers import *
from DataSourceManagers import *
from DatabaseManager import *
from SearchManager import *
# from sumy.parsers.plaintext import PlaintextParser
# from sumy.nlp.tokenizers import Tokenizer
# from sumy.summarizers.lsa import LsaSummarizer
# from sumy.nlp.stemmers import Stemmer
# from sumy.utils import get_stop_words
from threading import Thread, Semaphore

CONFIDENCE_THRESHOLD = 0.5

blobAccountNameDefault = 'videoanalyserstorage'
blobAccountKeyDefault = '0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w=='
cosmosdbEndpointDefault = 'https://video-analyzer-db.documents.azure.com:443/'
cosmosdbMasterkeyDefault = 'VREFPwEbkjNwRji7XaIjbauu2ElUc9TBgEWQsJ4OnuYJYPuHUlfD1Ru2zprjQRvKHWCouxDIbbMAt06tXKk8kA=='
cvKeyDefault = "c49f0b5b59654ca28e3fec02d015c60f"
cvURLDefault = "https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/"
azureSearchNameDefault = "video-analyzer-search"
azureSearchKeyDefault = '40BCFD3875D09243AB49A3175FE9AD99'
startTimeDefault = 0
endTimeDefault = 60
sampleRateDefault = 10000
videoFileRootPathDefault = './data/'
videoFileNameDefault = 'CarCrash.mp4'


db_config = {
    "ENDPOINT": cosmosdbEndpointDefault,
    "MASTERKEY": cosmosdbMasterkeyDefault
}


def create_blob_manager(account_name=blobAccountNameDefault, account_key=blobAccountKeyDefault):
    blob = BlobManager(account_name=account_name,
                       account_key=account_key)
    # blob.clear()
    blob.create_container('video')
    blob.create_container('image')
    blob.create_container('audio')
    return blob


# def generate_word_clouds_from_frames(video_data):
#     # Obtain top n keywords
#     top_keywords = video_data.top_keywords_from_frames(10)
#     top_caption_keywords = video_data.top_caption_keywords_from_frames(10)
#     # Generate wordcloud
#     font_path = 'Symbola.ttf'
#     word_cloud = WordCloud(background_color="white", font_path=font_path).generate_from_frequencies(dict(top_keywords))
#     word_cloud.to_file('Suntec_tags_word_cloud.jpg')
#     word_cloud = WordCloud(background_color="white", font_path=font_path).generate_from_frequencies(
#         dict(top_caption_keywords))
#     word_cloud.to_file('Suntec_captions_word_cloud.jpg')


def analyze_frames(blob, frame_list, image_analyzer, filename, db_manager, video_id, video_url, user_id):
    docs = []

    # Obtain a list of analyses based on the sampled frames asynchronously
    urls = [frame.url for frame in frame_list]
    analyses = image_analyzer.analyze_remote_by_batch(urls)

    # Add Image analyses result to frames
    image_data_list = map(lambda x: image_analyzer.convert_to_image_data(x), analyses)
    frame_to_data_list = list(zip(frame_list, image_data_list))

    for frame, image_data in frame_to_data_list:
        # Set image_data of frames
        frame.set_image_data(image_data)

        # Create Unique Cosmos DB ID
        new_id = str(video_id) + '_' + str(frame.video_time)

        # Add db_entry based on image_data of the frame
        # TODO - consider using Collection instead of joining them all in a string
        tags =','.join(image_data.tags)
        captions = ','.join([caption[0] for caption in image_data.captions if caption[1] >= Constants.CONFIDENCE_THRESHOLD ])
        celebrities = ','.join([celebrity[0] for celebrity in image_data.celebrities if celebrity[1] >= Constants.CONFIDENCE_THRESHOLD])
        landmarks = ','.join([landmark[0] for landmark in image_data.landmarks if landmark[1] >= Constants.CONFIDENCE_THRESHOLD])
        categories = ','.join([category[0] for category in image_data.categories if category[1] >= Constants.CONFIDENCE_THRESHOLD])
        dominant_colors = ','.join(image_data.dominant_colors)

        doc = {'id': new_id, 'user_id': user_id, 'video_id': video_id, 'video_url': video_url, 'filename': filename,
               'index': frame.index, 'time': frame.video_time, 'std_time': frame.video_time_std, 'url': frame.url,
               'tags': tags, 'captions': captions, 'categories': categories, 'celebrities': celebrities, 'landmarks': landmarks,
               'dominant_colors': dominant_colors, 'foreground_color': image_data.foreground_color, 'background_color': image_data.background_color,
               'accent_color': image_data.accent_color, 'isBwImg': image_data.isBwImg, 'height': image_data.height, 'width': image_data.width}

        query = {
            "query": "SELECT * FROM r WHERE r.filename=@filename AND r.time=@time",
            "parameters": [
                {"name": "@filename", "value": filename},
                {"name": "@time", "value": frame.video_time}
            ]
        }

        existing_docs = db_manager.query_doc(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, query)
        if len(existing_docs) != 0:
            db_manager.replace_doc(existing_docs[0], doc)
        else:
            db_entry = db_manager.create_doc(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, doc)
            frame.set_db_entry(db_entry)
        docs.append(doc)
    return docs


def analyze_faces(blob, frame_list, face_analyzer, filename, db_manager, video_id, video_url, docs):
    # Obtain a list of analyses based on the grabbed frames
    urls = [frame.url for frame in frame_list]
    analyses = face_analyzer.analyze_remote_by_batch(urls)

    # Add Image analyses result to frames
    face_data_lists = map(lambda x: face_analyzer.convert_to_face_data(x), analyses)
    frame_to_face_data_list = list(zip(frame_list, face_data_lists, docs))
    for frame, face_data_list, doc in frame_to_face_data_list:
        frame.set_face_data_list(face_data_list)
        dominant_emotions =',',join(frame.get_predominant_emotions(3))
        output_file.write('\n\n')
    output_file.close()


def summerize_captions(filename_no_extension):
    filepath = os.path.join(videoFileRootPath + 'Output_captions_', filename_no_extension + '.txt')
    parser = PlaintextParser.from_file(filepath, Tokenizer("english"))
    stemmer = Stemmer("english")
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words("english")
    for sentence in summarizer(parser.document, 5):
        print(sentence)


def init_analyzers(videoFileRootPath, cv_key, cv_url):
    image_analyzer = ImageAnalyzer(cv_key,
                                   cv_url, videoFileRootPath, 9)
    face_analyzer = FaceAnalyzer("7854c9ad29294ce89d2142ac0977b194",
                                 "https://southeastasia.api.cognitive.microsoft.com/face/v1.0/detect", videoFileRootPath, 9)
    text_analyzer = TextAnalyzer("5105a7087a364ba4a3b9467ca9f094ce",
                                 "https://southeastasia.api.cognitive.microsoft.com/text/analytics/v2.0/", videoFileRootPath)
    return image_analyzer, face_analyzer, text_analyzer


def get_caption_as_text(video_data, filename, db_manager, db_entry, video_file_rootpath):
    output_file = open(video_file_rootpath + "Output_captions_" + filename + ".txt", "w")
    captions = video_data.get_captions_as_text_trimmed()
    output_file.write(captions)
    db_entry['captions'] = captions
    db_manager.replace_doc(db_entry, db_entry)
    output_file.close()
    return captions


def extract_keywords_from_captions(text_analyzer, filename_no_extension, db_manager, db_entry, videoFileRootPath):
    filename = 'Output_captions_' + filename_no_extension + '.txt'
    analysis = text_analyzer.analyze_local(filename,
                                           TextAnalyticsService.KEY_PHRASES.value)
    # Add key phrases to db
    key_phrases = ', '.join(analysis['documents'][0]['keyPhrases'])
    db_entry['caption_keywords'] = key_phrases
    db_manager.replace_doc(db_entry, db_entry)
    return key_phrases


def extract_keywords_from_tags(video_data, db_manager, db_entry, num):
    top_frequent_tags = video_data.top_keywords_from_tags(num)
    keywords_string = ""
    for tag in top_frequent_tags:
        keywords_string += tag[0] + ", "
    db_entry['tags_keywords'] = keywords_string
    db_manager.replace_doc(db_entry, db_entry)
    return keywords_string


def extract_dominant_colors(video_data, db_manager, db_entry, num):
    dominant_colors_str = ""
    dominant_colors = video_data.get_dominant_colors(num)
    for color in dominant_colors:
        dominant_colors_str += color[0] + ', '
    db_entry['dominant_colors'] = dominant_colors_str
    db_manager.replace_doc(db_entry, db_entry)
    return dominant_colors_str


def extract_colors(video_data, db_manager, db_entry, num):
    foreground_colors_str = ""
    background_colors_str = ""
    ascent_colors_str = ""
    f_colors, b_colors, a_colors = video_data.get_colors(num)
    for color in f_colors:
        foreground_colors_str += color[0] + ', '
    for color in b_colors:
        background_colors_str += color[0] + ', '
    for color in a_colors:
        ascent_colors_str += color[0] + ', '
    db_entry['dominant_foreground_color'] = foreground_colors_str
    db_entry['dominant_background_color'] = background_colors_str
    db_entry['dominant_accent_color'] = ascent_colors_str
    db_manager.replace_doc(db_entry, db_entry)
    return foreground_colors_str, background_colors_str, ascent_colors_str


def extract_celebrities(video_data, db_manager, db_entry):
    celebrities_str = ""
    celebrities = video_data.get_celebrities()
    for celeb in celebrities:
        celebrities_str += celeb + ', '
    db_entry['celebrities'] = celebrities_str
    db_manager.replace_doc(db_entry, db_entry)
    return celebrities_str


def extract_landmarks(video_data, db_manager, db_entry):
    landmarks_str = ""
    landmarks = video_data.get_landmarks()
    for lm in landmarks:
        landmarks_str += lm + ', '
    db_entry['landmarks'] = landmarks_str
    db_manager.replace_doc(db_entry, db_entry)
    return landmarks_str


def analyze_video(filename, cv_key, cv_url, start, end, sampling_type, sampling_rate, blob_manager, video_manager, db_manager, video_file_rootpath, userId):

    # Initiate Analyzers
    image_analyzer, face_analyzer, text_analyzer = init_analyzers(video_file_rootpath, cv_key, cv_url)

    # Upload Video
    video_url = video_manager.upload_to_blob(os.path.join(video_manager.curr_dir, filename), 'video')

    # Generate Filename
    filename_no_extension = os.path.splitext(filename)[0]

    # Generate new CosmosDB id
    mutex = Semaphore(1)
    mutex.acquire()
    new_video_id = db_manager.get_next_id(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)
    mutex.release()

    # Create CosmosDB entry for the summarized info of the video
    doc_summarized = {'id': str(new_video_id), 'user_id': userId, 'name': filename_no_extension, 'start_time': start, 'end_time': end, 'sample_rate': sampling_rate}
    db_entry_summarized = db_manager.create_doc(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, doc_summarized)

    # Generate a list of frames
    frame_list = video_manager.grab_frames(filename, start, end, sampling_type, sampling_rate)

    # Analyze frames with Computer Vision API
    analyze_frames(blob_manager, frame_list, image_analyzer, filename_no_extension, db_manager, new_video_id, video_url, userId)

    # Analyze frames with Face API
    # analyze_faces(blob_manager, frame_list, face_analyzer, filename_no_extension, db_manager, new_video_id, video_url)

    # Generate a VideoData object from the list of frames
    video_data = VideoData(frame_list)

    # Extract most frequent keywords from captions
    captions = get_caption_as_text(video_data, filename_no_extension, db_manager, db_entry_summarized, video_file_rootpath)
    caption_keywords = extract_keywords_from_captions(text_analyzer, filename_no_extension, db_manager, db_entry_summarized, video_file_rootpath)

    # Extract most frequent keywords from tags
    tags_keywords = extract_keywords_from_tags(video_data, db_manager, db_entry_summarized, 10)

    # Extract most dominant colors of the video
    dominant_colors = extract_dominant_colors(video_data, db_manager, db_entry_summarized, 3)
    celebrities = extract_celebrities(video_data, db_manager, db_entry_summarized)
    landmarks = extract_landmarks(video_data, db_manager, db_entry_summarized)

    return new_video_id, filename_no_extension, video_url


def batch_analyze_video(filename, cv_key, cv_url, start, end, sampling_type, sampling_rate, blob_manager, video_manager, db_manager, video_file_rootpath, output_file):

    # Initiate Analyzers
    image_analyzer, face_analyzer, text_analyzer = init_analyzers(video_file_rootpath, cv_key, cv_url)

    # Upload Video
    video_url = video_manager.upload_to_blob(os.path.join(video_manager.curr_dir, filename), 'video')

    # Generate Filename
    filename_no_extension = os.path.splitext(filename)[0]

    # Generate new CosmosDB id
    mutex = Semaphore(1)
    mutex.acquire()
    new_video_id = db_manager.get_next_id(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)
    mutex.release()

    # Create CosmosDB entry
    doc_summarized = {'id': str(new_video_id), 'name': filename_no_extension}
    db_entry_summarized = db_manager.create_doc(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, doc_summarized)

    # Generate a list of frames
    frame_list = video_manager.grab_frames(filename, start, end, sampling_type, sampling_rate)

    # Analyze frames with Computer Vision API
    analyze_frames(blob_manager, frame_list, image_analyzer, filename_no_extension, db_manager, new_video_id, video_url)

    # Analyze frames with Face API
    # analyze_faces(blob_manager, frame_list, face_analyzer, filename_no_extension, db_manager)

    # Generate a VideoData object from the list of frames
    video_data = VideoData(frame_list)

    # Extract most frequent keywords from captions
    captions = get_caption_as_text(video_data, filename_no_extension, db_manager, db_entry_summarized, video_file_rootpath)
    caption_keywords = extract_keywords_from_captions(text_analyzer, filename_no_extension, db_manager, db_entry_summarized, video_file_rootpath)

    # Extract most frequent keywords from tags
    tags_keywords = extract_keywords_from_tags(video_data, db_manager, db_entry_summarized, 10)

    # Extract most dominant colors of the video
    dominant_colors = extract_dominant_colors(video_data, db_manager, db_entry_summarized, 3)
    celebrities = extract_celebrities(video_data, db_manager, db_entry_summarized)
    landmarks = extract_landmarks(video_data, db_manager, db_entry_summarized)
    fore_colors, back_colors, acc_colors = extract_colors(video_data, db_manager, db_entry_summarized, 2)

    output_file.write(str(new_video_id) + ' ; ' + filename_no_extension + ' ; ' + caption_keywords + ' ; ' +
                      tags_keywords + ' ; ' + dominant_colors + ' ; ' + fore_colors + ' ; ' + back_colors + ' ; ' +
                      acc_colors + ' ; ' + celebrities + ' ; ' + landmarks + '\n')


def search(keyword):
    search_manager = SearchManager("video-analyzer-search", "2017-11-11",
                                   'https://video-analyzer-search.search.windows.net',
                                   '40BCFD3875D09243AB49A3175FE9AD99')
    response = search_manager.search(Constants.SEARCH_INDEX_NAME_DEFAULT, keyword)
    return response.json()


def run(blobAccountName,
        blobAccountKey,
        cosmosdbEndpoint,
        cosmosdbMasterkey,
        cvKey,
        cvURL,
        azureSearchName,
        azureSearchKey,
        startTime,
        endTime,
        sampleRate,
        videoFileRootPath,
        videoFileName,
        userId):

    try:
        # Clears any legacy files
        clear_local_files(videoFileRootPath)

        # Initialze Azure Blob Storage managers
        blob_manager = create_blob_manager(blobAccountName, blobAccountKey)

        # Initialze Video Manager
        video_manager = VideoManager(videoFileRootPath, blob_manager)

        # Initialze Cosmos DB Manager
        db_manager = DBManager(cosmosdbEndpoint, cosmosdbMasterkey)

        # Create output cosmos DB for both video and extracted info from video
        db_videos = db_manager.read_database(Constants.DB_NAME_VIDEOS) if len(
            db_manager.find_databases(Constants.DB_NAME_VIDEOS)) != 0 \
            else db_manager.create_database(Constants.DB_NAME_VIDEOS)
        db_frames = db_manager.read_database(Constants.DB_NAME_FRAMES) if len(
            db_manager.find_databases(Constants.DB_NAME_FRAMES)) != 0 \
            else db_manager.create_database(Constants.DB_NAME_FRAMES)

        collection_videos = db_manager.read_collection(Constants.DB_NAME_VIDEOS,
                                                       Constants.COLLECTION_NAME_DEFAULT) if len(
            db_manager.find_collections(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
            else db_manager.create_collection(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, True, "V2",
                                              400)
        collection_frames = db_manager.read_collection(Constants.DB_NAME_FRAMES,
                                                       Constants.COLLECTION_NAME_DEFAULT) if len(
            db_manager.find_collections(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
            else db_manager.create_collection(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, True, "V2",
                                              400)

        # Analyze video with specified parameters: start time, end time, sampling rate
        video_id, video_name, video_url = analyze_video(videoFileName, cvKey, cvURL, start=startTime, end=endTime, sampling_type=GrabRateType.BY_SECOND,
                                             sampling_rate=sampleRate, blob_manager=blob_manager, video_manager=video_manager,
                                             db_manager=db_manager, video_file_rootpath=videoFileRootPath, userId=userId)

        # Search using Azure Search
        search_manager = SearchManager(azureSearchName, "2017-11-11",
                                       'https://' + azureSearchName + '.search.windows.net',
                                       azureSearchKey)
        search_manager.create_data_source(Constants.SEARCH_DATASOURCE_NAME_DEFAULT,
                                          "AccountEndpoint=" + cosmosdbEndpoint + ";AccountKey=" + cosmosdbMasterkey + ";Database=" + str(
                                              db_frames['id']),
                                          str(collection_frames['id']), None)
        search_manager.create_index(Constants.SEARCH_INDEX_NAME_DEFAULT)
        search_manager.create_indexer(Constants.SEARCH_INDEXER_NAME_DEFAULT, Constants.SEARCH_DATASOURCE_NAME_DEFAULT,
                                      Constants.SEARCH_INDEX_NAME_DEFAULT)
        search_manager.run_indexer(Constants.SEARCH_INDEXER_NAME_DEFAULT)
        # search_manager.get_indexer_status(Constants.SEARCH_INDEXER_NAME_DEFAULT)

        clear_local_files(videoFileRootPath)

        print(video_id)
        print(video_name)
        print(video_url)
        sys.stdout.flush()
    except Exception as e:
        print(e.args)

def batch_run():
    dir = './FrontEnd/public/videos/7/'
    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(dir) if isfile(join(dir, f)) and 'mp4' in f]

    clear_local_files(dir)
    blob_manager = create_blob_manager(blobAccountNameDefault, blobAccountKeyDefault)
    video_manager = VideoManager(dir, blob_manager)
    db_manager = DBManager(cosmosdbEndpointDefault, cosmosdbMasterkeyDefault)
    db_videos = db_manager.read_database(Constants.DB_NAME_VIDEOS) if len(
        db_manager.find_databases(Constants.DB_NAME_VIDEOS)) != 0 \
        else db_manager.create_database(Constants.DB_NAME_VIDEOS)
    db_frames = db_manager.read_database(Constants.DB_NAME_FRAMES) if len(
        db_manager.find_databases(Constants.DB_NAME_FRAMES)) != 0 \
        else db_manager.create_database(Constants.DB_NAME_FRAMES)
    collection_videos = db_manager.read_collection(Constants.DB_NAME_VIDEOS,
                                                   Constants.COLLECTION_NAME_DEFAULT) if len(
        db_manager.find_collections(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
        else db_manager.create_collection(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, True, "V2",
                                          400)
    collection_frames = db_manager.read_collection(Constants.DB_NAME_FRAMES,
                                                   Constants.COLLECTION_NAME_DEFAULT) if len(
        db_manager.find_collections(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
        else db_manager.create_collection(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, True, "V2",
                                          400)

    output_file = open(dir + "Metadata.txt", "w")
    # output_file.write('video_id ; video_name ; caption_keywords ; tag_keywords ; dominant_colors ; foreground_colors ; background_colors ; accent_colors ; celebrities ; landmarks\n')
    for file in files:
        batch_analyze_video(file, cvKeyDefault, cvURLDefault, start=0, end=60,
                                                        sampling_type=GrabRateType.BY_SECOND,
                                                        sampling_rate=2000, blob_manager=blob_manager,
                                                        video_manager=video_manager,
                                                        db_manager=db_manager, video_file_rootpath=dir, output_file=output_file)
        clear_local_files(dir)

# def cluster_analysis():
#     import pandas as pd
#     data = pd.read_csv('final_output.csv')
#     data['topic'] = data[['T0', 'T1', 'T2', 'T3']].idxmax(axis=1)
#     print(data)
#     header = ["video_name", "topic"]
#     data.to_csv('out.csv', columns=header)
#     for i in range(4):
#         font_path = 'Symbola_hint.ttf'
#         wordcloud = WordCloud(background_color="white", font_path=font_path).generate(
#             ' '.join(data[data.topic == 'T' + str(i)]['tag_keywords']))
#         wordcloud.to_file('wordcloud' + str(i) + '.jpg')

# Main Execution Body
if __name__ == '__main__':
    blobAccountName = sys.argv[1]
    blobAccountKey = sys.argv[2]
    cosmosdbEndpoint = sys.argv[3]
    cosmosdbMasterkey = sys.argv[4]
    cvKey = sys.argv[5]
    cvURL = sys.argv[6]
    azureSearchName = sys.argv[7]
    azureSearchKey = sys.argv[8]
    startTime = int(sys.argv[9])
    endTime = int(sys.argv[10])
    sampleRate = int(sys.argv[11])
    videoFileRootPath = sys.argv[12]
    videoFileName = sys.argv[13]
    userId = sys.argv[14]

    run(blobAccountName, blobAccountKey, cosmosdbEndpoint, cosmosdbMasterkey, cvKey, cvURL,
        azureSearchName, azureSearchKey, startTime, endTime, sampleRate, videoFileRootPath, videoFileName, userId)

    sys.stdout.flush()
    # run(blobAccountNameDefault, blobAccountKeyDefault, cosmosdbEndpointDefault, cosmosdbMasterkeyDefault, cvKeyDefault, cvURLDefault,
    #     azureSearchNameDefault, azureSearchKeyDefault, startTimeDefault, endTimeDefault, sampleRateDefault,
    #     'data/', 'JO.mp4', '1')





