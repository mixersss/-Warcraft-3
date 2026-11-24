"""Known server positions stay attached to the trip through confirmed arrival."""
import unittest
from pathlib import Path
from unittest.mock import Mock

from farm_scouting import scout_points
from regions import Regions
import test_alpha76
import test_travel58


class KnownCampTests(unittest.TestCase):
    def test_arrival_walk_uses_known_selected_camp_instead_of_rescoring_entire_map(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        regions=Regions(Path(__file__).resolve().parents[1]/'assets')
        policy.nav=regions.nav('garner')
        world.own.values.update({0:40,4:8,1:2000,31:2000})
        origin=world.own.position
        near=(origin[0]+2500,origin[1]+2500)
        known=(origin[0]+6500,origin[1]+2500)
        policy.nav.nearest=Mock(side_effect=lambda p,*args:tuple(p))
        policy.nav.land_component=Mock(return_value=1)
        policy.region={'farms':{'243':{'points':[near,known],'level':38,'hp':600}}}
        _,travel,_=test_travel58.Travel58Tests().make()
        travel.world=world
        travel.preferred_model=243
        travel.site_until=500
        travel.site_arrival=('garner',90)
        travel.site_camp=('garner',243,(known,))
        travel.tick=Mock(return_value=False)
        policy.hunt_travel=travel
        policy.move_to=Mock(return_value=True)
        policy.tick(100)
        self.assertEqual(policy.search_goal,known)
        policy.move_to.assert_called_once_with(known,100)

    def test_exact_server_coordinates_survive_rectangle_sampling_budget(self):
        from types import SimpleNamespace
        exact=(4100,4100)
        nav=SimpleNamespace(land_component=lambda p:1,nearest=lambda p,*args:p,
                            combat_allowed=lambda p:True)
        points=scout_points(nav,[{'rectangle_cm':[(0,0),(30000,30000)]},
                                 {'rectangle_cm':[exact,exact]}],[],limit=1)
        self.assertEqual(points[0],exact)
        self.assertEqual(len(points),2)
