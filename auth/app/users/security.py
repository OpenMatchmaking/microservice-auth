from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt", ])


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, database_hash):
    return pwd_context.verify(password, database_hash)
