import sys
import json
from SearchManager import *
from Utility import *

def search(keyword, video_id, searchName='video-analyzer-search', searchKey='40BCFD3875D09243AB49A3175FE9AD99'):
    search_manager = SearchManager(searchName, '2017-11-11',
                                   'https://' + searchName + '.search.windows.net',
                                   searchKey)
    search_manager.run_indexer('frame-indexer')
    filter = "filename eq '" + video_id + "'"
    response = search_manager.search_with_filter('frame-index', keyword, filter)
    return response.json()


if __name__ == '__main__':
    if sys.argv[3] is not '':
        result = search(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        result = search(sys.argv[1], sys.argv[2])
    print(json.dumps(result))
    sys.stdout.flush()
