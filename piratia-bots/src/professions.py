"""Labels for authoritative server job IDs, separate from a planned class."""
NAMES={0:'новичок',1:'мечник',2:'лучник',4:'исследователь',5:'знахарка',
       8:'чемпион',9:'крестоносец',12:'стрелок',13:'целитель',14:'колдунья',16:'покоритель морей'}

def describe(job):
    return str(job)+' — '+NAMES.get(job,'неизвестно') if type(job) is int else 'нет данных'
