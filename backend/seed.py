from datetime import datetime, timedelta, timezone

from app import create_app
from app.extensions import db
from app.models import Activity, ActivityRoutePoint, Crew, CrewMember, Session, SessionAttendance, User


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.filter_by(email="amina@example.com").first():
            seed_demo_progress()
            print("Seed data already exists.")
            return

        amina = User(
            name="Amina Njeri",
            email="amina@example.com",
            neighborhood="Ruiru",
            latitude=-1.1452,
            longitude=36.9561,
            platform_role="admin",
        )
        amina.set_password("password123")
        kamau = User(
            name="Kamau Admin",
            email="kamaua175@gmail.com",
            neighborhood="Ruiru",
            latitude=-1.1452,
            longitude=36.9561,
            platform_role="admin",
        )
        kamau.set_password("ongod100")
        brian = User(
            name="Brian Otieno",
            email="brian@example.com",
            neighborhood="Membley",
            latitude=-1.1742,
            longitude=36.9318,
        )
        brian.set_password("password123")
        db.session.add_all([amina, kamau, brian])
        db.session.flush()

        sunrise = Crew(
            name="Ruiru Sunrise Walk",
            description="Easy morning walks from public landmarks around Ruiru.",
            activity_type="walk",
            visibility="public",
            meeting_point_name="Ruiru Stadium Gate",
            meeting_latitude=-1.1452,
            meeting_longitude=36.9561,
            created_by=amina.id,
        )
        runners = Crew(
            name="Membley Road Runners",
            description="Beginner-friendly runs three mornings a week.",
            activity_type="run",
            visibility="public",
            meeting_point_name="Membley Baptist Church",
            meeting_latitude=-1.1742,
            meeting_longitude=36.9318,
            created_by=brian.id,
        )
        db.session.add_all([sunrise, runners])
        db.session.flush()

        db.session.add_all(
            [
                CrewMember(crew_id=sunrise.id, user_id=amina.id, role="organizer"),
                CrewMember(crew_id=sunrise.id, user_id=brian.id),
                CrewMember(crew_id=runners.id, user_id=brian.id, role="organizer"),
            ]
        )

        now = datetime.now(timezone.utc)
        past_session = Session(
            crew_id=sunrise.id,
            title="Monday Accountability Walk",
            activity_type="walk",
            scheduled_start=now - timedelta(days=3),
            expected_distance_m=3800,
            meeting_point_name=sunrise.meeting_point_name,
            meeting_latitude=sunrise.meeting_latitude,
            meeting_longitude=sunrise.meeting_longitude,
            difficulty="easy",
            status="completed",
            created_by=amina.id,
        )
        session = Session(
            crew_id=sunrise.id,
            title="Easy Sunrise Loop",
            activity_type="walk",
            scheduled_start=(now + timedelta(days=1)).replace(hour=2, minute=45, second=0, microsecond=0),
            expected_distance_m=4500,
            meeting_point_name=sunrise.meeting_point_name,
            meeting_latitude=sunrise.meeting_latitude,
            meeting_longitude=sunrise.meeting_longitude,
            difficulty="easy",
            created_by=amina.id,
        )
        run_session = Session(
            crew_id=runners.id,
            title="Membley 5K Starter",
            activity_type="run",
            scheduled_start=(now + timedelta(days=2)).replace(hour=2, minute=30, second=0, microsecond=0),
            expected_distance_m=5000,
            meeting_point_name=runners.meeting_point_name,
            meeting_latitude=runners.meeting_latitude,
            meeting_longitude=runners.meeting_longitude,
            difficulty="moderate",
            created_by=brian.id,
        )
        db.session.add_all([past_session, session, run_session])
        db.session.flush()
        db.session.add(SessionAttendance(session_id=session.id, user_id=amina.id))
        db.session.add(SessionAttendance(session_id=run_session.id, user_id=brian.id))

        started = now - timedelta(days=3, minutes=48)
        finished = now - timedelta(days=3, minutes=8)
        amina_activity = Activity(
            user_id=amina.id,
            session_id=past_session.id,
            activity_type="walk",
            started_at=started,
            finished_at=finished,
            duration_seconds=2400,
            distance_meters=3900,
            source="web_gps",
            start_latitude=-1.1452,
            start_longitude=36.9561,
            end_latitude=-1.1504,
            end_longitude=36.963,
        )
        brian_activity = Activity(
            user_id=brian.id,
            session_id=past_session.id,
            activity_type="walk",
            started_at=started + timedelta(minutes=2),
            finished_at=finished + timedelta(minutes=1),
            duration_seconds=2340,
            distance_meters=3800,
            source="web_gps",
            start_latitude=-1.1452,
            start_longitude=36.9561,
            end_latitude=-1.1504,
            end_longitude=36.963,
        )
        db.session.add_all([amina_activity, brian_activity])
        db.session.flush()
        for activity in [amina_activity, brian_activity]:
            for index, point in enumerate(
                [
                    (-1.1452, 36.9561),
                    (-1.1474, 36.9584),
                    (-1.1492, 36.9607),
                    (-1.1504, 36.963),
                ]
            ):
                db.session.add(
                    ActivityRoutePoint(
                        activity_id=activity.id,
                        latitude=point[0],
                        longitude=point[1],
                        accuracy=9,
                        recorded_at=activity.started_at + timedelta(minutes=index * 10),
                        sequence_number=index,
                    )
                )
        db.session.add_all(
            [
                SessionAttendance(
                    session_id=past_session.id,
                    user_id=amina.id,
                    status="completed",
                    joined_at=started - timedelta(days=1),
                    checked_in_at=started,
                    checked_out_at=finished,
                ),
                SessionAttendance(
                    session_id=past_session.id,
                    user_id=brian.id,
                    status="completed",
                    joined_at=started - timedelta(days=1),
                    checked_in_at=started + timedelta(minutes=2),
                    checked_out_at=finished + timedelta(minutes=1),
                ),
            ]
        )

        db.session.commit()
        print("Seeded demo users, crews, and sessions.")


