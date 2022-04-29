# import json
# import os
# import redis
# import time
#
# redis_client = redis.Redis(host='localhost', port=6379)
#
#
# def set_quran_redis():
#     with open(os.getcwd() + '/cogs/data/en_hilali.json', 'r') as f:
#         data = json.load(f)['data']['surahs']
#     for surah in data:
#         for ayah in surah['ayahs']:
#             redis_client.set(str(surah['number']) + "_" + str(ayah['numberInSurah']), ayah['text'])
#
#
#
#
# set_quran_redis()
