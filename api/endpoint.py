from api.v1 import users_routes as users
from api.v1 import saham_routes as saham

all_routers = [
    users.router,
    saham.router
]
