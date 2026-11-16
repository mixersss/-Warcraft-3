"""Read native spell costs and coral charge; never change an owned item locally."""

CORAL_LINKS = {5: 213, 6: 216, 7: 214}
BASIC_CORALS = {817: 5, 635: 6, 867: 7, 872: 8}

def required_links(world):
    links={7} if world.own.values.get(4) in (4,16) else set()
    if links and world.skills.get(213,{}).get('level'):links.add(5)
    if world.own.values.get(4)==16 and world.skills.get(216,{}).get('level'):links.add(6)
    return links


def damage_ready(world, catalog):
    job = world.own.values.get(4)
    if job not in (4, 16):
        return True
    for link, skill in ((7, 214), (6, 216)):
        if skill == 216 and job != 16:
            continue
        learned = world.skills.get(skill, {})
        identity = world.own.equipment.get(link)
        item = world.own.equipment_details.get(link, {})
        if (learned.get('level') and learned.get('state') == 1
                and catalog.types.get(identity) == 29
                and item.get('identity') == identity and item.get('valid')
                and item.get('energy', 0) >= max(1, learned.get('energy', 1))):
            return True
    return False


def spent_basic(world, item):
    """Only disposable plain level-I bag copies with a matching worn coral.

    Higher tiers, modified items, unknown energy/cost and the worn coral survive.
    A copy that can still pay for one learned spell is also retained.
    """
    link = BASIC_CORALS.get(item.identity)
    skill = world.skills.get(CORAL_LINKS.get(link), {})
    cost = skill.get('energy')
    return bool(world.own.values.get(4) in (4, 16) and link in CORAL_LINKS
                and skill.get('level') and type(cost) is int and cost > 0
                and world.own.equipment.get(link) == item.identity
                and item.valid and item.max_energy == 100 and item.energy < cost
                and not item.forge and not any(item.parameters)
                and not any(a or b for a, b in item.instance_attributes))
