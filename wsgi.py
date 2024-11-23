from app import create_app
import os
print("dir: "+str(os.listdir()),flush=True)
for i,dir in enumerate(os.listdir()):
    print(str(i) + ': ' + dir,flush=True)
app = create_app()
