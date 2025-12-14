from django.test import Client

client = Client()
url = '/movies/example-movie/'
resp = client.get(url)
text = resp.content.decode('utf-8', errors='ignore')
print('URL:', url)
print('Status code:', resp.status_code)
print("Contains title 'Rush Hour':", 'Rush Hour' in text)
print("Contains rating '4.9':", '4.9' in text)
print("Contains photo host 'tse3.mm.bing.net':", 'tse3.mm.bing.net' in text)
# print a small snippet around title if present
if 'Rush Hour' in text:
    i = text.find('Rush Hour')
    print('Snippet around title:', text[max(0,i-60):i+60])
