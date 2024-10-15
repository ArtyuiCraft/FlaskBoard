import os

if not os.path.exists("./instance") or not os.path.exists("./instance/flaskboard.sqlite"):
    os.system("flask --app flaskboard init-db")
