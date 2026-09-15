import os
import numpy as np
import omni.ext
from isaacsim.examples.browser import get_instance as get_browser_instance
from isaacsim.examples.interactive.base_sample import BaseSample, BaseSampleUITemplate
from isaacsim.core.api.objects import DynamicCuboid

class FallingCubeSample(BaseSample):
    def setup_scene(self):
        world = self.get_world()
        world.scene.add_default_ground_plane()
        world.scene.add(DynamicCuboid(prim_path="/World/LearningCube", name="learning_cube",
                                     position=np.array([0.0, 0.0, 1.5]), size=0.25,
                                     color=np.array([0.2, 0.7, 0.3])))

    async def setup_post_load(self):
        self.cube = self.get_world().scene.get_object("learning_cube")
        print("loaded pose:", self.cube.get_world_pose()[0])

    async def setup_post_reset(self):
        print("reset pose:", self.cube.get_world_pose()[0])

class ExampleExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.name = "Korean Falling Cube"
        self.category = "Korean Examples"
        self.sample = FallingCubeSample()
        self.ui = BaseSampleUITemplate(ext_id=ext_id, file_path=os.path.abspath(__file__),
            title=self.name, overview="Load, play and reset one falling cube.",
            doc_link="https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html",
            sample=self.sample)
        get_browser_instance().register_example(name=self.name, category=self.category,
            execute_entrypoint=self.ui.build_window, ui_hook=self.ui.build_ui)

    def on_shutdown(self):
        get_browser_instance().deregister_example(name=self.name, category=self.category)
        self.ui = None
        self.sample = None
