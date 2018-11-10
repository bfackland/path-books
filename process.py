from bs4 import BeautifulSoup
from os.path import exists
from PIL import Image


SOURCE_FOLDER = '/Users/wasl/Documents/Path backups/Path feed forever/'
INDEX_HTML = 'webarchive-index.html'


soup = BeautifulSoup(open('%s/%s' % (SOURCE_FOLDER, INDEX_HTML)), 'html.parser')
posts = soup.find_all('div', {'class':'section_feed'})[:3]


for post in posts:
    poster = post.find('a', {'class':'tit_profile'})
    if poster:
        poster = poster.text
    date = post.find('a', {'class':'desc_profile'})
    if date:
        date = date.text
    info = post.find('strong', {'class':'tit_feed'})
    if info:
        info = info.text
    print(poster, date, info)

    image = post.find('img', {'class':'img_figure'})
    if image:
        image_path = '%s%s' % (SOURCE_FOLDER, image['src'])
        image_exists = exists(image_path)
        print(image_path, image_exists)
        if image_exists:
            im = Image.open(image_path)

    empathy = post.find('div', {'class':'panel_empathy'})
    if empathy:
        responses = empathy.find_all('a', {'class':'link_empathy'})
        for response in responses:
            person = response.find('img', {'class':'img_profile'})
            if person:
                person = person['alt']
            emotion = response.find('span', {'class':'ico_path'})
            if emotion:
                emotion = emotion.text
            print(person, emotion)
        
#    import pdb; pdb.set_trace()