def seed_demo_progress():
    amina = User.query.filter_by(email="amina@example.com").first()
    kamau = User.query.filter_by(email="kamaua175@gmail.com").first()
    brian = User.query.filter_by(email="brian@example.com").first()
    sunrise = Crew.query.filter_by(name="Ruiru Sunrise Walk").first()
    runners = Crew.query.filter_by(name="Membley Road Runners").first()
    if not all([amina, brian, sunrise, runners]):
        return
    amina.platform_role = "admin"
    if not kamau:
        kamau = User(
            name="Kamau Admin",
            email="kamaua175@gmail.com",
            neighborhood="Ruiru",
            latitude=-1.1452,
            longitude=36.9561,
            platform_role="admin",
        )
        kamau.set_password("ongod100")
        db.session.add(kamau)
    else:
        kamau.platform_role = "admin"

    now = datetime.now(timezone.utc)
    if not Session.query.filter_by(title="Membley 5K Starter").first():
        db.session.add(
            Session(
                crew_id=runners.id,
                title="Membley 5K Starter",
                activity_type="run",
                scheduled_start=(now + timedelta(days=2)).replace(hour=2, minute=30, second=0, microsecond=0),
                expected_distance_m=5000,
                meeting_point_name=runners.meeting_point_name,
                meeting_latitude=runners.meeting_latitude,
                meeting_longitude=runners.meeting_longitude,
                difficulty="moderate",
                created_by=brian.id,
            )
        )

    if Activity.query.join(Session, Activity.session_id == Session.id).filter(Session.title == "Monday Accountability Walk").first():
        db.session.commit()
        return

    past_session = Session(
        crew_id=sunrise.id,
        title="Monday Accountability Walk",
        activity_type="walk",
        scheduled_start=now - timedelta(days=3),
        expected_distance_m=3800,
        meeting_point_name=sunrise.meeting_point_name,
        meeting_latitude=sunrise.meeting_latitude,
        meeting_longitude=sunrise.meeting_longitude,
        difficulty="easy",
        status="completed",
        created_by=amina.id,
    )
    db.session.add(past_session)
    db.session.flush()

    started = now - timedelta(days=3, minutes=48)
    finished = now - timedelta(days=3, minutes=8)
    activities = [
        Activity(
            user_id=amina.id,
            session_id=past_session.id,
            activity_type="walk",
            started_at=started,
            finished_at=finished,
            duration_seconds=2400,
            distance_meters=3900,
            source="web_gps",
            start_latitude=-1.1452,
            start_longitude=36.9561,
            end_latitude=-1.1504,
            end_longitude=36.963,
        ),
        Activity(
            user_id=brian.id,
            session_id=past_session.id,
            activity_type="walk",
            started_at=started + timedelta(minutes=2),
            finished_at=finished + timedelta(minutes=1),
            duration_seconds=2340,
            distance_meters=3800,
            source="web_gps",
            start_latitude=-1.1452,
            start_longitude=36.9561,
            end_latitude=-1.1504,
            end_longitude=36.963,
        ),
    ]
    db.session.add_all(activities)
    db.session.flush()

    route = [(-1.1452, 36.9561), (-1.1474, 36.9584), (-1.1492, 36.9607), (-1.1504, 36.963)]
    for activity in activities:
        for index, point in enumerate(route):
            db.session.add(
                ActivityRoutePoint(
                    activity_id=activity.id,
                    latitude=point[0],
                    longitude=point[1],
                    accuracy=9,
                    recorded_at=activity.started_at + timedelta(minutes=index * 10),
                    sequence_number=index,
                )
            )

    db.session.add_all(
        [
            SessionAttendance(
                session_id=past_session.id,
                user_id=amina.id,
                status="completed",
                joined_at=started - timedelta(days=1),
                checked_in_at=started,
                checked_out_at=finished,
            ),
            SessionAttendance(
                session_id=past_session.id,
                user_id=brian.id,
                status="completed",
                joined_at=started - timedelta(days=1),
                checked_in_at=started + timedelta(minutes=2),
                checked_out_at=finished + timedelta(minutes=1),
            ),
        ]
    )
    db.session.commit()


if __name__ == "__main__":
    seed()
