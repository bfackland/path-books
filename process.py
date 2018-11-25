from bs4 import BeautifulSoup
from os.path import exists
from PIL import Image
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from pickle import loads, dumps
import logging


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


SOURCE_FOLDER = '/Users/wasl/Documents/Path backups/Path feed forever/'
INDEX_HTML = 'webarchive-index.html'
BASE_DATE = datetime(year=2018, month=10, day=18)
AVERGAGE_DAYS_IN_A_YEAR = 365.25
AVERGAGE_DAYS_IN_A_MONTH = AVERGAGE_DAYS_IN_A_YEAR / 12.0
CARDS_FILENAME = './cards/cards.pickle'


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
        logger.error('COULD NOT PARSE TIMEFRAME:', timeframe)

    return result


def parse_post_info(info):
    location = None

    if info.startswith('Arrived in '):
        _, _, location = info.split(' ', 2)
    elif info.startswith('At ') or info.startswith('In '):
        _, location = info.split(' ', 1)

    return location


def parse_post_emotion(emotion):
    emotion = emotion.lower()

    if emotion not in ['laugh', 'surprise', 'happy', 'sad', 'love', 'comment', 'photo', 'thought']:
        logger.error("COULD NOT PARSE EMOTION:", emotion)

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
        card['image_path'] = None
        if image:
            image_path = '%s%s' % (SOURCE_FOLDER, image['src'])
            image_exists = exists(image_path)
            if image_exists:
                card['image_path'] = image_path
                im = Image.open(card['image_path'])
                im_width, im_height = im.size
                card['image_aspect'] = float(im_width) / float(im_height)

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

        cards.append(card)

    return cards


def score_cards(cards):
    for card in cards:
        score = 0
        for emotion, people in card['emotions'].items():
            if emotion == 'love':
                score += 2 * len(people)
            elif emotion == 'laugh':
                score += 1.5 * len(people)
            elif emotion == 'happy':
                score += 1 * len(people)
        card['score'] = score

    return cards


def store_cards(cards):
    logger.info("Writing cards to: %s" % CARDS_FILENAME)
    data = dumps(cards)
    file = open(CARDS_FILENAME, 'wb')
    file.write(data)
    file.close()


def load_cards():
    logger.info("Loading cards from: %s" % CARDS_FILENAME)
    data = open(CARDS_FILENAME, 'rb').read()
    cards = loads(data)
    return cards


def main():
    if not exists(CARDS_FILENAME):
        logger.info("Parsing posts in HTML and generating cards..")
        soup = BeautifulSoup(open('%s/%s' % (SOURCE_FOLDER, INDEX_HTML)), 'html.parser')
        posts = soup.find_all('div', {'class':'section_feed'})
        cards = parse_posts(posts)
        cards = score_cards(cards)
        store_cards(cards)
    else:
        cards = load_cards()

    page_width = 24.447*cm
    page_height = 20.955*cm
    margin = 2*cm
    pdf = canvas.Canvas('./books/example.pdf', pagesize=(page_width, page_height))

    cards = sorted(cards, key=lambda card: card['score'])
    # reverse to get highest score at the start
    cards.reverse()

    count = 0

    for card in cards:
        # render the page
        if card['poster'] and card['image_path'] and card['image_aspect'] > 1.3:
            logger.debug(card)
            image_aspect = card['image_aspect']

            if image_aspect > 1:
                width = int(page_width - 2*margin)
                height = int(width / image_aspect)
            else:
                height = int(page_height - 3*margin)
                width = int(height * image_aspect)

            pdf.drawImage(image=card['image_path'], x=margin, y=margin*2, width=width, height=height)
            text = "%s (%s)" % (card['poster'], card['score'])
            pdf.drawString(x=margin, y=margin, text=text)

            pdf.showPage()

            card['used'] = True

            count += 1
        
            if count == 20:
                break

    pdf.save()


if __name__ == "__main__":
    main()
