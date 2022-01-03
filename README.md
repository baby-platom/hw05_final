# Yatube

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)

**Мой самый первый проект**:smiley:

## Краткое описание: 

Foodgram - это продуктовый помощник. Здесь пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд 

В проекте применяется 
- **Django**, 
- **Python 3**,
- **Git**
- 

## Как развернуть проект локально: 

Клонировать репозиторий и перейти в него в командной строке: 

``` 
git clone https://github.com/baby-platom/hw05_final
``` 

``` 
cd hw05_final
``` 

Cоздать и активировать виртуальное окружение: 

``` 
python -m venv env 
``` 

```
source venv/Scripts/activate
``` 

``` 
python -m pip install --upgrade pip 
``` 
Установить зависимости из файла requirements.txt: 

``` 
pip install -r requirements.txt 
```

Выполнить миграции: 

``` 
python manage.py makemigrations
``` 
``` 
python manage.py migrate 
```
Запустить проект: 
``` 
python manage.py runserver
```

## Системные требования:

Предложенная инструкция по развертыванию проекта подходит для Windows, но он также можеть быть запущен на MacOS или Linux

Все зависимости изложены в requirements.txt (если развертывание проходит по инструкции, в виртуальном окружении все зависимости будут установлены)

## Автор: 

[Егорченков Платон](https://drive.google.com/file/d/1Rdy9sitBIYgMqdCd1qWXyT6SDRI2HQj2/view?usp=sharing)
