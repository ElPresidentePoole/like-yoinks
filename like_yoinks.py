#!/usr/bin/env python3

#author_id = 1209853478

import requests
import time

bearer_token = "CHANGE ME TO YOUR BEARER TOKEN"
handle = "CHANGE ME TO YOUR @"

def connect_to_endpoint(url, param_fields='') -> dict:
    print('attempting to connect to endpoint {}'.format(url))
    response = requests.request(
        "GET", url, auth=bearer_oauth, params=param_fields)
    print("response code: {}".format(response.status_code))
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

def bearer_oauth(r) -> None:
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2LikedTweetsPython"
    return r

def get_id_by_handle(handle) -> str:
    # GET /2/users/by
    # this function will only return the last result of the list if there are multiple matches for your handle
    # so make sure your handle matches 100%

    j = connect_to_endpoint("https://api.twitter.com/2/users/by?usernames={}".format(handle))
    return j['data'][-1]['id']

def get_handles_by_ids(list_of_ids) -> dict:
    # Given a list of IDs, return a dictionary containing their handles
    # with a key -> value of id -> handle
    USER_LOOKUP_RATE_LIMIT = 300
    handle_dict = {}

    list_of_lists_of_ids = split_list_into_chunks(list_of_ids, 100)

    times_we_harassed_twitter_api = 0
    for chunk_of_ids in list_of_lists_of_ids:
        # print('https://api.twitter.com/2/users?ids={}'.format(','.join(chunk_of_ids)))
        j = connect_to_endpoint('https://api.twitter.com/2/users?ids={}'.format(','.join(chunk_of_ids)))
        for entry in j['data']:
            handle_dict[entry['id']] = entry['username']
        times_we_harassed_twitter_api += 1
        if times_we_harassed_twitter_api % USER_LOOKUP_RATE_LIMIT == 0:
            print('We gotta take a nap for a bit or else Twitter will rate limit us :(')
            time.sleep(15 * 60 + 30)
    return handle_dict

def get_authors_of_likes(likes_list) -> list:
    # Given a list of likes (see: get_likes_by_id), return all of the author_ids in a list

    authors_of_our_likes = []
    for like in likes_list:
        authors_of_our_likes.append(like['author_id'])
    return authors_of_our_likes

def get_likes_by_id(id) -> list:
    # Given a user's ID, return a list of their likes

    # the default v2 rate limit of fetching likes is 75 per 15 minute interval
    # see: https://developer.twitter.com/en/docs/twitter-api/rate-limits
    LIKE_RATE_LIMIT = 75

    likes_so_far = []
    pages_grabbed = 0
    pagination_token = None
    done_grabbing_likes = False
    while not done_grabbing_likes:
        print('Fetching page', pages_grabbed, '...')
        params = {'tweet.fields': 'author_id'}
        if pagination_token: params['pagination_token'] = pagination_token
        json_response = connect_to_endpoint("https://api.twitter.com/2/users/{}/liked_tweets".format(id), params)
        if 'meta' in json_response and 'next_token' in json_response['meta']:
            pagination_token = json_response['meta']['next_token']
            print('Another page!  Please hold...')
        else:
            done_grabbing_likes = True
        try:
            likes_so_far += json_response['data']
        except KeyError:
            print('KEY ERROR???? WHAT DO YOU MEAN?  json_response LOOKS LIKE THIS!', json_response)
        pages_grabbed += 1
        if pages_grabbed % LIKE_RATE_LIMIT == 0:
            print('We gotta take a nap for a bit or else Twitter will rate limit us :(')
            time.sleep(15 * 60 + 30) # we gotta wait 15 minutes each LIKE_RATE_LIMIT, so, we do.  also i had 30 seconds to make sure we don't have to do this twice.

    #print(likes_so_far)
    return likes_so_far

def get_url_of_tweet(author_id_to_handle_dict, tweet) -> str:
    # Given a dictionary of author_id -> handle and a tweet, try to get their url
    # Twitter's API doesn't give us a url, so we have to rebuild it through a handle and the tweet's id
    author_handle = author_id_to_handle_dict[tweet['author_id']]
    tweet_id = tweet['id']
    return "https://twitter.com/{}/status/{}".format(author_handle, tweet_id)

def split_list_into_chunks(split_me, size_of_chunk) -> list:
    # Given a list of any size, return a list of smaller lists whose len is equal to size_of_chunk

    chunks = []
    for i in range(0, len(split_me), size_of_chunk):
        chunks.append(split_me[i:i+size_of_chunk])
    return chunks

def generate_bookmarks_html(author_id_to_handle_dict, likes) -> None:
    # Given a list of likes, write out a bookmarks.html file that can be imported into Firefox.

    header = """<DL>
    <DT><H3>Twitter</H3></DT>
    <DL>
    """
    footer = """</DL>
    </DL>"""

    with open('bookmarks.html', 'w', encoding='utf-8') as f:
        f.write(header)
        for like in likes:
            url = get_url_of_tweet(author_id_to_handle_dict, like)
            page_title = like['text']
            f.write('<DT><A HREF="{}">{}</A></DT>\n'.format(url, page_title))
        f.write(footer)
    print('Written likes to ./bookmarks.html!')

def generate_likes_txt(author_id_to_handle_dict, likes):
    with open('./likes.txt', 'w') as f:
        for like in likes:
            f.write('{}\n'.format(get_url_of_tweet(author_id_to_handle_dict, like)))
    print('Written likes to ./likes.txt!')

def main() -> None:
    id_of_handle = get_id_by_handle(handle)
    likes = get_likes_by_id(id_of_handle)
    authors_of_our_likes = get_authors_of_likes(likes)
    author_id_to_handle_dict = get_handles_by_ids(authors_of_our_likes)
    generate_likes_txt(author_id_to_handle_dict, likes)
    generate_bookmarks_html(author_id_to_handle_dict, likes)

if __name__ == '__main__':
    main()
