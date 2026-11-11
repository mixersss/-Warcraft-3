"""Offline population target planner, using this server's allowed profession/body pairs.

Does not create characters or grant jobs. Runtime remains a small hunting pilot.
"""
from collections import Counter, deque

# Supplied resource/script/MisSdk/TemplateSDK.lua AddCatTable (lines 158..202).
ALLOWED = {1: (9, 12, 16), 2: (8,), 3: (12, 13, 14, 16), 4: (13, 14, 16)}
RACE_TARGETS = {1: 100, 2: 100, 3: 100, 4: 100}
CLASS_TARGETS = {8: 100, 9: 60, 12: 60, 13: 60, 14: 60, 16: 60}


def plan_population(races=None, classes=None):
    races = dict(RACE_TARGETS if races is None else races)
    classes = dict(CLASS_TARGETS if classes is None else classes)
    if (set(races) - set(ALLOWED) or set(classes) - {8, 9, 12, 13, 14, 16}
            or any(type(n) is not int or n < 0 for n in [*races.values(), *classes.values()])
            or not 1 <= sum(races.values()) <= 400
            or sum(races.values()) != sum(classes.values())):
        raise ValueError('Invalid population quotas')
    # Integral max flow: never manufacture an illegal race/class pairing to meet quotas.
    graph = {}
    def edge(a, b, capacity):
        graph.setdefault(a, {})[b] = capacity
        graph.setdefault(b, {})[a] = 0
    for race, count in sorted(races.items()):
        edge('start', ('race', race), count)
        for job in ALLOWED[race]:
            if job in classes:
                edge(('race', race), ('job', job), 400)
    for job, count in sorted(classes.items()):
        edge(('job', job), 'end', count)
    flow = 0
    while True:
        parents, queue = {'start': None}, deque(['start'])
        while queue and 'end' not in parents:
            current = queue.popleft()
            for target, remaining in graph[current].items():
                if remaining and target not in parents:
                    parents[target] = current
                    queue.append(target)
        if 'end' not in parents:
            break
        amount, node = 400, 'end'
        while parents[node] is not None:
            previous = parents[node]
            amount = min(amount, graph[previous][node])
            node = previous
        node = 'end'
        while parents[node] is not None:
            previous = parents[node]
            graph[previous][node] -= amount
            graph[node][previous] += amount
            node = previous
        flow += amount
    if flow != sum(races.values()):
        raise ValueError('Race and class quotas conflict with server profession restrictions')
    per_race = {}
    for race in sorted(races):
        per_race[race] = []
        for job in ALLOWED[race]:
            count = graph.get(('job', job), {}).get(('race', race), 0)
            per_race[race].extend([job] * count)
    # Round-robin races, so early subsets are not entirely one body type.
    result = []
    while any(per_race.values()):
        for race, jobs in per_race.items():
            if jobs:
                result.append({'body': race, 'target_job': jobs.pop(0)})
    return result


if __name__ == '__main__':
    import json
    plan = plan_population()
    print(json.dumps({'target_count': len(plan), 'runtime_enabled': False,
                      'races': dict(Counter(p['body'] for p in plan)),
                      'classes': dict(Counter(p['target_job'] for p in plan))}, indent=2))
