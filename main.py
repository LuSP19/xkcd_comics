import os
from random import randint

import requests
from dotenv import load_dotenv


def get_latest_comic_num():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def download_comic():
    number_of_comics = get_latest_comic_num()
    comic_number = randint(1, number_of_comics)
    url = f'https://xkcd.com/{comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    response = response.json()

    comment = response['alt']

    image_link = response['img']
    response = requests.get(image_link)
    response.raise_for_status()
    with open('comic.png', 'wb') as file:
        file.write(response.content)

    return(comment)


def upload_comic(comics_group_id, vk_access_token, vk_api_version, comment):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id':comics_group_id,
        'access_token':vk_access_token,
        'v': vk_api_version,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    response = response.json()
    with open('comic.png', 'rb') as file:
        url = response['response']['upload_url']
        files = {'photo': file}
        response = requests.post(url, files=files)
        response.raise_for_status()
        response = response.json()

    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params['server'] = response['server']
    params['photo'] = response['photo']
    params['hash'] = response['hash']
    response = requests.get(url, params=params)
    response.raise_for_status()
    response = response.json()

    media_id = response['response'][0]['id']
    owner_id =  response['response'][0]['owner_id']

    url = 'https://api.vk.com/method/wall.post'
    params['owner_id'] = '-' + comics_group_id
    params['from_group'] = '1'
    params['attachments'] = f'photo{owner_id}_{media_id}'
    params['message'] = comment
    response = requests.get(url, params=params)
    response.raise_for_status()


def main():
    load_dotenv()
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    comics_group_id = os.getenv('COMICS_GROUP_ID')
    vk_api_version = '5.131'
    comment = download_comic()
    upload_comic(comics_group_id, vk_access_token, vk_api_version, comment)
    os.remove('comic.png')


if __name__ == '__main__':
    main()
