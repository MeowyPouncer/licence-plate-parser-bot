from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()

class Advertisement(Base):
    __tablename__ = 'advertisements'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    year = Column(Integer)
    price = Column(Integer)
    drive = Column(String)
    city = Column(String)
    phone_number = Column(String)
    ad_id = Column(String, unique=True)
    ad_link = Column(String)
    car_number = Column(String, ForeignKey('car_numbers.number'))
    car_number_rel = relationship("CarNumber", back_populates="advertisements")


class CarNumber(Base):
    __tablename__ = 'car_numbers'
    number = Column(String, primary_key=True)
    advertisements = relationship("Advertisement", order_by=Advertisement.id, back_populates="car_number_rel")


engine = create_engine('sqlite:///volume/ads.db')
Base.metadata.create_all(engine)

Session = scoped_session(sessionmaker(bind=engine))


def add_advertisement(ad_detail):
    session = Session()
    try:
        if 'title' not in ad_detail or 'car_number' not in ad_detail:
            logger.error("Недостаточно данных для добавления объявления.")
            raise ValueError("Недостаточно данных для добавления объявления.")

        existing_ad = session.query(Advertisement).filter_by(ad_id=ad_detail['ad_id']).first()
        if existing_ad:
            logger.warning(f"Объявление с ad_id={ad_detail['ad_id']} уже существует. Пропуск добавления.")
            return False

        year_int = int(ad_detail['additional_info'].get('Год', 0))

        car_number = session.query(CarNumber).filter_by(number=ad_detail['car_number']).first()
        if not car_number:
            car_number = CarNumber(number=ad_detail['car_number'])
            session.add(car_number)

        new_ad = Advertisement(
            title=ad_detail['title'],
            year=year_int,
            drive=ad_detail['additional_info'].get('Привод', ''),
            city=ad_detail['additional_info'].get('Город', ''),
            phone_number=ad_detail.get('phone_number', ''),
            price=ad_detail.get('price', 0),
            ad_id=ad_detail.get('ad_id', ''),
            ad_link=ad_detail.get('ad_link', ''),
            car_number_rel=car_number
        )
        session.add(new_ad)
        session.commit()
        logger.info(f"Объявление успешно добавлено: {ad_detail['title']}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при добавлении объявления в базу данных: {e}")
        session.rollback()
        return False
    finally:
        session.close()


async def search_ads_by_number(car_number):
    session = Session()
    try:
        car_number_obj = session.query(CarNumber).filter_by(number=car_number).first()
        if not car_number_obj:
            logger.info(f"Номер автомобиля {car_number} не найден в базе.")
            return []

        ads = session.query(Advertisement).filter_by(car_number=car_number_obj.number).all()
        if not ads:
            logger.info(f"Объявления для автомобиля с номером {car_number} не найдены.")
            return []

        ads_info = [{
            'title': ad.title,
            'year': ad.year,
            'drive': ad.drive,
            'price': ad.price,
            'car_number': ad.car_number,
            'city': ad.city,
            'phone_number': ad.phone_number,
            'ad_link': ad.ad_link
        } for ad in ads]

        logger.info(f"Найдены объявления для номера {car_number}: {ads_info}")
        return ads_info
    except Exception as e:
        logger.error(f"Ошибка при поиске объявлений по номеру автомобиля: {e}")
        return []
    finally:
        session.close()

