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
    xkcd_response = requests.get(url)
    xkcd_response.raise_for_status()
    xkcd_decoded_response = xkcd_response.json()

    comment = xkcd_decoded_response['alt']

    image_link = xkcd_decoded_response['img']
    image_request_response = requests.get(image_link)
    image_request_response.raise_for_status()
    with open('comic.png', 'wb') as file:
        file.write(image_request_response.content)

    return comment


def upload_comic(group_id, vk_access_token, vk_api_version):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    upload_url_request_response = requests.get(url, params=params)
    upload_url_request_response.raise_for_status()
    decoded_upload_url_request_response = upload_url_request_response.json()
    check_for_errors(decoded_upload_url_request_response)

    upload_url = decoded_upload_url_request_response['response']['upload_url']
    with open('comic.png', 'rb') as file:
        files = {'photo': file}
        upload_request_response = requests.post(upload_url, files=files)
    upload_request_response.raise_for_status()
    decoded_upload_request_response = upload_request_response.json()
    check_for_errors(decoded_upload_request_response)

    photo = decoded_upload_request_response['photo']
    server = decoded_upload_request_response['server']
    hash = decoded_upload_request_response['hash']

    return photo, server, hash


def save_comic(group_id, photo, server, hash, vk_access_token, vk_api_version):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': hash,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    save_photo_request_response = requests.get(url, params=params)
    save_photo_request_response.raise_for_status()
    decoded_save_photo_request_response = save_photo_request_response.json()
    check_for_errors(decoded_save_photo_request_response)

    media_id = decoded_save_photo_request_response['response'][0]['id']
    owner_id = decoded_save_photo_request_response['response'][0]['owner_id']

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
        'owner_id': '-' + group_id,
        'from_group': '1',
        'attachments': f'photo{owner_id}_{media_id}',
        'message': comic_comment,
        'access_token': vk_access_token,
        'v': vk_api_version,
    }

    publish_comic_request_response = requests.get(url, params=params)
    publish_comic_request_response.raise_for_status()
    check_for_errors(publish_comic_request_response.json())


def main():
    load_dotenv()
    group_id = os.getenv('COMICS_GROUP_ID')
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_api_version = '5.131'

    comic_number = get_random_comic_num()
    comic_comment = download_comic(comic_number)

    photo, server, hash = upload_comic(
        group_id,
        vk_access_token,
        vk_api_version
    )
    owner_id, media_id = save_comic(
        group_id,
        photo,
        server,
        hash,
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

    os.remove('comic.png')


if __name__ == '__main__':
    main()
