from db import session, User

def check_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return False
    return True

def get_existed_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    return user