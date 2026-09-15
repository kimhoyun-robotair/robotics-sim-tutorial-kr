import carb.settings
import omni.ext

class SettingsExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.value = carb.settings.get_settings().get("/exts/kr.settings.demo/data/foo")
        print("kr.settings.demo startup foo =", self.value)

    def on_shutdown(self):
        print("kr.settings.demo shutdown")
