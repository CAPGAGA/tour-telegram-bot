import datetime

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    Boolean,
    func,
)
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

class Admin(BaseTable):
    """
        Table to store admins of telegram bot
    """

    __tablename__ = 'admin'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class AdminRout(BaseTable):
    """
        Table to store admins routs
    """

    __tablename__ = 'admin_rout'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey('admin.id'))
    rout_id: Mapped[int] = mapped_column(ForeignKey('rout.id'))


class BaseUser(BaseTable):

    """
        Table to store users of telegram bot
    """

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean,default=False)
    username: Mapped[str] = mapped_column(String, nullable=True)


class Order(BaseTable):

    """
        Table to store orders of users
    """

    __tablename__ = 'order'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    rout_id: Mapped[int] = mapped_column(ForeignKey("rout.id"))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    payment_link: Mapped[str] = mapped_column(String, nullable=True)


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

