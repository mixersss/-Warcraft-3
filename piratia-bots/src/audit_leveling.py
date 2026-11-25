"""Read-only fleet audit. Never reads accounts, PINs or saved credentials."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

GEMS={860,861,862,863,864,865,866,885,1012,*range(5609,5617),*range(6400,6408)}


def inspect(report):
    hunt=report.get('hunt',{});world=hunt.get('world',{})
    learning=hunt.get('hunting_learning',{})
    equipment=report.get('equipment',{});pet=report.get('petcare',{})
    flags=[]
    inventory=report.get('vendor',{})
    gem_units=sum(i.get('count',0) for i in inventory.get('bag_items',[]) if i.get('id') in GEMS)
    if inventory.get('free_bag_slots',99)<=4:flags.append('в сумке осталось 4 ячейки или меньше')
    if gem_units>=10:flags.append('накоплены камни: проверить ларёк/резерв ковки')
    idle=learning.get('seconds_without_xp',0) or 0
    if idle>=600:flags.append('нет опыта 10+ минут')
    if hunt.get('state_seconds',0)>=60 and not hunt.get('target_id'):
        flags.append('состояние без цели 60+ секунд: проверить движение/переход')
    if hunt.get('offmesh_recovery',{}).get('reason'):
        flags.append('геометрия: '+hunt['offmesh_recovery']['reason'])
    if world.get('profession')==0 and world.get('level',0)>=9:flags.append('нет первой профессии')
    if not pet.get('observed_fairy'):flags.append('нет подтверждённой феи')
    if pet.get('urgently_hungry'):flags.append('голодная фея')
    if pet.get('full_growth') and not pet.get('required_fruit_owned'):flags.append('фея ждёт плод')
    plan=report.get('skills',{}).get('development_plan',{})
    if plan.get('blocker'):flags.append('навыки: '+plan['blocker'])
    spell=hunt.get('combat_skills',{})
    if spell.get('reason'):flags.append('бой: '+spell['reason'])
    if equipment.get('confirmation_timeouts'):flags.append('были тайм-ауты экипировки')
    attributes=world.get('combat_attributes',{})
    if world.get('hp',0)<world.get('max_hp',1)*.55:flags.append('низкие HP')
    if attributes.get('2',0)<attributes.get('32',0)*.35:flags.append('низкие SP')
    return {'bot':report.get('bot_index'),'version':report.get('version'),
            'time_utc':report.get('time_utc'),'level':world.get('level'),
            'job':world.get('profession'),'map':world.get('map'),
            'position':world.get('position'),'state':hunt.get('state'),
            'state_seconds':round(hunt.get('state_seconds',0)),
            'xp_net':learning.get('session_xp_net'),
            'xp_per_minute':learning.get('session_xp_per_minute'),
            'without_xp_seconds':round(idle),'flags':flags,
            'search_destination':hunt.get('search_destination'),
            'camp':hunt.get('hunting_coordinates'),
            'portal_problem':hunt.get('portal_shortcut',{}).get('last_problem'),
            'travel_state':report.get('hunting_travel',{}).get('state'),
            'fairy_blocker':pet.get('purchase_blocker'),
            'gem_units':gem_units,'stall_opens':report.get('market',{}).get('confirmed_opens',0)}


def audit(directory):
    rows=[];errors=[]
    for path in sorted(Path(directory).glob('bot-report-*.json')):
        try:rows.append(inspect(json.loads(path.read_text(encoding='utf-8-sig'))))
        except (OSError,ValueError,TypeError,AttributeError) as error:
            errors.append({'file':path.name,'error':type(error).__name__})
    flags=Counter(flag for row in rows for flag in row['flags'])
    return {'reports':len(rows),'levels':dict(Counter(row['level'] for row in rows)),
            'positive_session_xp':sum((r['xp_net'] or 0)>0 for r in rows),
            'no_xp_10min':sum(r['without_xp_seconds']>=600 for r in rows),
            'flags':dict(flags),'read_errors':errors,'bots':rows,
            'limits':'Snapshot flags are diagnostic leads, not proof of a continuous idle period. Session XP may include owner grants; compare fresh sessions.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Аудит кача по bot-report-*.json; аккаунты не читаются')
    parser.add_argument('directory',nargs='?',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv);directory=Path(args.directory)
    result=audit(directory);output=args.output or directory/'leveling-audit.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with output.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['bot','version','time_utc','level','job','map','position','state','state_seconds','xp_net','xp_per_minute','without_xp_seconds','flags']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for row in result['bots']:writer.writerow({**row,'flags':'; '.join(row['flags'])})
    print(f"Отчётов: {result['reports']}; положительный опыт за сессию: {result['positive_session_xp']}; без опыта 10+ минут: {result['no_xp_10min']}")
    print(output);print(output.with_suffix('.csv'))


if __name__=='__main__':main()
