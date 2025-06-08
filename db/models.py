import datetime

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    Boolean,
    func, BigInteger,
)
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlalchemy.orm import Mapped
from sqlalchemy.orm._orm_constructors import mapped_column

from db.database import Base

class BaseTable(Base):
    """
       This is just abstract table to create created_at and updated_at
       by default in models where it's needed
   """

    __abstract__ = True

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # sets timestamp to creation
        server_onupdate=func.now()  # update timestamp on update
    )

class Creator(BaseTable):
    """
        Table to store creators of tours
    """

    __tablename__ = 'creator'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    creator_name: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)


class CreatorRout(BaseTable):
    """
        Table to store creators routs
    """

    __tablename__ = 'creator_rout'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey('creator.id'))
    rout_id: Mapped[int] = mapped_column(ForeignKey('rout.id'))


class BaseUser(BaseTable):

    """
        Table to store users of telegram bot
    """

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    is_creator: Mapped[bool] = mapped_column(Boolean,default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey('creator.id'), nullable=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    # users that registered with telegram won't have password
    password: Mapped[str] = mapped_column(String, nullable=True)
    lang: Mapped[str] = mapped_column(String, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'is_creator': self.is_creator,
            'is_admin': self.is_admin,
            'creator_id': self.creator_id,
            'username': self.username,
            'lang': self.lang
        }

class Order(BaseTable):

    """
        Table to store orders of users
    """

    __tablename__ = 'order'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    rout_id: Mapped[int] = mapped_column(ForeignKey("rout.id"))
    amount: Mapped[float] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    payment_link: Mapped[str] = mapped_column(String, nullable=True)


class WithdrawRequest(BaseTable):

    """
        Table to store withdraw requests of creators
    """

    __tablename__ = 'withdraw_request'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("creator.id"))
    amount: Mapped[float] = mapped_column(NUMERIC(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')
    method: Mapped[str] = mapped_column(String, nullable=False)

class RoutLocation(BaseTable):

    """
        Table to store rout locations
    """

    __tablename__ = 'rout_location'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rout_id: Mapped[int] = mapped_column(ForeignKey("rout.id"))
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)

class Rout(BaseTable):

    """
        Rout to store and access rout points
    """

    __tablename__ = 'rout'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rout_name: Mapped[str] = mapped_column(String, nullable=False)
    rout_description: Mapped[str] = mapped_column(String, nullable=False)
    base_price: Mapped[int] = mapped_column(nullable=False)
    is_displayed: Mapped[bool] = mapped_column(Boolean, default=False)
    image: Mapped[str] = mapped_column(String, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'rout_name': self.rout_name,
            'rout_description': self.rout_description,
            'base_price': self.base_price,
            'is_displayed': self.is_displayed,
            'image': self.image,
        }

class PromoCode(BaseTable):

    """
        Table to store promo codes
    """

    __tablename__ = 'promo_code'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    promo_type: Mapped[str] = mapped_column(String, nullable=False, default='flat')
    discount: Mapped[str] = mapped_column(nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey('creator.id'))
    promo_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    promo_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    use_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)

class PromoCodeRout(BaseTable):

    """
        Table to link promo codes and routs
    """

    __tablename__ = 'promo_code_rout'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey('promo_code.id'))
    rout_id: Mapped[int] = mapped_column(ForeignKey('rout.id'))


class UserRout(BaseTable):
    """
        Table to store purchased routs
    """

    __tablename__ = 'user_rout'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    rout_id: Mapped[int] = mapped_column(ForeignKey('rout.id'))


class RoutPoint(BaseTable):

    """
        Table to store rout points of rout
    """

    __tablename__ = 'rout_point'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rout_id: Mapped[int] = mapped_column(ForeignKey('rout.id'))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    point_name: Mapped[str] = mapped_column(String, nullable=True)
    point_text: Mapped[str] = mapped_column(Text, nullable=True)


    def to_dict(self):
        return {
            'id': self.id,
            'rout_id': self.rout_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'point_text': self.point_text,
        }


class PointsAudio(BaseTable):

    """
        Table to store points audio file names
    """

    __tablename__ = 'rout_point_audio'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rout_point_id: Mapped[int] = mapped_column(ForeignKey('rout_point.id'))
    audio_name: Mapped[str] = mapped_column(String, nullable=False)


class PointMedia(BaseTable):

    """
        Table to store points media file names
    """

    __tablename__ = 'rout_point_media'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rout_point_id: Mapped[int] = mapped_column(ForeignKey('rout_point.id'))
    media_name: Mapped[str] = mapped_column(String, nullable=False)

class CurrencyRates(Base):
    """
        Table to store currency rates, updates once a day
    """

    __tablename__ = 'currency_rates'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usd_usd: Mapped[float] = mapped_column(NUMERIC(10,5))
    usd_eur: Mapped[float] = mapped_column(NUMERIC(10,5))
    usd_rub: Mapped[float] = mapped_column(NUMERIC(10,5))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True),
        server_default=func.now()
    )