import carb.settings
import omni.kit.app

settings = carb.settings.get_settings()
settings.set("/exts/kr.settings.demo/data/foo", True)
manager = omni.kit.app.get_app().get_extension_manager()
manager.set_extension_enabled_immediate("kr.settings.demo", False)
manager.set_extension_enabled_immediate("kr.settings.demo", True)
print("live setting", settings.get("/exts/kr.settings.demo/data/foo"))
