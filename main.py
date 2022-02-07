import os
from random import randint

import requests
from dotenv import load_dotenv


def get_latest_comic_num():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def get_random_comic_num():
    number_of_comics = get_latest_comic_num()
    return randint(1, number_of_comics)


def check_for_errors(decoded_response):
    error = decoded_response.get('error')
    if error:
        raise requests.HTTPError(error['error_code'], error['error_msg'])


def download_comic(num):
    url = f'https://xkcd.com/{num}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    decoded_response = response.json()

    comment = decoded_response['alt']

    image_link = decoded_response['img']
    response = requests.get(image_link)
    response.raise_for_status()
    with open('comic.png', 'wb') as file:
        file.write(response.content)

    return comment


def upload_comic(group_id, vk_access_token, vk_api_version):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    decoded_response = response.json()
    check_for_errors(decoded_response)

    upload_url = decoded_response['response']['upload_url']
    with open('comic.png', 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    decoded_response = response.json()
    check_for_errors(decoded_response)

    photo = decoded_response['photo']
    server = decoded_response['server']
    photo_hash = decoded_response['hash']

    return photo, server, photo_hash


def save_comic(
    group_id,
    photo,
    server,
    photo_hash,
    vk_access_token,
    vk_api_version
):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': photo_hash,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    decoded_response = response.json()
    check_for_errors(decoded_response)

    media_id = decoded_response['response'][0]['id']
    owner_id = decoded_response['response'][0]['owner_id']

    return owner_id, media_id


def publish_comic(
    group_id,
    owner_id,
    media_id,
    vk_access_token,
    vk_api_version,
    comic_comment
):
    url = 'https://api.vk.com/method/wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'from_group': '1',
        'attachments': f'photo{owner_id}_{media_id}',
        'message': comic_comment,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    check_for_errors(response.json())


def main():
    load_dotenv()
    group_id = os.getenv('COMICS_GROUP_ID')
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_api_version = '5.131'

    comic_number = get_random_comic_num()
    comic_comment = download_comic(comic_number)

    try:
        photo, server, photo_hash = upload_comic(
            group_id,
            vk_access_token,
            vk_api_version
        )
        owner_id, media_id = save_comic(
            group_id,
            photo,
            server,
            photo_hash,
            vk_access_token,
            vk_api_version
        )
        publish_comic(
            group_id,
            owner_id,
            media_id,
            vk_access_token,
            vk_api_version,
            comic_comment
        )
    finally:
        os.remove('comic.png')


if __name__ == '__main__':
    main()
