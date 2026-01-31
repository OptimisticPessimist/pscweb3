
import inspect
from playscript.conv import pdf

print("Classes in playscript.conv.pdf:")
for name, obj in inspect.getmembers(pdf):
    if inspect.isclass(obj):
        print(f"Class: {name}")
        for method_name, method in inspect.getmembers(obj):
            if inspect.isfunction(method) or inspect.ismethod(method):
                print(f"  Method: {method_name}")

print("\nFunctions in playscript.conv.pdf:")
for name, obj in inspect.getmembers(pdf):
    if inspect.isfunction(obj):
        print(f"Function: {name}")
