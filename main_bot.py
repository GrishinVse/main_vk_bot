import vk_api
import random
import json
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType

token = "597bafb876abbf5cb3ce8782bdd7f324fd8a9dd1cfc8f650157d0eafb514cefe2c51e757f33f3a11f8eda"

vk = vk_api.VkApi(token=token)
vk._auth_token()

def message_writer(user_id, message,keyboard=None):
    random_id=random.randint(1, 2147483647)
    vk.method('messages.send', {'user_id': user_id, 'message': message,'random_id':random_id,'keyboard':keyboard})

def keyboard_maker(list_buttons=[],brand=None,hall_name=None,date=None,film=None,next_=0):
    keyboard={"one_time": True}
    list_buttons=list_buttons[32*next_:]
    if next_:
        payload={'b':brand,'h':hall_name,'d':date,'f':film,'n':next_-1}
        button_previous={"action": {"type": "text","payload": payload,"label": 'НАЗАД'},
                        "color": "negative"}
    else:
        button_previous=None
    if len(list_buttons)>32:
        payload={'b':brand,'h':hall_name,'d':date,'f':film,'n':next_+1}
        button_next={"action": {"type": "text","payload": payload,"label": 'ДАЛЕЕ'},
                     "color": "positive"}
    else:
        button_next=None
    
    list_buttons=list_buttons[:32]
    buttons=[]
    for i,button in enumerate(list_buttons):
        
        payload={'b':brand,'h':hall_name,'d':date,'f':film,'n':0}
        if not payload['b']:
            payload['b']=button
        elif not payload['h']:
            payload['h']=button
        elif not payload['d']:
            payload['d']=button
        else:
            payload['f']=button
        button={"action": {"type": "text","payload": payload,"label": next_*32+i+1},
                "color": "secondary"}
        buttons.append(button)
    list_buttons=[]
    while buttons:  
        list_buttons.append(buttons[:4])
        buttons=buttons[4:]
    if button_next and button_previous:
        list_buttons.append([button_previous,button_next])
    elif button_next:
        list_buttons.append([button_next])
    elif button_previous:
        list_buttons.append([button_previous])
    else:
        pass
    menu_button={"action": {"type": "text","payload": None,"label": 'В МЕНЮ'},
                "color": "primary"}
    
    list_buttons.append([menu_button])
    keyboard["buttons"]=list_buttons 
    keyboard=str(json.dumps(keyboard))
    return keyboard

def halls(brand):
    conn=sqlite3.connect(f'{brand.lower()}.db')
    cursor=conn.cursor()
    halls = cursor.execute("SELECT * from halls").fetchall()
    return [elem[2] for elem in halls]

def dates(brand, cinema_hall):
    dates = []
    conn=sqlite3.connect(f'{brand.lower()}.db')
    cursor=conn.cursor()
    all_dates = cursor.execute(f"select Date from sessions where Hall_Name='{cinema_hall}'").fetchall()
    for date in all_dates:
        dates.append(date[0])
    dates = sorted(list(set(dates)))
    return dates

def films(brand, hall_name, date):
    films = []
    conn=sqlite3.connect(f'{brand.lower()}.db')
    cursor=conn.cursor()
    all_films = cursor.execute(f"select Film_Name from sessions where (Date='{date}' and Hall_Name = '{hall_name}')").fetchall()
    for film in all_films:
        films.append(film[0])
    films = sorted(list(set(films)))
    return films

def final_info(brand, hall_name, date, film):
    
    conn=sqlite3.connect(f'{brand.lower()}.db')
    cursor=conn.cursor()
    
    hall_info=cursor.execute(f"select * from halls where name='{hall_name}'").fetchall()[0]  
    hall_address = hall_info[3]
    hall_metro = hall_info[4]
    hall_phone = hall_info[5]
    hall_url = hall_info[6]
    
    film_info=cursor.execute(f"select * from cinemas where name='{film}'").fetchall()[0]
    film_duration = film_info[3]
    film_genres = film_info[5]
    
    sesions_info=cursor.execute(f"select * from sessions where (Film_Name='{film}' and Hall_Name='{hall_name}' and Date='{date}')").fetchall()
    Final_Text=f'''Информация о кинотеатре:
{brand} - {hall_name} 
по адресу {hall_address}
Ближайшее метро {hall_metro}
Связаться по телефону {hall_phone}
Или через сайт: {hall_url}
------------------------
Фильм: {film} // {film_genres}
{film_duration} минут
Сеансы:'''
    for item in sesions_info:
        Final_Text = Final_Text + f'\nФормат: {item[5]}, время: {item[6]}'
    return Final_Text

#Brands = ['KARO','CinemaPark','CinemaStar']

Brands = ['KARO','CinemaPark']

longpoll = VkLongPoll(vk)       
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            payload=json.loads(event.extra_values.get('payload','""'))
            if request == "привет" or request == "хай" or request == "приф" or request == "начать":
                message_writer(event.user_id, "Привет! Начнем работу 💪")
            if not(payload):
                message_writer(event.user_id, 'Выберите бренд\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(Brands)]),keyboard_maker(Brands))
            elif payload['b']and not payload['h']:
                next_ = payload['n']
                brand = payload['b']
                
                hall_name = halls(brand)
                
                message_writer(event.user_id,'Выберите кинотеатр\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(hall_name)]),keyboard_maker(hall_name,brand,next_=next_))
            elif payload['b'] and payload['h'] and not payload['d']:
                next_ = payload['n']
                brand = payload['b']
                hall_name = payload['h']
                
                date = dates(brand, hall_name)
                
                message_writer(event.user_id,'Выберите дату\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(date)]),keyboard_maker(date,brand,hall_name,next_=next_))
            elif payload['b']and payload['h'] and payload['d'] and not payload['f']:
                next_ = payload['n']
                brand = payload['b']
                hall_name = payload['h']
                date = payload['d']
                
                film = films(brand, hall_name, date)
                
                message_writer(event.user_id,'Выберите фильм\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(film)]),keyboard_maker(film,brand,hall_name,date,next_=next_))
            else:
                brand = payload['b']
                hall_name = payload['h']
                date = payload['d']
                film = payload['f']
                
                info = final_info(brand, hall_name, date, film)
                
                message_writer(event.user_id, info, keyboard_maker())