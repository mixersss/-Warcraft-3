"""Compositional trade wording; callers supply only observed stock/quote/location facts."""
import itertools

OPENINGS=('','Смотри: ','Кстати, ','Вот: ','По товару: ','По делу: ','Если нужно: ','По продаже: ',
          'Ассортимент: ','Кому нужно: ','Для покупки: ','Из товаров: ','Моё предложение: ','Предлагаю: ',
          'Уточню: ','На продажу: ','Объявление: ','Про товар: ','По цене: ','Доступно: ')
ENDINGS=('',' Пиши.',' Спрашивай.',' Если нужно.',' Цена указана.',' Можешь проверить.',
         ' Посмотри.',' Есть интерес?',' Обращайся.',' Для желающих.',' Можно обсудить.',
         ' Сверь цену.',' Без спешки.',' Уточняй.',' Пиши в ЛС.',' Кому подходит?',
         ' Вот условия.',' Решай.',' Жду вопроса.',' Если подходит.')
SALE=(
 'ID{item}: {count} шт., {price}G/шт. {place}.',
 'Есть ID{item}, {count} шт. По {price}G. {place}.',
 'В продаже ID{item}: {count} шт. По {price}G. {place}.',
 'Ларёк: ID{item}, {count} шт., {price}G за штуку. {place}.',
 'Товар ID{item}, {count} шт. Цена {price}G/шт. {place}.',
 'Найдётся ID{item}: {count} шт. По {price}G/шт. {place}.',
 'Из товаров ID{item}: {count} шт., {price}G/шт. {place}.',
 'Можно купить ID{item}: {count} шт., {price}G/шт. {place}.',
 'Сейчас в ларьке ID{item}, {count} шт. По {price}G. {place}.',
 'Выставлен ID{item}: {count} шт. Цена {price}G/шт. {place}.',
 'Проверь ларёк: ID{item}, {count} шт., {price}G/шт. {place}.',
 'Открыта продажа ID{item}: {count} шт. По {price}G. {place}.')
MEETING=('Сейчас я: {place}.','Текущее место: {place}.','Мои координаты сейчас: {place}.',
         'Посмотри здесь: {place}.','Я сейчас здесь: {place}.','Вот где я сейчас: {place}.',
         'На данный момент: {place}.','Текущая точка: {place}.')

def variants(kind,**facts):
    facts.setdefault('label','')
    templates=SALE if kind=='sale' else MEETING
    for opening,template,ending in itertools.product(OPENINGS,templates,ENDINGS):
        if kind=='sale' and facts['label']:template=template.replace('ID{item}','{label} ID{item}')
        text=opening+template.format(**facts)+ending
        if len(text.encode('cp1251',errors='replace'))<=120:yield text

def render(rng,kind,**facts):
    # Reservoir selection avoids allocating thousands of rendered strings per chat event.
    chosen=None
    for index,text in enumerate(variants(kind,**facts),1):
        if rng.randrange(index)==0:chosen=text
    return chosen
