import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('cinemapark.db')
cursor=conn.cursor()

import requests
from bs4 import BeautifulSoup
import re

def remove_all(string):
    pattern = re.compile(r'[А-Яа-яёЁ0-9 :\n]+')
    return pattern.findall(string)[0].strip()

def find_all_theatres(theatres):
    dicti = {}
    for theatre in theatres:
        Metro = []
        metroes = theatre.findAll('span', class_= 'sub_title')[1].text.strip().split('\n')
        for metro in metroes:
            Metro.append(metro.strip())

        if theatre.findAll('h3')[0].text.strip() == 'Синема Парк Зеленопарк':
            Metro = ['Не завезли(']
        
        dicti[theatre.findAll('h3')[0].text.strip()] = {
            'metro': Metro,
            'address': theatre.findAll('span', class_= 'sub_title')[0].text.strip(),
            'phones': '+7-800-700-01-11' ,
            'url_hall': theatre.findAll('a')[0]['href']
        }
    return dicti

# Парсинг кинотеатров

url = "https://kinoteatr.ru/raspisanie-kinoteatrov/"
r = requests.get(url) 
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    theatres = soup.findAll('div', class_='col-md-12 cinema_card')
    CP_theatres = find_all_theatres(theatres)
else:
    print("Страница не найдена!")
    
cursor.execute('''CREATE TABLE halls(
                id integer PRIMARY KEY,
                web_id integer,
                name text,
                address text,
                metro text,
                phones text,
                theatre_url text)''')

id_=1
for key,item in CP_theatres.items():
    try:
        elements=[id_,id_,key,item['address'],', '.join(item['metro']),item['phones'],item['url_hall']]
        cursor.execute("insert into halls values ({},{},'{}','{}','{}','{}','{}')".format(*elements))
        id_+=1
    except sqlite3.IntegrityError:
        print(f'Вообще-то id({id_}) не уникален, ты смотри что добавляешь!')
        break
conn.commit()

# Парсинг списка фильмов

url_films = 'https://kinoteatr.ru/kinoafisha/'
print(url_films)

r = requests.get(url_films)
soup = BeautifulSoup(r.text, "html.parser")

films = soup.findAll('div', class_="movie_card_clickable")

films_dicti = {}
for film in films:
    film_name = film.findAll('span', class_='movie_card_header title')[0].text.strip()
    film_id = film.findAll('a')[0]['data-gtm-ec-id']
    film_age = film.findAll('i', class_='raiting_sub')[0].text.strip()
    film_genre = film.findAll('span', class_='hidden', itemprop="genre")[0].text.capitalize()
    film_duration = film.findAll('span', class_='hide-md title')[0].text.strip().split()[0]
    film_url = film.findAll('a')[0]['href']
    film_discription = film.findAll('meta', itemprop="description")[0]['content']
    
    if film_name.lower() == 'джуманджи: новый уровень':
        film_name = 'Джуманджи: Новый уровень'
    
    films_dicti[film_name] = {'ID':film_id,'Rec_age':film_age, 'Genre':film_genre, 'Duration':film_duration, 'URL':film_url, 'Discr':film_discription}
    
    
cursor.execute("""CREATE TABLE cinemas(
                id integer PRIMARY KEY,
                website_id integer NOT NULL,
                name text NOT NULL,
                duration integer NOT NULL,
                language text NOT NULL,
                genres text NOT NULL)""")

id_=1
for key,el in films_dicti.items():
    data_id=el['ID']
    name = key
    duration=el['Duration']
    language='undefined'
    genres=el['Genre']
    try:
        cursor.execute(f"insert into cinemas values ({id_},{data_id},'{name}',{duration},'{language}','{genres}')")
        id_+=1
    except sqlite3.IntegrityError:
        print(f'Вообще-то id({id_}) не уникален, ты смотри что добавляешь!')
        break
conn.commit()

# Парсинг дат и сеансов

session = {}
for theatre in CP_theatres:
    
    url_films = CP_theatres[theatre]['url_hall']
    print(url_films)
    
    r = requests.get(url_films)
    soup = BeautifulSoup(r.text, "html.parser")

    dates = soup.findAll('input')[0]['data-dates'].split(',')
    print(dates)
    
    local_sessions = {}
    for date in dates:
        
        local_sessions[date] = []
        url_hall_films = url_films + '?date=' + date
        r = requests.get(url_hall_films)
        
        soup_films = BeautifulSoup(r.text, "html.parser")
        films = soup_films.findAll('div', class_='shedule_movie bordered gtm_movie')
        
        for film in films:
            film_name = film['data-gtm-list-item-filmname']           
            dicti = {film_name:[]}
            
            times = film.findAll('a', class_='shedule_session')
            for time in times:
                film_time = time.findAll('span', class_='shedule_session_time')[0].text.strip()
                dicti[film_name].append(film_time)
            
            local_sessions[date].append(dicti)
    session[theatre] = local_sessions

cursor.execute("""CREATE TABLE sessions(
                id PRIMARY KEY,
                Hall_Name text,
                Hall_url text,
                Date text,
                Film_Name text,
                Film_Format text,
                Time text,
                FOREIGN KEY (Hall_Name) REFERENCES halls(name)
                )""")

id_ = 1
cursor=conn.cursor()
for key, vals in session.items():
    
    HallName = key
    Hall_url = CP_theatres[HallName]['url_hall']
   
    cursor.execute("""SELECT * from halls where name = ?""", (HallName,))
    records = cursor.fetchall()
    for row in records:
        print('--->',row)
        
        Hall_id = row[1]
        HallAdress = row[3]
        HallMetro = row[4]
        HallPhones = row[5]
        HallURL = row[6]
       
        print(f'''Hall_id = {Hall_id}
        HallAdress = {HallAdress}
        HallMetro = {HallMetro}
        HallPhones = {HallPhones}
        HallURL = {HallURL}''')
   
    for date, list_elements in vals.items():
        print('--->',date)
        for el in list_elements:
            print(el)
            for Name, schedule in el.items():
                FilmName = Name
                FilmSchedule = schedule
                print(FilmSchedule)
                for time in FilmSchedule:
                    FilmFormat = 'nodata'
                    FilmTime = time
                    cursor.execute(f"insert into sessions values ({id_},'{HallName}', '{HallURL}', '{date}', '{FilmName}', '{FilmFormat}', '{FilmTime}')")
                    id_ += 1
                
conn.commit()