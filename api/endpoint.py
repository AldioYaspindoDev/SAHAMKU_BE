from api.v1 import users_routes as users
from api.v1 import saham_routes as saham
from api.v1 import news_routes as news
from api.v1 import market_routes as market

all_routers = [
    users.router,
    saham.router,
    news.router,
    market.router
]
