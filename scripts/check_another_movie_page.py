from django.test import Client

client = Client()
url = '/movies/another-movie/'
resp = client.get(url)
text = resp.content.decode('utf-8', errors='ignore')
print('URL:', url)
print('Status code:', resp.status_code)
print("Contains title 'Another':", 'Another' in text)
print("Contains rating '2.3':", '2.3' in text)
print("Contains photo host 'cloudfront.net':", 'cloudfront.net' in text)
if 'Another' in text:
    i = text.find('Another')
    print('Snippet around title:', text[max(0,i-80):i+80])
