import requests
import logging
import json
import time

logging.basicConfig(level=logging.DEBUG)
#
# async def get_translations(session, url) -> dict:
#     try:
#         async with session.get(url) as resp:
#             data = {"failed": True}
#
#             try:
#                 data = await resp.json()
#             except ContentTypeError:
#                 pass
#             except ClientPayloadError:
#                 print(url)
#                 pass
#
#             return data
#     except TimeoutError:
#         return {}
#     except ServerDisconnectedError:
#         return {}
#
#
# async def start(editions):
#     async with aiohttp.ClientSession() as session:
#         tasks = []
#         for j in editions:
#             tasks.append(asyncio.ensure_future(get_translations(session, f"http://api.alquran.cloud/v1/quran/{j}")))
#             print("Adding task: " + j)
#             await asyncio.sleep(2)
#         results = await asyncio.gather(*tasks)
#         for i in results:
#             if 'code' in i:
#                 if i['code'] == 200:
#                     with open(f"{i['data']['edition']['language']}-{i['data']['edition']['englishName']}", "w+") as f:
#                         json.dump(i['data'], f)
#
#                     if i['data']['edition']['language'] in languages:
#                         languages[i['data']['edition']['language']].append(i['data']['edition']['englishName'])
#                     else:
#                         languages.update({i['data']['edition']['language']: [i['data']['edition']['englishName']]})
#                     content.update({i['data']['edition']['englishName']: i})
#

def set_all_quran_editions():
    editions = requests.get("http://api.alquran.cloud/v1/edition").json()['data']
    logging.info(f"Number of editions: {len(editions)}")
    for i in editions:
        print(i)
    for i in editions:
        time.sleep(0.001)
        try:
            print(f"http://api.alquran.cloud/v1/quran/{i['englishName']}")
            with requests.get(f"http://api.alquran.cloud/v1/quran/{i['englishName']}",
                              headers={'Accept': 'application/json'}) as r:
                if r.status_code == 200:
                    with open(f"{i['language']}-{i['englishName']}", "w+") as f:
                        f.write(r.text.encode('utf-8').decode('utf-8'))
                        pass
                try:
                    print(r.status_code)
                except requests.exceptions.ChunkedEncodingError as ex:
                    print(f"Invalid chunk encoding {str(ex)}")

                print(i['englishName'])

        except KeyError:
            print("Key Error")
            pass
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
            print("Chunk Error")
            pass


set_all_quran_editions()
