from app import create_app, db
from app.models.user import User
from app.models.category import Category
from app.models.rbac import Role
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, ROLE_REPORTER

app = create_app()

def seed_data():
    with app.app_context():
        # Check if users already exist
        if User.query.first() is None:
            print("Creating users...")

            # BUG-007: Look up role_id from the roles table — do NOT pass the old role= string
            admin_role = Role.query.filter_by(name=ROLE_ADMIN).first()
            agent_role = Role.query.filter_by(name=ROLE_AGENT).first()
            reporter_role = Role.query.filter_by(name=ROLE_REPORTER).first()

            if not admin_role or not agent_role or not reporter_role:
                print(
                    "ERROR: System roles not found in the database.\n"
                    "Please run migrate_rbac.py first:\n"
                    "  python migrate_rbac.py"
                )
                return

            admin = User(username='admin', email='admin@example.com', role_id=admin_role.id)
            admin.password = 'admin123'

            agent = User(username='agent', email='agent@example.com', role_id=agent_role.id)
            agent.password = 'agent123'

            reporter = User(username='reporter', email='reporter@example.com', role_id=reporter_role.id)
            reporter.password = 'reporter123'

            db.session.add_all([admin, agent, reporter])

        # Check if categories already exist
        if Category.query.first() is None:
            print("Creating categories...")

            categories = [
                Category(name='Authentication', description='Issues with login, registration, sessions'),
                Category(name='UI/UX', description='Visual bugs, broken layouts, usability issues'),
                Category(name='Database', description='Data corruption, missing records, query errors'),
                Category(name='API', description='Endpoint failures, timeouts, unexpected payloads'),
                Category(name='Performance', description='Slow loading times, high resource usage'),
                Category(name='Security', description='Vulnerabilities, unauthorized access'),
                Category(name='Other', description='Anything else')
            ]

            db.session.add_all(categories)

        try:
            db.session.commit()
            print("Database seeded successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {e}")

if __name__ == '__main__':
    seed_data()
