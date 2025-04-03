import os
import shutil
from app import create_app, db
from app.models import User


def reset_database():
    # Create a temporary app to get the instance path
    temp_app = create_app()
    instance_path = temp_app.instance_path
    
    # Remove the entire instance folder to ensure clean state
    if os.path.exists(instance_path):
        shutil.rmtree(instance_path)
        print("Instance folder removed")
    
    # Create new instance folder
    os.makedirs(instance_path)
    print("New instance folder created")
    
    # Create a new app with explicit database path
    app = create_app()
    db_path = os.path.join(instance_path, 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Create new database and tables
    with app.app_context():
        db.create_all()
        print("New database created with updated schema")
        
        # Create admin user
        admin = User(
            username='admin',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created")
        
        print("Database reset complete!")


if __name__ == '__main__':
    reset_database() 