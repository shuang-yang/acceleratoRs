import sys
import json
from SearchManager import *
from Utility import *


def search(keyword, searchName, searchKey):
    search_manager = SearchManager(searchName, '2017-11-11',
                                   'https://' + searchName + '.search.windows.net',
                                   searchKey)
    search_manager.run_indexer(Constants.SEARCH_INDEXER_NAME_DEFAULT)
    response = search_manager.search(Constants.SEARCH_INDEX_NAME_DEFAULT, keyword)
    return response.json()


if __name__ == '__main__':
    result = search(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result))
    sys.stdout.flush()
