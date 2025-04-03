from app import create_app, db
from app.models import User

def migrate_database():
    app = create_app()
    with app.app_context():
        # Add role column to existing users
        db.session.execute('ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT "user"')
        db.session.commit()
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_database() 