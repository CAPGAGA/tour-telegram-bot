import databases
import sqlalchemy
from settings import DATABASE_URL


database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String), # telegram username of user e.g. @example
    sqlalchemy.Column("chat_id", sqlalchemy.Integer), # chat id with user e.g. 123
    sqlalchemy.Column("registration_date", sqlalchemy.DateTime), # date of registration
    sqlalchemy.Column('access_granted', sqlalchemy.Boolean), # access column -> true after payment received
    sqlalchemy.Column('current_rout', sqlalchemy.ForeignKey('routs.id')), # currently selected rout
    sqlalchemy.Column('current_rout_point', sqlalchemy.ForeignKey('rout_points.id')), # currently selected rout point
    sqlalchemy.Column('user_reg_hash', sqlalchemy.String)
)

admins = sqlalchemy.Table(
    'admins',
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("chat_id", sqlalchemy.Integer, unique=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True)
)

keys = sqlalchemy.Table(
    'keys',
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("key", sqlalchemy.String),
    sqlalchemy.Column("used", sqlalchemy.Boolean, unique=False, default=False)
)

routes = sqlalchemy.Table(
    "routs",
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('rout_name', sqlalchemy.String) # names of routs
)

rout_points = sqlalchemy.Table(
    "rout_points",
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('rout_id', sqlalchemy.ForeignKey('routs.id')),
    sqlalchemy.Column('previous_point', sqlalchemy.Integer), # id of previous point
    sqlalchemy.Column('next_point', sqlalchemy.Integer), # id of next point
    sqlalchemy.Column('description', sqlalchemy.String), # plain text description
    sqlalchemy.Column('map_point', sqlalchemy.String), # url with coordinates e.g [longitude, latitude]
    sqlalchemy.Column('images', sqlalchemy.String), # filename to images on local machine
    sqlalchemy.Column('audio', sqlalchemy.String) # filename to audio file on local machine
)

promo_codes = sqlalchemy.Table(
    "promo_codes",
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('name', sqlalchemy.String),
    sqlalchemy.Column('price', sqlalchemy.Integer),
    sqlalchemy.Column('is_percent', sqlalchemy.Boolean),
    sqlalchemy.Column('percent', sqlalchemy.Integer),
    sqlalchemy.Column('is_counter', sqlalchemy.Boolean),
    sqlalchemy.Column('counter', sqlalchemy.Integer),
    sqlalchemy.Column('promocode', sqlalchemy.String, unique=True)
)

subscriptions_keys = sqlalchemy.Table(
    "subscription_keys",
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('key', sqlalchemy.String, unique=True),
    sqlalchemy.Column('used', sqlalchemy.Boolean)
)


engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

metadata.create_all(engine)

