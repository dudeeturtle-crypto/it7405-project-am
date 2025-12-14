from django.test import Client

client = Client()
url = '/movies/gladiator/'
resp = client.get(url)
text = resp.content.decode('utf-8', errors='ignore')
print('URL:', url)
print('Status code:', resp.status_code)
print("Contains title 'Gladiator':", 'Gladiator' in text)
print("Contains rating '4.7':", '4.7' in text)
# try common poster hosts
print("Contains 'imdb' or 'cloudfront' or 'amazon':", any(h in text for h in ['imdb', 'cloudfront.net', 'amazon']))
if 'Gladiator' in text:
    i = text.find('Gladiator')
    print('Snippet around title:', text[max(0,i-80):i+80])
