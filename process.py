from bs4 import BeautifulSoup
from os.path import exists
from PIL import Image
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


SOURCE_FOLDER = '/Users/wasl/Documents/Path backups/Path feed forever/'
INDEX_HTML = 'webarchive-index.html'
BASE_DATE = datetime(year=2018, month=10, day=18)
AVERGAGE_DAYS_IN_A_YEAR = 365.25
AVERGAGE_DAYS_IN_A_MONTH = AVERGAGE_DAYS_IN_A_YEAR / 12.0


def parse_post_timeframe(timeframe):
    result = None

    if timeframe.lower() == 'a month ago':
        result = BASE_DATE - timedelta(days=AVERGAGE_DAYS_IN_A_MONTH)
    elif timeframe.lower() == 'a year ago':
        result = BASE_DATE - timedelta(days=AVERGAGE_DAYS_IN_A_YEAR)
    else:
        try:
            number, unit, _ = timeframe.split(' ', 2)
            number = int(number)
            if unit.startswith('month'):
                number = number / AVERGAGE_DAYS_IN_A_MONTH
            elif unit.startswith('year'):
                number = number / AVERGAGE_DAYS_IN_A_YEAR
            result = BASE_DATE - timedelta(days=number)
        except:
            pass

    if not result:
        print('COULD NOT PARSE TIMEFRAME:', timeframe)

    return result


def parse_post_info(info):
    location = None

    if info.startswith('Arrived in '):
        _, _, location = info.split(' ', 2)
    elif info.startswith('At ') or info.startswith('In '):
        _, location = info.split(' ', 1)

    return location


def parse_post_emotion(emotion):
    if emotion.lower() not in ['laugh', 'surprise', 'happy', 'sad', 'love', 'comment', 'photo', 'thought']:
        print("COULD NOT PARSE EMOTION:", emotion)

    return emotion


def friendly_name(name):
    if name == 'Anthony':
        return 'Tony'
    if name == 'Rachel':
        return 'Ray'
    if name == 'Lindsey':
        return 'Lin'

    return name


def parse_posts(posts):
    cards = []

    for post in posts:
        card = {
            'emotions' : {},
            'thoughts' : [],
            }

        poster = post.find('a', {'class':'tit_profile'})
        poster = friendly_name(poster.text)
        card['poster'] = poster

        timeframe = post.find('a', {'class':'desc_profile'})
        timeframe = timeframe.text
        date = parse_post_timeframe(timeframe)
        card['date'] = date

        info = post.find('strong', {'class':'tit_feed'})
    
        if info:
            info = info.text
            location = parse_post_info(info)
            if location:
                card['location'] = location

        image = post.find('img', {'class':'img_figure'})
        card['image'] = None
        if image:
            image_path = '%s%s' % (SOURCE_FOLDER, image['src'])
            image_exists = exists(image_path)
            card['image'] = image_path

        empathy = post.find('div', {'class':'panel_empathy'})
        if empathy:
            responses = empathy.find_all('a', {'class':'link_empathy'})
            for response in responses:
                person = response.find('img', {'class':'img_profile'})
                if person:
                    person = friendly_name(person['alt'])
                    emotion = response.find('span', {'class':'ico_path'})
                    if emotion:
                        emotion = emotion.text
                        emotion = parse_post_emotion(emotion)
                        if emotion in card['emotions'].keys():
                            if person not in card['emotions'][emotion]:
                                card['emotions'][emotion].append(person)
                        else:
                            card['emotions'][emotion] = [person, ]

        #     info_cmt = post.find('div', {'class':'info_cmt'})
        #     comment = None
        #     if info_cmt:
        #         cont_cmt = info_cmt.find('span', {'class':'cont_cmt'})
        #         if cont_cmt:
        #             spans = cont_cmt.find_all('span')
        #             for span in spans:
        #                 sub_span = span.find('span')
        #                 if sub_span:
        #                     comment = sub_span.text
        #                     print(comment)
        #                     break

        desc_thought = post.find('p', {'class':'desc_thought'})
        thought = None
        if desc_thought:
            spans = desc_thought.find_all('span')
            for span in spans:
                sub_span = span.find('span')
                if sub_span:
                    thought = sub_span.text
                    card['thoughts'].append(thought)
                    break

        print(card)
        cards.append(card)

    return cards


def main():
    soup = BeautifulSoup(open('%s/%s' % (SOURCE_FOLDER, INDEX_HTML)), 'html.parser')
    posts = soup.find_all('div', {'class':'section_feed'})[:10]
    cards = parse_posts(posts)

    page_width = 24.447*cm
    page_height = 20.955*cm
    margin = 2*cm
    page = canvas.Canvas('./books/example.pdf', pagesize=(page_width, page_height))

    for card in cards:
        # render the page
        if card['poster'] and card['image']:
            page.drawString(x=margin, y=margin, text=card['poster'])
            im = Image.open(card['image'])

            im_width, im_height = im.size
            im_aspect = float(im_width) / float(im_height)
            if im_aspect > 1:
                width = int(page_width - 2*margin)
                height = int(width / im_aspect)
            else:
                height = int(page_height - 3*margin)
                width = int(height * im_aspect)

            page.drawImage(image=card['image'], x=margin, y=margin*2, width=width, height=height)
            page.showPage()

    page.save()


if __name__ == "__main__":
    main()
