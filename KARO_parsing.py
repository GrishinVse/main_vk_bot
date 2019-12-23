import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('karo.db')
cursor=conn.cursor()

def remove_all(string):
    pattern = re.compile(r'[А-Яа-яёЁ0-9 ]+')
    return pattern.findall(string)[0].strip()

def find_all_theatres_KARO(theatres):
    dicti = {}
    metro_class = "cinemalist__cinema-item__metro__station-list__station-item"
    for theatre in theatres:
        dicti[theatre.findAll('h4')[0].text.strip()] = {
            'metro': [remove_all(i.text) for i in theatre.findAll('li', class_= metro_class)],
            'address': theatre.findAll('p')[0].text.split('+')[0].strip(),
            'phones': '+' +  theatre.findAll('p')[0].text.split('+')[-1],
            'data-id' : theatre['data-id']
        }
    return dicti

url = "https://karofilm.ru"
url_theatres = url + "/theatres"

r = requests.get(url_theatres) 
if r.status_code == 200:
    soup = BeautifulSoup(r.text, "html.parser")
    theatres = soup.findAll('li', class_='cinemalist__cinema-item')
    karo_theatres = find_all_theatres_KARO(theatres)
else:
    print("Страница не найдена!")
    
#cursor.execute('drop table halls')
    
cursor.execute('''CREATE TABLE halls(
                id integer PRIMARY KEY,
                web_id integer,
                name text,
                address text,
                metro text,
                phones text,
                theatre_url text)''')

id_=1
for key,item in karo_theatres.items():
    try:
        elements=[id_,item['data-id'],key,item['address'],', '.join(item['metro']),item['phones'],url_theatres + "?id=" + item['data-id']]
        cursor.execute("insert into halls values ({},{},'{}','{}','{}','{}','{}')".format(*elements))
        id_+=1
    except sqlite3.IntegrityError:
        print(f'Вообще-то id({id_}) не уникален, ты смотри что добавляешь!')
        break
conn.commit()

#cursor.execute('drop table cinemas')

cursor.execute("""CREATE TABLE cinemas(
                id integer PRIMARY KEY,
                website_id integer NOT NULL,
                name text NOT NULL,
                duration integer NOT NULL,
                language text NOT NULL,
                genres text NOT NULL)""")

films_all_class='afisha-item'
r = requests.get(url)
if r.status_code==200:
    films_all_parser=BeautifulSoup(r.text,'html.parser')
    all_films_list=films_all_parser.findAll('div',class_=films_all_class)
else:
    print('Ошибка! Фильм не найден!')
    
id_=1
for element in all_films_list:
    data_id=element['data-id']
    name=element.findAll('h3')[0].text.strip()
    duration=element.findAll('span')[0].text
    language='undefined'
    try:
        genres=element.findAll('p',class_='afisha-genre')[0].text
    except IndexError:
        genres='undefined'
    try:
        cursor.execute(f"insert into cinemas values ({id_},{data_id},'{name}',{duration},'{language}','{genres}')")
        id_+=1
    except sqlite3.IntegrityError:
        print(f'Вообще-то id({id_}) не уникален, ты смотри что добавляешь!')
        break
conn.commit()

#cursor.execute('drop table sessions')

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

MAIN_DICT = {}
for place in karo_theatres:
    
    Place_ID = karo_theatres[place]['data-id']
    
    url_ = 'https://karofilm.ru/theatres?id='+ Place_ID
    print('Hall URL = ',url_)

    r = requests.get(url_)

    dates = []
    films_dicti = {}

    date_parser=BeautifulSoup(r.text,'html.parser')
    dates=date_parser.findAll('select',class_='widget-select')[0]
    dates=[i['data-id'] for i in dates.findAll('option')]
    
    for date in dates:
        url_dates = url_ + '&date=' + date
        new_r = requests.get(url_dates)   
        soup_dates = BeautifulSoup(new_r.text, "html.parser")

        films = soup_dates.findAll('div', class_="cinema-page-item__schedule__row__data")
        films_dicti[date] = []
        for film in films:
            film_name = film.findAll('h3')[0].text.split(',')[0].split('/')[0].strip()

            dicti = {'Name': film_name , 'Schedule' : {}}

            ScheduleData = film.findAll('div', class_="cinema-page-item__schedule__row__board-row")
            for Data in ScheduleData:
                Formats = Data.findAll('div', class_="cinema-page-item__schedule__row__board-row__left")
                for Format in Formats:
                    dicti['Schedule'][Format.text.strip()] = []
                Times = Data.findAll('div', class_="cinema-page-item__schedule__row__board-row__right")
                for Time in Times:
                    B = Time.findAll('a', class_="karo-wi-button sessionButton")
                    for num in B:
                        dicti['Schedule'][Format.text.strip()].append(num.text)

            films_dicti[date].append(dicti)
    
    MAIN_DICT[place] = films_dicti
    
id_ = 1
cursor=conn.cursor()
for key, vals in MAIN_DICT.items():
    HallName = key
    Hall_ID = karo_theatres[HallName]['data-id']

    cursor.execute("""SELECT * from halls where web_id = ?""", (Hall_ID,))
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
            FilmName = el['Name']
            
            FilmSchedule = el['Schedule']
            
            for form, times in FilmSchedule.items():
                FilmFormat = form
                FilmTimes = times
                
                for FilmTime in FilmTimes:

                    cursor.execute(f'insert into sessions values ({id_},"{HallName}", "{HallURL}", "{date}", "{FilmName}", "{FilmFormat}", "{FilmTime}")')
                    id_ += 1
                    
                    
conn.commit()