import omni.ext
import omni.ui as ui
import omni.usd
from pxr import Gf, UsdGeom

class StarterExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.window = ui.Window("Korean Extension Starter", width=350, height=130)
        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("Create a local USD cube with a callback")
                ui.Button("Create Cube", clicked_fn=self.create_cube)

    def create_cube(self):
        stage = omni.usd.get_context().get_stage()
        path = "/World/ExtensionCube"
        if stage.GetPrimAtPath(path):
            raise RuntimeError("ExtensionCube exists; open a new stage to repeat")
        cube = UsdGeom.Cube.Define(stage, path)
        cube.CreateSizeAttr(0.3)
        cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
        print("created", path)

    def on_shutdown(self):
        if self.window:
            self.window.destroy()
        self.window = None
