a = [
        {
            "id": "0",
            "provider": "provider0",
            "info": {
                "name": "video1.mp4",
                "tags": ["action", "mistery", "comedy"]
            }
        },
        {
            "id": "1",
            "provider": "provider1",
            "info": {
                "name": "video2.mp4",
                "tags": ["action", "mistery", "comedy"]
            }
        }
    ]

print(a)

for el in a:
    if el["id"] == "1":
        el["info"]["name"] = "nombre cambiado"

print(a)