"""A portable prim behavior with timeline and explicit event control."""
import math
import random

import carb.eventdispatcher
from omni.kit.scripting import BehaviorScript
from pxr import Gf, Sdf, UsdGeom


class OrbitBehavior(BehaviorScript):
    def on_init(self):
        self._origin = None
        self._rng = random.Random(71)
        self._phase = 0.0
        for name, default in [('radius', 0.6), ('speed', 1.0)]:
            attribute = self.prim.CreateAttribute(f'exposedVar:orbit:{name}', Sdf.ValueTypeNames.Double)
            if not attribute.HasAuthoredValueOpinion():
                attribute.Set(default)
        self._subscription = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name='lesson.orbit.randomize', on_event=self._on_event, observer_name=str(self.prim_path))

    def _on_event(self, event):
        if event.payload.get('prim_path') == str(self.prim_path):
            self._phase = self._rng.uniform(0, 2 * math.pi)
            carb.eventdispatcher.get_eventdispatcher().dispatch_event(
                event_name='lesson.orbit.done', payload={'prim_path': str(self.prim_path), 'state_name': 'RANDOMIZED'})

    def on_play(self):
        translate = self.prim.GetAttribute('xformOp:translate')
        if not translate:
            translate = UsdGeom.Xformable(self.prim).AddTranslateOp().GetAttr()
            translate.Set((0, 0, 0))
        self._origin = Gf.Vec3d(translate.Get())

    def on_update(self, current_time, delta_time):
        if self._origin is None or delta_time <= 0:
            return
        radius = self.prim.GetAttribute('exposedVar:orbit:radius').Get()
        speed = self.prim.GetAttribute('exposedVar:orbit:speed').Get()
        angle = speed * current_time + self._phase
        self.prim.GetAttribute('xformOp:translate').Set(
            self._origin + Gf.Vec3d(radius * math.cos(angle), radius * math.sin(angle), 0))

    def on_stop(self):
        if self._origin is not None:
            self.prim.GetAttribute('xformOp:translate').Set(self._origin)
            self._origin = None

    def on_destroy(self):
        self._subscription.reset()
