"""Run in a second Script Editor tab after tab1_create.py."""
if not cube or not cube.GetPrim().IsValid():
    raise RuntimeError("Run tab1_create.py on the current stage first")
print("before", cube.GetSizeAttr().Get())
cube.GetSizeAttr().Set(1.0)
print("after", cube.GetSizeAttr().Get())
